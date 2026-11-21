"""Lightweight zero-dependency Web Dashboard UI for FRIDAY."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

from core.mt5_connector import MT5Connector


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FRIDAY — Institutional Trading Command Center</title>
  <style>
    :root {
      --bg: #0b0f17; --card: #131a26; --border: #1f2a3d;
      --text: #e6edf3; --muted: #8b949e; --green: #2ea043; --red: #f85149; --blue: #58a6ff;
    }
    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { margin: 0; background: var(--bg); color: var(--text); padding: 24px; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .badge { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: #1f2a3d; color: var(--blue); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
    .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
    .value { font-size: 24px; font-weight: 700; margin-top: 6px; }
    .pos { color: var(--green); } .neg { color: var(--red); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 600; }
    .section { margin-bottom: 24px; }
    pre { background: #090d14; border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-size: 12px; max-height: 240px; overflow-y: auto; color: #c9d1d9; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1 style="margin:0;font-size:22px;">FRIDAY Command Center</h1>
      <span style="color:var(--muted);font-size:13px;">SMC + Multi-Persona AI Council + Risk Guardrails</span>
    </div>
    <span id="modeBadge" class="badge">Connecting...</span>
  </div>

  <div class="grid">
    <div class="card"><div class="label">Balance</div><div id="balance" class="value">--</div></div>
    <div class="card"><div class="label">Equity</div><div id="equity" class="value">--</div></div>
    <div class="card"><div class="label">Floating P&amp;L</div><div id="pnl" class="value">--</div></div>
    <div class="card"><div class="label">Open Trades</div><div id="openCount" class="value">--</div></div>
    <div class="card"><div class="label">Session</div><div id="session" class="value" style="font-size:18px;">--</div></div>
  </div>

  <div class="card section">
    <h3 style="margin-top:0;">Open Positions</h3>
    <table>
      <thead><tr><th>Ticket</th><th>Symbol</th><th>Side</th><th>Lots</th><th>Open</th><th>Current</th><th>SL</th><th>TP</th><th>P&amp;L</th></tr></thead>
      <tbody id="posBody"><tr><td colspan="9" style="color:var(--muted);">No open positions</td></tr></tbody>
    </table>
  </div>

  <div class="card section">
    <h3 style="margin-top:0;">Recent AI &amp; SMC Decisions</h3>
    <table>
      <thead><tr><th>Time</th><th>Symbol</th><th>Dir</th><th>SMC</th><th>AI</th><th>Regime</th><th>Reasoning</th></tr></thead>
      <tbody id="aiBody"><tr><td colspan="7" style="color:var(--muted);">Waiting for decisions...</td></tr></tbody>
    </table>
  </div>

  <div class="card">
    <h3 style="margin-top:0;">Live Bot Logs</h3>
    <pre id="logs">Loading logs...</pre>
  </div>

  <script>
    async function refresh() {
      try {
        const res = await fetch('/api/status');
        const d = await res.json();
        document.getElementById('modeBadge').textContent = `${d.mode} | ${d.session}`;
        document.getElementById('balance').textContent = `$${d.balance.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        document.getElementById('equity').textContent = `$${d.equity.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        const pnlEl = document.getElementById('pnl');
        pnlEl.textContent = `${d.floating_pnl >= 0 ? '+' : ''}$${d.floating_pnl.toFixed(2)}`;
        pnlEl.className = 'value ' + (d.floating_pnl >= 0 ? 'pos' : 'neg');
        document.getElementById('openCount').textContent = d.positions.length;
        document.getElementById('session').textContent = d.session;

        const posBody = document.getElementById('posBody');
        posBody.innerHTML = d.positions.length ? d.positions.map(p => `
          <tr>
            <td>${p.ticket}</td><td><b>${p.symbol}</b></td><td>${p.type}</td><td>${p.volume}</td>
            <td>${p.price_open}</td><td>${p.price_current}</td><td>${p.sl}</td><td>${p.tp}</td>
            <td class="${p.profit >= 0 ? 'pos' : 'neg'}">${p.profit >= 0 ? '+' : ''}$${p.profit.toFixed(2)}</td>
          </tr>`).join('') : '<tr><td colspan="9" style="color:var(--muted);">No open positions</td></tr>';

        const aiBody = document.getElementById('aiBody');
        aiBody.innerHTML = d.recent_decisions.length ? d.recent_decisions.map(r => `
          <tr>
            <td>${(r.timestamp || '').slice(11, 19)}</td><td><b>${r.symbol}</b></td><td>${r.direction}</td>
            <td>${r.smc_score}</td><td>${r.ai_decision} (${r.ai_confidence}%)</td><td>${r.ai_regime}</td>
            <td style="color:var(--muted);">${r.ai_reasoning}</td>
          </tr>`).join('') : '<tr><td colspan="7" style="color:var(--muted);">No decisions recorded yet</td></tr>';

        document.getElementById('logs').textContent = d.logs.join('\\n');
      } catch (e) {}
    }
    refresh();
    setInterval(refresh, 3000);
  </script>
</body>
</html>
"""


def collect_status(connector: MT5Connector, db_path: Path, log_path: Path, mode_label: str, session: str) -> Dict[str, Any]:
    acc = connector.get_account_snapshot()
    positions = connector.get_open_positions()
    recent_decisions: List[Dict[str, Any]] = []
    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT timestamp, symbol, direction, smc_score, ai_decision, ai_confidence, ai_regime, ai_reasoning "
                    "FROM trade_journal ORDER BY id DESC LIMIT 10"
                ).fetchall()
                recent_decisions = [dict(r) for r in rows]
        except Exception:
            pass

    logs: List[str] = []
    if log_path.exists():
        try:
            logs = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-25:]
        except Exception:
            pass

    return {
        "mode": mode_label,
        "session": session,
        "balance": round(acc.balance, 2),
        "equity": round(acc.equity, 2),
        "floating_pnl": round(acc.profit, 2),
        "positions": positions,
        "recent_decisions": recent_decisions,
        "logs": logs,
    }


def start_dashboard(
    connector: MT5Connector,
    db_path: Path,
    log_path: Path,
    mode_label: str,
    session_fn,
    host: str = "127.0.0.1",
    port: int = 8501,
) -> ThreadingHTTPServer:
    logger = logging.getLogger("FRIDAY")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/api/status":
                payload = collect_status(connector, db_path, log_path, mode_label, session_fn())
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"FRIDAY Web UI running at http://{host}:{port}")
    return server
