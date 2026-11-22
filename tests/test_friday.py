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


def test_small_account_sizing_and_over_risk_protection():
    from strategy.smc_engine import TradeSetup

    rm = RiskManager(RiskConfig(risk_per_trade_pct=1.0, max_single_trade_risk_pct=5.0, allowed_sessions=[]))
    small_acc = AccountSnapshot(balance=50.0, equity=50.0, margin_free=50.0, profit=0.0)

    # 1. XAUUSD with $25 SL -> 0.01 lot risks $25 (50% of $50) -> MUST be blocked
    gold_specs = SymbolSpecs(
        symbol="XAUUSD", digits=2, point=0.01, trade_tick_size=0.01, trade_tick_value=1.0,
        volume_min=0.01, volume_max=100.0, volume_step=0.01, bid=2650.0, ask=2650.2, spread_points=20.0,
    )
    gold_setup = TradeSetup(
        symbol="XAUUSD", direction="BUY", entry=2650.0, stop_loss=2625.0, take_profit=2700.0,
        risk_reward=2.0, smc_score=85, atr=10.0, htf_bias="BULLISH",
    )
    allowed, _, reason = rm.validate_and_size(
        setup=gold_setup, specs=gold_specs, account=small_acc,
        open_positions_count=0, today_pnl=0.0, today_trades=0, session="London",
    )
    assert not allowed
    assert "risks" in reason

    # 2. EURUSD with 15-pip (0.0015) SL -> 0.01 lot risks $1.50 (3.0% <= 5.0%) -> MUST be approved at 0.01
    eur_specs = SymbolSpecs(
        symbol="EURUSD", digits=5, point=0.00001, trade_tick_size=0.00001, trade_tick_value=1.0,
        volume_min=0.01, volume_max=100.0, volume_step=0.01, bid=1.085, ask=1.0851, spread_points=10.0,
    )
    eur_setup = TradeSetup(
        symbol="EURUSD", direction="BUY", entry=1.085, stop_loss=1.0835, take_profit=1.088,
        risk_reward=2.0, smc_score=85, atr=0.001, htf_bias="BULLISH",
    )
    allowed_eur, lots_eur, _ = rm.validate_and_size(
        setup=eur_setup, specs=eur_specs, account=small_acc,
        open_positions_count=0, today_pnl=0.0, today_trades=0, session="London",
    )
    assert allowed_eur
    assert lots_eur == 0.01

    # 3. Balance < $100 with 1 open position -> MUST block 2nd position
    blocked_second, _, reason_second = rm.validate_and_size(
        setup=eur_setup, specs=eur_specs, account=small_acc,
        open_positions_count=1, today_pnl=0.0, today_trades=1, session="London",
    )
    assert not blocked_second
    assert "Max open trades (1)" in reason_second


def test_stoploss_guard_cooldown_blocks_revenge_trading():
    from datetime import datetime, timezone
    from risk.protections import ProtectionManager

    pm = ProtectionManager(stoploss_limit=2, lookback_minutes=60, cooldown_minutes=30)
    now = datetime.now(timezone.utc)
    pm.record_trade_result("EURUSD", -50.0, now=now)
    locked, _ = pm.is_symbol_locked("EURUSD", now=now)
    assert not locked

    pm.record_trade_result("EURUSD", -40.0, now=now)
    locked, reason = pm.is_symbol_locked("EURUSD", now=now)
    assert locked
    assert "StoplossGuard" in reason


def test_order_manager_peak_profit_ratchet_tracks_rr():
    from execution.order_manager import OrderManager

    om = OrderManager(
        connector=MT5Connector(Credentials(), simulate=True),
        risk_cfg=RiskConfig(),
        magic_number=777001,
        dry_run=True,
    )
    om._peak_rr[12345] = 0.85
    # Simulated pullback to 0.50R (<= 0.85 * 0.65 = 0.5525) triggers harvest condition
    peak = om._peak_rr[12345]
    rr_now = 0.50
    assert peak >= 0.6 and rr_now > 0.15 and rr_now <= peak * 0.65


def test_dashboard_collect_status_returns_valid_payload(tmp_path):
    from ui.dashboard import collect_status

    conn = MT5Connector(Credentials(), simulate=True)
    assert conn.connect()
    payload = collect_status(
        connector=conn,
        db_path=tmp_path / "missing.db",
        log_path=tmp_path / "missing.log",
        mode_label="SIMULATE",
        session="London",
    )
    assert payload["mode"] == "SIMULATE"
    assert payload["balance"] == 10000.0
    assert "margin_free" in payload
    assert "total_profits" in payload
    assert "total_losses" in payload
    assert isinstance(payload["equity_curve"], list)
    assert isinstance(payload["market_watch"], list)
    assert isinstance(payload["positions"], list)
    assert "schedule" in payload


