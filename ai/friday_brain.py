"""FRIDAY AI Brain: Multi-Persona LLM Council with Structured JSON Decisions."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    OpenAI = None
    HAS_OPENAI = False

from config.settings import AIBrainConfig
from core.ea31337_bridge import EA31337Signal
from core.market_context import TimeframeSummary
from strategy.smc_engine import TradeSetup


@dataclass
class AIVerdict:
    decision: str  # "APPROVE" or "REJECT"
    confidence: int  # 0-100
    market_regime: str
    reasoning: str
    refined_sl: Optional[float] = None
    refined_tp: Optional[float] = None
    source: str = "openai"


SYSTEM_PROMPT = """You are FRIDAY, an institutional-grade quantitative trading council.
You evaluate Smart Money Concepts (SMC) trade setups using three internal analysts:
1. Structure & Liquidity Analyst: Verifies liquidity sweep quality, Order Block / FVG confluence, and Higher-Timeframe (D1/H4) alignment.
2. Macro & Volatility Guard: Checks ATR, RSI exhaustion, spread-to-ATR cost, and active trading session.
3. Risk/Reward Critic: Validates stop-loss placement beyond liquidity and realistic take-profit before opposing structure.

Rules:
- Never blindly approve. Reject counter-trend setups with weak confluence, extreme RSI exhaustion against entry, or poor spread/volatility.
- Output MUST be valid JSON with exact keys:
{
  "decision": "APPROVE" or "REJECT",
  "confidence": integer 0-100,
  "market_regime": "TRENDING" | "RANGING" | "VOLATILE" | "CHOPPY",
  "refined_sl": number or null,
  "refined_tp": number or null,
  "reasoning": "concise 1-2 sentence explanation"
}
"""


class FridayBrain:
    """Evaluates SMC setups using free/paid LLM providers (Gemini, Groq, OpenAI, Ollama) + adaptive memory."""

    def __init__(
        self,
        config: AIBrainConfig,
        api_key: str = "",
        gemini_api_key: str = "",
        groq_api_key: str = "",
        ollama_base_url: str = "",
        ollama_api_key: str = "",
        ollama_model: str = "deepseek-v4.1-flash",
    ):
        self.logger = logging.getLogger("FRIDAY")
        self.cfg = config
        self.client = None
        self.provider = "fallback"
        self.active_model = config.model

        if not HAS_OPENAI:
            return

        def _valid(k: str) -> bool:
            return bool(k and "your-" not in k.lower())

        if _valid(ollama_api_key):
            self.client = OpenAI(
                api_key=ollama_api_key,
                base_url=ollama_base_url or "https://ollama.com/v1",
            )
            self.provider = "ollama_cloud"
            self.active_model = ollama_model or "deepseek-v4.1-flash"
        elif _valid(gemini_api_key):
            self.client = OpenAI(
                api_key=gemini_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            self.provider = "gemini"
            self.active_model = "gemini-2.5-flash"
        elif _valid(groq_api_key):
            self.client = OpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            self.provider = "groq"
            self.active_model = "llama-3.3-70b-versatile"
        elif ollama_base_url:
            self.client = OpenAI(api_key="ollama", base_url=ollama_base_url)
            self.provider = "ollama"
            self.active_model = ollama_model or "llama3.2"
        elif _valid(api_key):
            self.client = OpenAI(api_key=api_key)
            self.provider = "openai"
            self.active_model = config.model

    def evaluate(
        self,
        setup: TradeSetup,
        tf_summaries: Dict[str, TimeframeSummary],
        recent_ltf_df: pd.DataFrame,
        session: str,
        spread_atr_ratio: float,
        memory_examples: List[Dict],
        ea31337_signal: Optional[EA31337Signal] = None,
    ) -> AIVerdict:
        if not self.cfg.enabled:
            return AIVerdict(
                decision="APPROVE",
                confidence=setup.smc_score,
                market_regime="ALGO_ONLY",
                reasoning="AI Brain disabled; passing deterministic SMC score.",
                source="bypass",
            )

        if self.client is None:
            return self._deterministic_fallback(setup, tf_summaries, spread_atr_ratio, ea31337_signal)

        recent_candles = recent_ltf_df.tail(12).reset_index()
        recent_candles["time"] = recent_candles["time"].astype(str)
        payload = {
            "symbol": setup.symbol,
            "session": session,
            "spread_to_atr_ratio": round(spread_atr_ratio, 4),
            "setup": {
                "direction": setup.direction,
                "entry": round(setup.entry, 6),
                "stop_loss": round(setup.stop_loss, 6),
                "take_profit": round(setup.take_profit, 6),
                "risk_reward": setup.risk_reward,
                "smc_score": setup.smc_score,
                "confluence_tags": setup.confluence_tags,
                "notes": setup.notes,
            },
            "multi_timeframe_context": {
                tf: {
                    "trend": s.trend,
                    "ema_20": s.ema_20,
                    "ema_50": s.ema_50,
                    "rsi_14": s.rsi_14,
                    "atr_14": s.atr_14,
                }
                for tf, s in tf_summaries.items()
            },
            "recent_m15_candles": recent_candles[["time", "open", "high", "low", "close", "tick_volume"]].to_dict(
                orient="records"
            ),
            "recent_memory": memory_examples,
            "ea31337_indicator_consensus": (
                {
                    "bias": ea31337_signal.bias,
                    "consensus_score": ea31337_signal.consensus_score,
                    "active_strategies": ea31337_signal.active_strategies,
                }
                if ea31337_signal
                else None
            ),
        }

        try:
            response = self.client.chat.completions.create(
                model=self.active_model,
                temperature=self.cfg.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload)},
                ],
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)

            decision = str(data.get("decision", "REJECT")).upper()
            if decision not in ("APPROVE", "REJECT"):
                decision = "REJECT"

            confidence = int(max(0, min(100, int(data.get("confidence", 0)))))
            regime = str(data.get("market_regime", "UNKNOWN"))
            reasoning = str(data.get("reasoning", "No reasoning provided."))

            refined_sl = data.get("refined_sl") if self.cfg.allow_tp_sl_refinement else None
            refined_tp = data.get("refined_tp") if self.cfg.allow_tp_sl_refinement else None

            return AIVerdict(
                decision=decision,
                confidence=confidence,
                market_regime=regime,
                reasoning=reasoning,
                refined_sl=float(refined_sl) if refined_sl is not None else None,
                refined_tp=float(refined_tp) if refined_tp is not None else None,
                source=self.provider,
            )
        except Exception as exc:
            self.logger.warning(f"OpenAI evaluation failed ({exc}); using deterministic fallback.")
            return self._deterministic_fallback(setup, tf_summaries, spread_atr_ratio, ea31337_signal)

    def _deterministic_fallback(
        self,
        setup: TradeSetup,
        tf_summaries: Dict[str, TimeframeSummary],
        spread_atr_ratio: float,
        ea31337_signal: Optional[EA31337Signal] = None,
    ) -> AIVerdict:
        """Rule-based fallback when no OpenAI key is configured."""
        score = setup.smc_score
        if spread_atr_ratio > 0.2:
            score -= 15
        htf_aligned = "HTFAligned" in setup.confluence_tags
        if htf_aligned:
            score += 5
        if ea31337_signal:
            aligned = (setup.direction == "BUY" and ea31337_signal.bias == "BULLISH") or (
                setup.direction == "SELL" and ea31337_signal.bias == "BEARISH"
            )
            if aligned:
                score += 10
            elif ea31337_signal.bias != "NEUTRAL":
                score -= 10
        score = max(0, min(100, score))
        decision = "APPROVE" if score >= self.cfg.min_confidence else "REJECT"
        return AIVerdict(
            decision=decision,
            confidence=score,
            market_regime="TRENDING" if htf_aligned else "RANGING",
            reasoning="Local council fallback (set OPENAI_API_KEY in .env for full GPT reasoning).",
            source="fallback",
        )
