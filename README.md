# FRIDAY — Institutional SMC + Multi-Persona AI Trading Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform: MetaTrader 5](https://img.shields.io/badge/Platform-MetaTrader%205-green.svg)](https://www.metatrader5.com/)

**FRIDAY** is a standalone, modular MetaTrader 5 (MT5) algorithmic trading system that fuses deterministic **Smart Money Concepts (SMC)** with a **Multi-Persona OpenAI Trading Council**, **SQLite Adaptive Memory**, and **Hard Risk Guardrails**.

---

## Architecture

```text
MT5 Market Data (D1 / H4 / H1 / M15)
        │
        ▼
[1] Multi-Timeframe Context Builder  ──► Trend, EMA20/50, RSI, ATR, Session, Spread
        │
        ▼
[2] Deterministic SMC Engine         ──► Liquidity Sweeps, BOS, Order Blocks, FVGs, Score
        │
        ▼
[3] FRIDAY AI Council (OpenAI JSON)  ──► Structure + Macro + R:R Analysts + SQLite Memory
        │
        ▼
[4] Hard Risk Manager (Final Veto)   ──► Accurate Lot Sizing, Daily Loss, Max DD, Sessions
        │
        ▼
[5] Order & Trade Manager            ──► Live / Dry-Run Execution, Breakeven & Trailing SL
```

---

## Key Features

- **Deterministic SMC Engine (`strategy/smc_engine.py` & `strategy/killzone_vwap.py`):**
  - Fractal swing high/low detection, liquidity sweeps, BOS, Order Blocks, FVGs, Pin-Bar rejection wicks, and RSI(14) exhaustion guard
  - Institutional Killzones (`LondonKillzone`, `NYKillzone`), Session VWAP, and PDH/PDL Premium/Discount scoring
- **Multi-Persona AI Council & Self-Learner (`ai/friday_brain.py`, `ai/self_learner.py`):**
  - Supports OpenAI, Google Gemini, Groq, and Ollama Cloud/Local with automatic cooldown circuit-breaker
  - Learns per-symbol/direction edge from realized MT5 closed deals and throttles risk on losing streaks
- **Soft UI Command Center (`ui/dashboard.py`, `core/database.py`):**
  - White & Lime Green Bootstrap 5 Soft UI at `http://127.0.0.1:8501` with Sign-In auth, weekend countdown, candlestick chart, live news, one-click Backtester, Profit Factor/Expectancy analytics, and PostgreSQL/SQLite persistence
- **CLI Backtester (`backtest_cli.py`):**
  - Run `run friday --backtest` to benchmark all 6 symbols (`EURUSD`, `GBPUSD`, `USDJPY`, `XAUUSD`, `EURJPY`, `AUDUSD`)
- **Adaptive SQLite Trade Memory (`ai/memory.py`):**
  - Logs every setup, AI verdict, and trade outcome to `data/friday_memory.db`
  - Feeds recent symbol-specific history back into FRIDAY's prompt
- **Hard Risk Guardrails (`risk/risk_manager.py`):**
  - Exact MT5 position sizing (`risk_amount / ((sl_distance / tick_size) * tick_value)`)
  - Daily loss limit, max drawdown circuit breaker, max open/daily trades, spread-to-ATR filter, and session filter
- **Safe Execution Modes (`main.py`):**
  - `--simulate`: Full synthetic multi-timeframe run without MT5 open
  - `--dry-run`: Live/Demo MT5 quotes + AI analysis with simulated orders
  - `--live`: Live/Demo MT5 order execution with breakeven at 1R and ATR trailing stops

---

## Project Structure

```text
FRIDAY/
├── ai/
│   ├── friday_brain.py       # OpenAI 3-persona council & structured JSON verdict
│   └── memory.py             # SQLite adaptive trade journal
├── config/
│   ├── friday_config.json    # Strategy, AI, and risk parameters
│   └── settings.py           # Config & .env loader
├── core/
│   ├── market_context.py     # MTF indicators, ATR, RSI, session detection
│   └── mt5_connector.py      # MT5 lifecycle & synthetic simulation fallback
├── execution/
│   └── order_manager.py      # Order execution, breakeven & trailing stop
├── risk/
│   └── risk_manager.py       # Hard risk guardrails & MT5 lot sizing
├── strategy/
│   └── smc_engine.py         # SMC liquidity sweep, BOS, OB & FVG detector
├── tests/
│   └── test_friday.py        # Unit tests
├── utils/
│   └── logger.py             # Colored console & rotating file logger
├── .env.example
├── .gitignore
├── LICENSE
├── main.py
├── README.md
└── requirements.txt
```

---

## Quick Start

1. **Clone & enter the project:**
   ```powershell
   git clone https://github.com/tatendatembojnr-code/friday.git
   cd friday
   ```
2. **Create a virtual environment & install dependencies:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   ```powershell
   copy .env.example .env
   ```
   Fill in `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`, `MT5_PATH`, and `OPENAI_API_KEY` in `.env`.
4. **Run tests & simulation:**
   ```powershell
   pytest -v
   python main.py --simulate --once
   ```
5. **Run in Dry-Run or Live/Demo mode:**
   ```powershell
   python main.py --dry-run
   # When ready on a demo account:
   python main.py --live
   ```

---

## Disclaimer

Trading financial markets involves substantial risk of loss. Always test thoroughly on a **demo account** before using live capital.

## License

This project is licensed under the [MIT License](LICENSE).
