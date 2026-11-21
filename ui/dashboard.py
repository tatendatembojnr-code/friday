"""Soft UI Web Dashboard server and REST API for FRIDAY."""

from __future__ import annotations

import json
import logging
import mimetypes
import sqlite3
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

from config.settings import BASE_DIR, FridaySettings
from core.backtester import run_backtest
from core.database import DatabaseManager
from core.market_schedule import get_market_schedule_info
from core.mt5_connector import MT5Connector
from ui.template import LOGIN_HTML, SOFT_UI_HTML


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
            "symbols": ",".join(settings.trading.symbols),
            "risk_per_trade_pct": settings.risk.risk_per_trade_pct,
            "max_single_trade_risk_pct": settings.risk.max_single_trade_risk_pct,
            "max_daily_loss_pct": settings.risk.max_daily_loss_pct,
            "max_drawdown_pct": settings.risk.max_drawdown_pct,
            "max_open_trades": settings.risk.max_open_trades,
            "max_trades_per_symbol": settings.risk.max_trades_per_symbol,
            "max_usd_exposure": settings.risk.max_usd_exposure,
            "max_daily_trades": settings.risk.max_daily_trades,
            "min_smc_score": settings.smc.min_smc_score,
            "ai_min_confidence": settings.ai_brain.min_confidence,
            "default_rr_target": settings.smc.default_rr_target,
            "breakeven_at_rr": settings.risk.breakeven_at_rr,
            "trailing_start_rr": settings.risk.trailing_start_rr,
            "max_trade_duration_minutes": settings.risk.max_trade_duration_minutes,
            "poll_interval_seconds": settings.mode.poll_interval_seconds,
            "dry_run": settings.mode.dry_run,
        }

    return {
        "mode": mode_label,
        "db_backend": "postgresql" if (settings and __import__("os").getenv("DATABASE_URL", "").startswith("postgres")) else "sqlite",
        "paused": bool(bot_state.get("paused")) if bot_state else False,
        "session": session,
        "schedule": get_market_schedule_info(),
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
        if "max_daily_loss_pct" in payload and payload["max_daily_loss_pct"] is not None:
            val = float(payload["max_daily_loss_pct"])
            raw["risk"]["max_daily_loss_pct"] = val
            settings.risk.max_daily_loss_pct = val
        if "max_drawdown_pct" in payload and payload["max_drawdown_pct"] is not None:
            val = float(payload["max_drawdown_pct"])
            raw["risk"]["max_drawdown_pct"] = val
            settings.risk.max_drawdown_pct = val
        if "breakeven_at_rr" in payload and payload["breakeven_at_rr"] is not None:
            val = float(payload["breakeven_at_rr"])
            raw["risk"]["breakeven_at_rr"] = val
            settings.risk.breakeven_at_rr = val
        if "poll_interval_seconds" in payload and payload["poll_interval_seconds"] is not None:
            val = int(payload["poll_interval_seconds"])
            raw["mode"]["poll_interval_seconds"] = val
            settings.mode.poll_interval_seconds = val
        if "max_single_trade_risk_pct" in payload and payload["max_single_trade_risk_pct"] is not None:
            val = float(payload["max_single_trade_risk_pct"])
            raw["risk"]["max_single_trade_risk_pct"] = val
            settings.risk.max_single_trade_risk_pct = val
        if "max_trades_per_symbol" in payload and payload["max_trades_per_symbol"] is not None:
            val = int(payload["max_trades_per_symbol"])
            raw["risk"]["max_trades_per_symbol"] = val
            settings.risk.max_trades_per_symbol = val
        if "max_usd_exposure" in payload and payload["max_usd_exposure"] is not None:
            val = int(payload["max_usd_exposure"])
            raw["risk"]["max_usd_exposure"] = val
            settings.risk.max_usd_exposure = val
        if "max_daily_trades" in payload and payload["max_daily_trades"] is not None:
            val = int(payload["max_daily_trades"])
            raw["risk"]["max_daily_trades"] = val
            settings.risk.max_daily_trades = val
        if "trailing_start_rr" in payload and payload["trailing_start_rr"] is not None:
            val = float(payload["trailing_start_rr"])
            raw["risk"]["trailing_start_rr"] = val
            settings.risk.trailing_start_rr = val
        if "max_trade_duration_minutes" in payload and payload["max_trade_duration_minutes"] is not None:
            val = int(payload["max_trade_duration_minutes"])
            raw["risk"]["max_trade_duration_minutes"] = val
            settings.risk.max_trade_duration_minutes = val
        if "ai_min_confidence" in payload and payload["ai_min_confidence"] is not None:
            val = int(payload["ai_min_confidence"])
            raw["ai_brain"]["min_confidence"] = val
            settings.ai_brain.min_confidence = val
        if payload.get("symbols"):
            syms = [s.strip().upper() for s in str(payload["symbols"]).split(",") if s.strip()]
            if syms:
                raw["trading"]["symbols"] = syms
                settings.trading.symbols = syms
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
    if payload.get("openai_api_key"):
        updates["OPENAI_API_KEY"] = str(payload["openai_api_key"])
    if payload.get("gemini_api_key"):
        updates["GEMINI_API_KEY"] = str(payload["gemini_api_key"])
    if payload.get("groq_api_key"):
        updates["GROQ_API_KEY"] = str(payload["groq_api_key"])
    if payload.get("ollama_api_key"):
        updates["OLLAMA_API_KEY"] = str(payload["ollama_api_key"])
    if payload.get("ollama_model"):
        updates["OLLAMA_MODEL"] = str(payload["ollama_model"])
    if payload.get("telegram_bot_token"):
        updates["TELEGRAM_BOT_TOKEN"] = str(payload["telegram_bot_token"])
    if payload.get("telegram_chat_id"):
        updates["TELEGRAM_CHAT_ID"] = str(payload["telegram_chat_id"])

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
    db = DatabaseManager(db_path=db_path)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def _get_session_user(self) -> str | None:
            cookie_hdr = self.headers.get("Cookie", "")
            if not cookie_hdr:
                return None
            c = SimpleCookie()
            c.load(cookie_hdr)
            morsel = c.get("friday_session")
            if not morsel:
                return None
            return db.verify_session(morsel.value)

        def _send_json(self, data: Any, status: int = 200, set_cookie: str | None = None) -> None:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            if set_cookie:
                self.send_header("Set-Cookie", set_cookie)
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

            if parsed.path == "/login":
                body = LOGIN_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            user = self._get_session_user()
            if not user:
                if parsed.path.startswith("/api/"):
                    self._send_json({"error": "Unauthorized"}, status=401)
                else:
                    self.send_response(302)
                    self.send_header("Location", "/login")
                    self.end_headers()
                return

            if parsed.path == "/api/status":
                lbl = "DRY-RUN" if (settings and settings.mode.dry_run) else mode_label
                payload = collect_status(connector, db_path, log_path, lbl, session_fn(), settings, state)
                self._send_json(payload)
                return

            if parsed.path == "/api/market_chart":
                qs = parse_qs(parsed.query)
                sym = qs.get("symbol", ["XAUUSD"])[0]
                df = connector.get_ohlc(sym, "M15", 80)
                if df is None:
                    self._send_json({"labels": [], "closes": [], "candles": []})
                    return
                labels = [str(t)[11:16] for t in df.index]
                closes = [round(float(c), 5) for c in df["close"]]
                candles = [
                    {
                        "time": int(idx.timestamp()),
                        "open": round(float(row["open"]), 5),
                        "high": round(float(row["high"]), 5),
                        "low": round(float(row["low"]), 5),
                        "close": round(float(row["close"]), 5),
                    }
                    for idx, row in df.iterrows()
                ]
                self._send_json({"labels": labels, "closes": closes, "candles": candles})
                return

            if parsed.path == "/api/news":
                import urllib.request
                import xml.etree.ElementTree as ET
                news_items = []
                try:
                    url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F,EURUSD=X,GBPUSD=X,JPY=X&region=US&lang=en-US"
                    req = urllib.request.Request(url, headers={"User-Agent": "FRIDAY-Bot/1.0"})
                    with urllib.request.urlopen(req, timeout=3.0) as resp:
                        root = ET.fromstring(resp.read())
                    for item in root.findall(".//item")[:8]:
                        news_items.append(
                            {
                                "title": item.findtext("title", ""),
                                "link": item.findtext("link", "#"),
                                "pubDate": item.findtext("pubDate", "")[:22],
                            }
                        )
                except Exception:
                    news_items = [
                        {"title": "Live RSS feed unavailable offline — check internet connection.", "link": "#", "pubDate": ""}
                    ]
                self._send_json({"items": news_items})
                return

            if parsed.path == "/api/backtest":
                qs = parse_qs(parsed.query)
                sym = qs.get("symbol", ["XAUUSD"])[0]
                bars = int(qs.get("bars", ["300"])[0])
                res = run_backtest(connector, settings or FridaySettings.load(), symbol=sym, bars=bars)
                self._send_json(res)
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

            if self.path == "/api/login":
                uname = str(payload.get("username", "")).strip()
                pwd = str(payload.get("password", ""))
                if db.verify_user(uname, pwd):
                    tok = db.create_session(uname)
                    db.log_audit(uname, "LOGIN", "Signed into Web Command Center")
                    self._send_json(
                        {"ok": True, "username": uname},
                        set_cookie=f"friday_session={tok}; Path=/; HttpOnly; SameSite=Lax",
                    )
                else:
                    self._send_json({"ok": False, "error": "Invalid username or password"}, status=401)
                return

            if self.path == "/api/logout":
                cookie_hdr = self.headers.get("Cookie", "")
                c = SimpleCookie()
                if cookie_hdr:
                    c.load(cookie_hdr)
                    if "friday_session" in c:
                        db.delete_session(c["friday_session"].value)
                self._send_json({"ok": True}, set_cookie="friday_session=; Path=/; Max-Age=0")
                return

            user = self._get_session_user()
            if not user:
                self._send_json({"error": "Unauthorized"}, status=401)
                return

            if self.path == "/api/bot/toggle":
                state["paused"] = not state.get("paused", False)
                db.log_audit(user, "BOT_TOGGLE", f"paused={state['paused']}")
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
