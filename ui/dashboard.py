"""Soft UI Web Dashboard server and REST API for FRIDAY."""

from __future__ import annotations

import json
import logging
import mimetypes
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

from config.settings import BASE_DIR, FridaySettings
from core.mt5_connector import MT5Connector
from ui.template import SOFT_UI_HTML


ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def collect_status(
    connector: MT5Connector,
    db_path: Path,
    log_path: Path,
    mode_label: str,
    session: str,
    settings: FridaySettings | None = None,
    bot_state: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    acc = connector.get_account_snapshot()
    positions = connector.get_open_positions()
    recent_decisions: List[Dict[str, Any]] = []
    closed_deals: List[Dict[str, Any]] = []
    total_profits = 0.0
    total_losses = 0.0
    win_count = 0
    loss_count = 0

    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT timestamp, symbol, direction, smc_score, ai_decision, ai_confidence, ai_regime, ai_reasoning "
                    "FROM trade_journal ORDER BY id DESC LIMIT 15"
                ).fetchall()
                recent_decisions = [dict(r) for r in rows]

                has_deals = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='closed_deals'"
                ).fetchone()
                if has_deals:
                    deal_rows = conn.execute(
                        "SELECT ticket, timestamp, symbol, direction, pnl, outcome "
                        "FROM closed_deals ORDER BY ticket DESC LIMIT 30"
                    ).fetchall()
                    closed_deals = [dict(r) for r in deal_rows]
                    agg = conn.execute(
                        "SELECT "
                        "COALESCE(SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END), 0.0), "
                        "COALESCE(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END), 0.0), "
                        "SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END), "
                        "SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) "
                        "FROM closed_deals"
                    ).fetchone()
                    total_profits = float(agg[0] or 0.0)
                    total_losses = float(agg[1] or 0.0)
                    win_count = int(agg[2] or 0)
                    loss_count = int(agg[3] or 0)
        except Exception:
            pass

    total_closed = win_count + loss_count
    win_rate = round((win_count / total_closed) * 100.0, 1) if total_closed > 0 else 0.0

    # Build equity curve from closed deals + live equity
    equity_curve: List[Dict[str, Any]] = []
    running_pnl = 0.0
    for d in reversed(closed_deals):
        running_pnl += float(d["pnl"])
        equity_curve.append({"label": (d["timestamp"] or "")[11:16] or str(d["ticket"]), "value": round(running_pnl, 2)})
    equity_curve.append({"label": "Now", "value": round(acc.equity, 2)})

    market_watch: List[Dict[str, Any]] = []
    symbols = settings.trading.symbols if settings else ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    for sym in symbols:
        specs = connector.get_symbol_specs(sym)
        if specs:
            market_watch.append(
                {
                    "symbol": sym,
                    "bid": round(specs.bid, specs.digits),
                    "ask": round(specs.ask, specs.digits),
                    "spread": round(specs.spread_points, 1),
                    "last_close": round(specs.bid, specs.digits),
                }
            )

    logs: List[str] = []
    if log_path.exists():
        try:
            logs = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]
        except Exception:
            pass

    cfg_payload = None
    if settings:
        cfg_payload = {
            "mt5_login": settings.credentials.mt5_login,
            "mt5_server": settings.credentials.mt5_server,
            "risk_per_trade_pct": settings.risk.risk_per_trade_pct,
            "max_open_trades": settings.risk.max_open_trades,
            "min_smc_score": settings.smc.min_smc_score,
            "default_rr_target": settings.smc.default_rr_target,
            "dry_run": settings.mode.dry_run,
        }

    return {
        "mode": mode_label,
        "paused": bool(bot_state.get("paused")) if bot_state else False,
        "session": session,
        "balance": round(acc.balance, 2),
        "equity": round(acc.equity, 2),
        "margin_free": round(acc.margin_free, 2),
        "floating_pnl": round(acc.profit, 2),
        "total_profits": round(total_profits, 2),
        "total_losses": round(total_losses, 2),
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate_pct": win_rate,
        "max_open_trades": settings.risk.max_open_trades if settings else 3,
        "positions": positions,
        "recent_decisions": recent_decisions,
        "closed_deals": closed_deals,
        "equity_curve": equity_curve,
        "market_watch": market_watch,
        "logs": logs,
        "config": cfg_payload,
    }