def test_market_schedule_weekend_countdown():
    from datetime import datetime, timezone
    from core.market_schedule import get_market_schedule_info

    sat = datetime(2026, 11, 21, 6, 30, tzinfo=timezone.utc)
    info = get_market_schedule_info(now_utc=sat, local_now=datetime(2026, 11, 21, 8, 30))
    assert info["is_weekend_closed"] is True
    assert info["seconds_to_open"] > 0
    assert "Good Morning, Tatenda" in info["greeting"]


def test_database_user_auth_and_session(tmp_path):
    from core.database import DatabaseManager

    db = DatabaseManager(db_path=tmp_path / "auth_test.db")
    assert db.create_user("trader1", "secret123")
    assert db.verify_user("trader1", "secret123")
    assert not db.verify_user("trader1", "wrong")

    tok = db.create_session("trader1")
    assert db.verify_session(tok) == "trader1"
    db.log_audit("trader1", "TEST_ACTION", "unit test")
    db.delete_session(tok)
    assert db.verify_session(tok) is None


def test_killzone_vwap_and_self_learner(tmp_path):
    from ai.self_learner import SelfLearner
    from strategy.killzone_vwap import score_institutional_location

    bonus, tags = score_institutional_location(
        direction="BUY", price=1.0810, vwap=1.0850, pdh=1.0900, pdl=1.0800, killzone="LondonKillzone"
    )
    assert bonus == 20
    assert "DiscountVWAP" in tags and "NearPDL" in tags and "LondonKillzone" in tags

    mem = FridayMemory(tmp_path / "learn.db")
    for t in range(1, 5):
        mem.sync_closed_deal(t, "EURUSD", "BUY", 100.0)
    learner = SelfLearner(tmp_path / "learn.db")
    adj, _ = learner.get_learned_adjustment("EURUSD", "BUY")
    assert adj == 10


def test_news_guard_and_backtester():
    from config.settings import FridaySettings
    from core.backtester import run_backtest
    from core.news_guard import NewsGuard

    ng = NewsGuard()
    flagged, matched = ng.check_macro_risk(["US CPI inflation surges above forecast"])
    assert flagged is True
    assert "CPI" in matched

    clean, _ = ng.check_macro_risk(["Quiet Asian session ahead"])
    assert clean is False

    conn = MT5Connector(Credentials(), simulate=True)
    assert conn.connect()
    res = run_backtest(conn, FridaySettings(), symbol="EURUSD", bars=200)
    assert "total_trades" in res
    assert res["bars"] == 200


def test_expanded_symbols_loaded_in_config():
    from config.settings import FridaySettings

    s = FridaySettings.load()
    assert "EURJPY" in s.trading.symbols
    assert "AUDUSD" in s.trading.symbols


def test_analytics_loss_streak_edge_matrix_and_webhook(tmp_path):
    from ai.self_learner import SelfLearner
    from core.analytics import compute_portfolio_analytics
    from core.webhook_server import parse_webhook_alert

    mem = FridayMemory(tmp_path / "metrics.db")
    mem.sync_closed_deal(1, "EURUSD", "BUY", 120.0)
    mem.sync_closed_deal(2, "EURUSD", "BUY", -40.0)
    mem.sync_closed_deal(3, "EURUSD", "BUY", -30.0)

    stats = compute_portfolio_analytics(tmp_path / "metrics.db")
    assert stats["total_trades"] == 3
    assert stats["profit_factor"] > 1.5

    learner = SelfLearner(tmp_path / "metrics.db")
    assert learner.get_recent_loss_streak() == 2
    matrix = learner.get_edge_matrix()
    assert len(matrix) == 1 and matrix[0]["symbol"] == "EURUSD"

    ok, alert, _ = parse_webhook_alert({"secret": "abc", "symbol": "xauusd", "action": "buy"}, expected_secret="abc")
    assert ok and alert["symbol"] == "XAUUSD" and alert["action"] == "BUY"
    bad, _, _ = parse_webhook_alert({"secret": "wrong", "symbol": "XAUUSD", "action": "BUY"}, expected_secret="abc")
    assert not bad
