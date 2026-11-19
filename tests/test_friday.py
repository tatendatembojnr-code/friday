"""Unit tests for FRIDAY core modules."""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai.memory import FridayMemory
from config.settings import Credentials, RiskConfig, SMCConfig
from core.mt5_connector import AccountSnapshot, MT5Connector, SymbolSpecs
from risk.risk_manager import RiskManager
from strategy.smc_engine import SMCEngine


def test_smc_engine_detects_simulated_setup():
    connector = MT5Connector(Credentials(), simulate=True)
    assert connector.connect()
    df = connector.get_ohlc("EURUSD", "M15", 200)
    assert df is not None and len(df) == 200

    engine = SMCEngine(SMCConfig(min_smc_score=45))
    setup = engine.analyze(df, "EURUSD", htf_bias="BULLISH")
    assert setup is not None
    assert setup.symbol == "EURUSD"
    assert setup.direction == "BUY"
    assert setup.stop_loss < setup.entry < setup.take_profit


def test_risk_manager_lot_sizing_accuracy():
    rm = RiskManager(RiskConfig(risk_per_trade_pct=1.0, allowed_sessions=[]))
    specs = SymbolSpecs(
        symbol="EURUSD",
        digits=5,
        point=0.00001,
        trade_tick_size=0.00001,
        trade_tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        bid=1.0850,
        ask=1.08515,
        spread_points=15.0,
    )
    # 1% of 10,000 = $100 risk. SL distance = 0.0020 (200 points * $1 = $200/lot) -> 0.50 lots
    lots = rm.calculate_lot_size(balance=10000.0, sl_distance=0.0020, specs=specs)
    assert lots == 0.50


def test_memory_journal_roundtrip(tmp_path):
    db_file = tmp_path / "test_mem.db"
    mem = FridayMemory(db_file)
    row_id = mem.record_decision(
        symbol="EURUSD",
        direction="BUY",
        session="London",
        htf_bias="BULLISH",
        smc_score=85,
        ai_decision="APPROVE",
        ai_confidence=82,
        ai_regime="TRENDING",
        ai_reasoning="Strong sweep + HTF alignment",
        entry=1.085,
        sl=1.083,
        tp=1.090,
        lot_size=0.5,
        executed=True,
    )
    assert row_id > 0
    recent = mem.get_recent_context("EURUSD", limit=3)
    assert len(recent) == 1
    assert recent[0]["ai_decision"] == "APPROVE"