def _update_env_and_config(payload: Dict[str, Any], settings: FridaySettings) -> None:
    cfg_path = BASE_DIR / "config" / "friday_config.json"
    if cfg_path.exists():
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        if "risk_per_trade_pct" in payload and payload["risk_per_trade_pct"] is not None:
            val = float(payload["risk_per_trade_pct"])
            raw["risk"]["risk_per_trade_pct"] = val
            settings.risk.risk_per_trade_pct = val
        if "max_open_trades" in payload and payload["max_open_trades"] is not None:
            val = int(payload["max_open_trades"])
            raw["risk"]["max_open_trades"] = val
            settings.risk.max_open_trades = val
        if "min_smc_score" in payload and payload["min_smc_score"] is not None:
            val = int(payload["min_smc_score"])
            raw["smc"]["min_smc_score"] = val
            settings.smc.min_smc_score = val
        if "default_rr_target" in payload and payload["default_rr_target"] is not None:
            val = float(payload["default_rr_target"])
            raw["smc"]["default_rr_target"] = val
            settings.smc.default_rr_target = val
        if "dry_run" in payload:
            raw["mode"]["dry_run"] = bool(payload["dry_run"])
            settings.mode.dry_run = bool(payload["dry_run"])
        cfg_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    env_path = BASE_DIR / ".env"
    env_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    updates = {}
    if payload.get("mt5_login"):
        updates["MT5_LOGIN"] = str(payload["mt5_login"])
    if payload.get("mt5_password"):
        updates["MT5_PASSWORD"] = str(payload["mt5_password"])
    if payload.get("mt5_server"):
        updates["MT5_SERVER"] = str(payload["mt5_server"])
    if payload.get("gemini_api_key"):
        updates["GEMINI_API_KEY"] = str(payload["gemini_api_key"])
    if payload.get("groq_api_key"):
        updates["GROQ_API_KEY"] = str(payload["groq_api_key"])

    if updates:
        new_lines = []
        seen = set()
        for line in env_lines:
            if "=" in line and not line.strip().startswith("#"):
                k = line.split("=", 1)[0].strip()
                if k in updates:
                    new_lines.append(f"{k}={updates[k]}")
                    seen.add(k)
                    continue
            new_lines.append(line)
        for k, v in updates.items():
            if k not in seen:
                new_lines.append(f"{k}={v}")
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def start_dashboard(
    connector: MT5Connector,
    db_path: Path,
    log_path: Path,
    mode_label: str,
    session_fn,
    settings: FridaySettings | None = None,
    order_mgr=None,
    bot_state: Dict[str, Any] | None = None,
    host: str = "127.0.0.1",
    port: int = 8501,
) -> ThreadingHTTPServer:
    logger = logging.getLogger("FRIDAY")
    state = bot_state if bot_state is not None else {"paused": False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json(self, data: Any, status: int = 200) -> None:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/assets/"):
                rel = parsed.path[len("/assets/"):]
                file_path = (ASSETS_DIR / rel).resolve()
                if ASSETS_DIR.resolve() in file_path.parents and file_path.is_file():
                    ctype, _ = mimetypes.guess_type(str(file_path))
                    data = file_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", ctype or "application/octet-stream")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                self.send_error(404)
                return

            if parsed.path == "/api/status":
                lbl = "DRY-RUN" if (settings and settings.mode.dry_run) else mode_label
                payload = collect_status(connector, db_path, log_path, lbl, session_fn(), settings, state)
                self._send_json(payload)
                return

            if parsed.path == "/api/market_chart":
                qs = parse_qs(parsed.query)
                sym = qs.get("symbol", ["XAUUSD"])[0]
                df = connector.get_ohlc(sym, "M15", 60)
                if df is None:
                    self._send_json({"labels": [], "closes": []})
                    return
                labels = [str(t)[11:16] for t in df.index]
                closes = [round(float(c), 5) for c in df["close"]]
                self._send_json({"labels": labels, "closes": closes})
                return

            body = SOFT_UI_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            payload = json.loads(raw_body) if raw_body.strip() else {}

            if self.path == "/api/bot/toggle":
                state["paused"] = not state.get("paused", False)
                self._send_json({"paused": state["paused"]})
                return

            if self.path == "/api/close_position" and order_mgr:
                ticket = int(payload.get("ticket", 0))
                for p in connector.get_open_positions():
                    if p["ticket"] == ticket:
                        ok = order_mgr.close_position(p, reason="Manual close from UI")
                        self._send_json({"closed": ok})
                        return
                self._send_json({"closed": False}, status=404)
                return

            if self.path == "/api/close_all" and order_mgr:
                count = 0
                for p in connector.get_open_positions():
                    if order_mgr.close_position(p, reason="Close All from UI"):
                        count += 1
                self._send_json({"closed_count": count})
                return

            if self.path == "/api/config" and settings:
                _update_env_and_config(payload, settings)
                if hasattr(order_mgr, "dry_run"):
                    order_mgr.dry_run = settings.mode.dry_run or connector.simulate
                self._send_json({"ok": True, "message": "Saved! Settings applied."})
                return

            self._send_json({"error": "Not found"}, status=404)

    server = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info(f"FRIDAY Soft UI Dashboard running at http://{host}:{port}")
    return server
