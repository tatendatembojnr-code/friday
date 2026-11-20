"""Unit tests for FRIDAY core modules."""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai.memory import FridayMemory
from config.settings import Credentials, EA31337BridgeConfig, RiskConfig, SMCConfig
from core.ea31337_bridge import EA31337Bridge
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


def test_ea31337_bridge_reads_fresh_and_ignores_stale(tmp_path):
    import json
    from datetime import datetime, timedelta, timezone

    sig_file = tmp_path / "ea31337_signals.json"
    fresh_ts = datetime.now(timezone.utc).isoformat()
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    sig_file.write_text(
        json.dumps(
            {
                "EURUSD": {
                    "bias": "BULLISH",
                    "consensus_score": 85,
                    "active_strategies": ["EMA_Cross", "MACD_Trend"],
                    "timestamp": fresh_ts,
                },
                "GBPUSD": {
                    "bias": "BEARISH",
                    "consensus_score": 70,
                    "active_strategies": ["RSI_Momentum"],
                    "timestamp": stale_ts,
                },
            }
        ),
        encoding="utf-8",
    )

    bridge = EA31337Bridge(EA31337BridgeConfig(enabled=True, signal_file=str(sig_file), max_age_seconds=900))
    eur = bridge.get_signal("EURUSD")
    assert eur is not None
    assert eur.bias == "BULLISH"
    assert eur.consensus_score == 85

    gbp = bridge.get_signal("GBPUSD")
    assert gbp is None


def test_usd_correlation_cap_blocks_third_correlated_trade():
    from strategy.smc_engine import TradeSetup

    rm = RiskManager(RiskConfig(risk_per_trade_pct=1.0, max_usd_exposure=2, allowed_sessions=[]))
    specs = SymbolSpecs(
        symbol="EURUSD", digits=5, point=0.00001, trade_tick_size=0.00001, trade_tick_value=1.0,
        volume_min=0.01, volume_max=100.0, volume_step=0.01, bid=1.085, ask=1.0851, spread_points=10.0,
    )
    setup = TradeSetup(
        symbol="EURUSD", direction="SELL", entry=1.085, stop_loss=1.087, take_profit=1.081,
        risk_reward=2.0, smc_score=80, atr=0.001, htf_bias="BEARISH",
    )
    open_pos = [
        {"symbol": "GBPUSD", "type": "SELL"},  # +1 USD
        {"symbol": "XAUUSD", "type": "SELL"},  # +1 USD
    ]
    allowed, lots, reason = rm.validate_and_size(
        setup=setup, specs=specs, account=AccountSnapshot(10000, 10000, 10000, 0),
        open_positions_count=2, today_pnl=0.0, today_trades=2, session="London",
        symbol_open_count=0, open_positions=open_pos,
    )
    assert not allowed
    assert "USD correlation cap" in reason
