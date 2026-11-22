"""FRIDAY - Cutting-Edge SMC + Multi-Persona AI Trading Bot for MetaTrader 5."""

from __future__ import annotations

import utils.http_session
import utils.transport
import utils.session
import argparse
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai.friday_brain import FridayBrain
from ai.memory import FridayMemory
from ai.ml.inference_pipeline import MLInferencePipeline
from ai.self_learner import SelfLearner
from config.settings import FridaySettings
from core.database import DatabaseManager
from core.ea31337_bridge import EA31337Bridge
from core.market_context import build_htf_bias, detect_trading_session, summarize_timeframe
from core.mt5_connector import MT5Connector
from core.news_guard import NewsGuard
from core.tradingview_ta import TradingViewClient
from execution.order_manager import OrderManager
from risk.protections import ProtectionManager
from risk.risk_manager import RiskManager
from strategy.killzone_vwap import compute_vwap_and_pdh_pdl, get_killzone, score_institutional_location
from strategy.smc_engine import SMCEngine
from ui.dashboard import start_dashboard
from utils.logger import setup_logger
from utils.notifier import TelegramNotifier


def run_cycle(
    settings: FridaySettings,
    connector: MT5Connector,
    smc: SMCEngine,
    brain: FridayBrain,
    ml_pipe: MLInferencePipeline,
    memory: FridayMemory,
    learner: SelfLearner,
    bridge: EA31337Bridge,
    tv_client: TradingViewClient,
    news_guard: NewsGuard,
    protections: ProtectionManager,
    notifier: TelegramNotifier,
    risk_mgr: RiskManager,
    order_mgr: OrderManager,
    logger,
) -> None:
    session = detect_trading_session()
    order_mgr.manage_open_positions()
    account = connector.get_account_snapshot()
    today_pnl, today_trades = connector.get_today_closed_pnl()
    open_positions = connector.get_open_positions(magic=settings.mode.magic_number)

    # Learn from real closed MT5 deals (sync into SQLite memory & StoplossGuard)
    if not connector.simulate:
        try:
            import MetaTrader5 as mt5
            from datetime import datetime, timedelta, timezone
            now_utc = datetime.now(timezone.utc)
            deals = mt5.history_deals_get(now_utc - timedelta(days=1), now_utc) or []
            for d in deals:
                if d.magic == settings.mode.magic_number and d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_INOUT):
                    side = "BUY" if d.type == mt5.DEAL_TYPE_SELL else "SELL"
                    net_pnl = float(d.profit + d.swap + d.commission)
                    if memory.sync_closed_deal(int(d.ticket), d.symbol, side, net_pnl):
                        protections.record_trade_result(d.symbol, net_pnl)
        except Exception:
            pass

    logger.info(
        f"Scan | Session={session} | Balance={account.balance:.2f} | "
        f"Open={len(open_positions)} | TodayPnL={today_pnl:.2f}"
    )

    if not connector.simulate:
        macro_risk, headline = news_guard.check_macro_risk()
        if macro_risk:
            logger.warning(f"NewsGuard active (high-impact headline: {headline[:70]}); skipping new entries.")
            return

    for symbol in settings.trading.symbols:
        tf_summaries = {}
        for tf in settings.trading.htf_timeframes + [settings.trading.context_timeframe]:
            df_tf = connector.get_ohlc(symbol, tf, settings.trading.bars_to_fetch)
            if df_tf is not None and len(df_tf) >= 50:
                tf_summaries[tf] = summarize_timeframe(df_tf, tf)

        df_ltf = connector.get_ohlc(symbol, settings.trading.ltf_timeframe, settings.trading.bars_to_fetch)
        if df_ltf is None or len(df_ltf) < 60:
            logger.warning(f"{symbol}: Insufficient {settings.trading.ltf_timeframe} data.")
            continue

        htf_bias = build_htf_bias(tf_summaries)
        ctx_tf = tf_summaries.get(settings.trading.context_timeframe)
        adx_14 = ctx_tf.adx_14 if ctx_tf else 25.0
        vol_ratio = ctx_tf.vol_ratio if ctx_tf else 1.0

        setup = smc.analyze(df_ltf, symbol, htf_bias)

        # Choppy-market filter: require liquidity sweep when ADX < 18
        if setup is not None and adx_14 < 18.0 and not any("Sweep" in t for t in setup.confluence_tags):
            logger.debug(f"{symbol}: Skipping continuation in choppy regime (ADX={adx_14}).")
            setup = None

        # Adaptive Learning Gate + Institutional Killzone/VWAP + SelfLearner score adjustment
        if setup is not None:
            df_d1 = connector.get_ohlc(symbol, "D1", 10)
            levels = compute_vwap_and_pdh_pdl(df_ltf, df_d1)
            kz = get_killzone()
            loc_bonus, loc_tags = score_institutional_location(
                setup.direction, setup.entry, levels["vwap"], levels["pdh"], levels["pdl"], kz
            )
            learned_adj, learned_note = learner.get_learned_adjustment(symbol, setup.direction)
            setup.smc_score = max(0, min(100, setup.smc_score + loc_bonus + learned_adj))
            setup.confluence_tags.extend(loc_tags)
            if loc_tags or learned_adj != 0:
                logger.info(f"{symbol}: Quant Boost ({loc_tags}, {learned_note}) -> Score={setup.smc_score}")

            n_hist, wr = memory.get_symbol_win_rate(symbol, last_n=10)
            if n_hist >= 3 and wr < 0.45 and setup.smc_score < 85:
                logger.info(f"{symbol}: Adaptive Learning raised bar (win_rate={wr*100:.0f}% < 45%, score={setup.smc_score} < 85).")
                setup = None

        # Smart auto-close: if an open trade is contradicted by a strong opposing SMC setup, close it
        if setup is not None and setup.smc_score >= 70:
            for pos in open_positions:
                if pos["symbol"] == symbol and pos["type"] != setup.direction:
                    if order_mgr.close_position(pos, reason=f"Opposing SMC {setup.direction} (score={setup.smc_score})"):
                        open_positions = connector.get_open_positions(magic=settings.mode.magic_number)

        if setup is None:
            logger.debug(f"{symbol}: No qualifying SMC setup (HTF={htf_bias}).")
            continue

        symbol_open_count = sum(1 for p in open_positions if p["symbol"] == symbol)
        if len(open_positions) >= settings.risk.max_open_trades or symbol_open_count >= settings.risk.max_trades_per_symbol:
            continue

        locked, lock_reason = protections.is_symbol_locked(symbol)
        if locked:
            logger.info(f"{symbol}: {lock_reason}")
            continue

        specs = connector.get_symbol_specs(symbol)
        if specs is None:
            continue

        spread_atr_ratio = (specs.ask - specs.bid) / setup.atr if setup.atr > 0 else 1.0
        ml_pred = ml_pipe.predict(df_ltf, setup, spread_atr_ratio=spread_atr_ratio, vol_ratio=vol_ratio)
        if ml_pred.ml_available:
            logger.info(
                f"{symbol} | ML({ml_pred.model_version}/{ml_pred.model_name}): "
                f"p_win={ml_pred.p_win:.2f}, E[R]={ml_pred.expected_r:.2f}, "
                f"Regime={ml_pred.regime.regime}, Decision={ml_pred.decision}"
            )
            if ml_pred.decision in ("REJECT", "ABSTAIN"):
                logger.info(f"{symbol}: Filtered by ML meta-labeler ({ml_pred.decision}).")
                continue

        mem_examples = memory.get_recent_context(symbol, limit=settings.ai_brain.max_memory_examples)
        ea_sig = bridge.get_signal(symbol)
        if ea_sig:
            logger.info(f"{symbol} | EA31337 Bridge: {ea_sig.bias} ({ea_sig.consensus_score}%)")
        tv_sig = None if connector.simulate else tv_client.get_consensus(symbol)
        if tv_sig:
            logger.info(f"{symbol} | TradingView TA: {tv_sig.recommendation} ({tv_sig.score})")

        verdict = brain.evaluate(
            setup=setup,
            tf_summaries=tf_summaries,
            recent_ltf_df=df_ltf,
            session=session,
            spread_atr_ratio=spread_atr_ratio,
            memory_examples=mem_examples,
            ea31337_signal=ea_sig,
            tv_consensus=tv_sig,
        )

        logger.info(
            f"{symbol} | Setup={setup.direction} (SMC={setup.smc_score}) | "
            f"AI={verdict.decision} ({verdict.confidence}%, {verdict.market_regime}, src={verdict.source}) | "
            f"{verdict.reasoning}"
        )

        # Apply AI SL/TP refinement only if it respects direction and minimum R:R
        if verdict.refined_sl and verdict.refined_tp:
            if setup.direction == "BUY" and verdict.refined_sl < setup.entry < verdict.refined_tp:
                setup.stop_loss = verdict.refined_sl
                setup.take_profit = verdict.refined_tp
            elif setup.direction == "SELL" and verdict.refined_tp < setup.entry < verdict.refined_sl:
                setup.stop_loss = verdict.refined_sl
                setup.take_profit = verdict.refined_tp

        ai_passed = verdict.decision == "APPROVE" and verdict.confidence >= settings.ai_brain.min_confidence
        executed = False
        lot_size = 0.0

        if ai_passed:
            recent_streak = learner.get_recent_loss_streak()
            allowed, lot_size, reason = risk_mgr.validate_and_size(
                setup=setup,
                specs=specs,
                account=account,
                open_positions_count=len(open_positions),
                today_pnl=today_pnl,
                today_trades=today_trades,
                session=session,
                symbol_open_count=symbol_open_count,
                open_positions=open_positions,
                vol_ratio=vol_ratio,
                recent_loss_streak=recent_streak,
            )
            if allowed:
                res = order_mgr.execute_setup(setup, lot_size)
                executed = bool(res.get("success"))
                if executed:
                    today_trades += 1
                    notifier.send(
                        f"*FRIDAY* {setup.direction} `{symbol}` | Lots: `{lot_size}` | "
                        f"SMC: `{setup.smc_score}` | AI: `{verdict.confidence}%`"
                    )
            else:
                logger.info(f"{symbol}: Blocked by RiskManager -> {reason}")

        memory.record_decision(
            symbol=symbol,
            direction=setup.direction,
            session=session,
            htf_bias=htf_bias,
            smc_score=setup.smc_score,
            ai_decision=verdict.decision,
            ai_confidence=verdict.confidence,
            ai_regime=verdict.market_regime,
            ai_reasoning=verdict.reasoning,
            entry=setup.entry,
            sl=setup.stop_loss,
            tp=setup.take_profit,
            lot_size=lot_size,
            executed=executed,
        )

    order_mgr.manage_open_positions()


