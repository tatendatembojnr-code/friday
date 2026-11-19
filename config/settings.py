"""Configuration loader for FRIDAY trading bot."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class ModeConfig:
    dry_run: bool = True
    poll_interval_seconds: int = 60
    magic_number: int = 777001


@dataclass
class TradingConfig:
    symbols: List[str] = field(default_factory=lambda: ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"])
    htf_timeframes: List[str] = field(default_factory=lambda: ["D1", "H4"])
    ltf_timeframe: str = "M15"
    context_timeframe: str = "H1"
    bars_to_fetch: int = 250


@dataclass
class SMCConfig:
    swing_lookback: int = 5
    min_smc_score: int = 65
    fvg_min_atr_ratio: float = 0.15
    sl_atr_buffer: float = 0.4
    default_rr_target: float = 2.5


@dataclass
class AIBrainConfig:
    enabled: bool = True
    model: str = "gpt-4o-mini"
    min_confidence: int = 70
    temperature: float = 0.15
    max_memory_examples: int = 5
    allow_tp_sl_refinement: bool = True


@dataclass
class EA31337BridgeConfig:
    enabled: bool = True
    signal_file: str = "data/ea31337_signals.json"
    max_age_seconds: int = 900
    alignment_bonus_score: int = 10


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_drawdown_pct: float = 8.0
    max_open_trades: int = 3
    max_daily_trades: int = 5
    min_risk_reward: float = 1.8
    max_spread_atr_ratio: float = 0.25
    breakeven_at_rr: float = 1.0
    trailing_start_rr: float = 1.5
    trailing_atr_mult: float = 1.0
    allowed_sessions: List[str] = field(
        default_factory=lambda: ["London", "New York", "London-NY Overlap"]
    )


@dataclass
class Credentials:
    mt5_login: int = 0
    mt5_password: str = ""
    mt5_server: str = ""
    mt5_path: str = ""
    openai_api_key: str = ""


@dataclass
class FridaySettings:
    mode: ModeConfig = field(default_factory=ModeConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    smc: SMCConfig = field(default_factory=SMCConfig)
    ai_brain: AIBrainConfig = field(default_factory=AIBrainConfig)
    ea31337_bridge: EA31337BridgeConfig = field(default_factory=EA31337BridgeConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    credentials: Credentials = field(default_factory=Credentials)

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "FridaySettings":
        load_dotenv(BASE_DIR / ".env")
        path = Path(config_path) if config_path else BASE_DIR / "config" / "friday_config.json"

        raw = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

        login_raw = os.getenv("MT5_LOGIN", "0").strip()
        creds = Credentials(
            mt5_login=int(login_raw) if login_raw.isdigit() else 0,
            mt5_password=os.getenv("MT5_PASSWORD", ""),
            mt5_server=os.getenv("MT5_SERVER", ""),
            mt5_path=os.getenv("MT5_PATH", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )

        return cls(
            mode=ModeConfig(**raw.get("mode", {})),
            trading=TradingConfig(**raw.get("trading", {})),
            smc=SMCConfig(**raw.get("smc", {})),
            ai_brain=AIBrainConfig(**raw.get("ai_brain", {})),
            ea31337_bridge=EA31337BridgeConfig(**raw.get("ea31337_bridge", {})),
            risk=RiskConfig(**raw.get("risk", {})),
            credentials=creds,
        )