def main() -> None:
    parser = argparse.ArgumentParser(description="FRIDAY - SMC + AI Council MT5 Trading Bot")
    parser.add_argument("--config", type=str, default=None, help="Path to custom friday_config.json")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run (no live orders)")
    parser.add_argument("--live", action="store_true", help="Enable live order execution")
    parser.add_argument("--simulate", action="store_true", help="Run with synthetic data (no MT5 needed)")
    parser.add_argument("--once", action="store_true", help="Run a single scan cycle and exit")
    parser.add_argument("--no-ui", action="store_true", help="Disable the local web dashboard UI")
    args = parser.parse_args()

    logger = setup_logger(log_dir=BASE_DIR / "logs")
    settings = FridaySettings.load(args.config)

    if args.dry_run:
        settings.mode.dry_run = True
    elif args.live:
        settings.mode.dry_run = False

    logger.info(
        f"Booting FRIDAY | DryRun={settings.mode.dry_run} | Simulate={args.simulate} | "
        f"AIModel={settings.ai_brain.model}"
    )

    connector = MT5Connector(settings.credentials, simulate=args.simulate)
    if not connector.connect():
        logger.error("Failed to initialize MT5 connection. Exiting.")
        sys.exit(1)

    smc = SMCEngine(settings.smc)
    brain = FridayBrain(
        settings.ai_brain,
        api_key=settings.credentials.openai_api_key,
        gemini_api_key=settings.credentials.gemini_api_key,
        groq_api_key=settings.credentials.groq_api_key,
        ollama_base_url=settings.credentials.ollama_base_url,
        ollama_api_key=settings.credentials.ollama_api_key,
        ollama_model=settings.credentials.ollama_model,
    )
    db_mgr = DatabaseManager(BASE_DIR / "data" / "friday_memory.db")
    memory = FridayMemory(BASE_DIR / "data" / "friday_memory.db")
    learner = SelfLearner(BASE_DIR / "data" / "friday_memory.db")
    ml_pipe = MLInferencePipeline()
    bridge = EA31337Bridge(settings.ea31337_bridge)
    tv_client = TradingViewClient()
    news_guard = NewsGuard()
    protections = ProtectionManager()
    notifier = TelegramNotifier()
    risk_mgr = RiskManager(settings.risk, db=db_mgr)
    order_mgr = OrderManager(
        connector=connector,
        risk_cfg=settings.risk,
        magic_number=settings.mode.magic_number,
        dry_run=settings.mode.dry_run,
    )

    bot_state = {"paused": False}
    ui_server = None
    if not args.no_ui and not args.once:
        mode_lbl = "SIMULATE" if args.simulate else ("DRY-RUN" if settings.mode.dry_run else "LIVE")
        ui_server = start_dashboard(
            connector=connector,
            db_path=BASE_DIR / "data" / "friday_memory.db",
            log_path=BASE_DIR / "logs" / "friday.log",
            mode_label=mode_lbl,
            session_fn=detect_trading_session,
            settings=settings,
            order_mgr=order_mgr,
            bot_state=bot_state,
        )

    try:
        while True:
            if not bot_state.get("paused", False):
                run_cycle(
                    settings, connector, smc, brain, ml_pipe, memory, learner, bridge,
                    tv_client, news_guard, protections, notifier, risk_mgr, order_mgr, logger,
                )
            if args.once:
                break
            time.sleep(settings.mode.poll_interval_seconds)
    except KeyboardInterrupt:
        logger.info("FRIDAY stopped by user.")
    finally:
        if ui_server:
            ui_server.shutdown()
        connector.shutdown()
        logger.info("FRIDAY shutdown complete.")


if __name__ == "__main__":
    main()
