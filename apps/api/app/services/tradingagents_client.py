from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas import ResearchDepth


@dataclass(frozen=True)
class TradingAgentsRawResult:
    state: dict[str, Any]
    decision: str
    sources: list[str]
    cost_cents: int


def _demo_result(ticker: str, report_date: date, depth: ResearchDepth) -> TradingAgentsRawResult:
    depth_copy = {
        ResearchDepth.quick: "快速",
        ResearchDepth.standard: "標準",
        ResearchDepth.deep: "深度",
    }[depth]
    return TradingAgentsRawResult(
        state={
            "bull_researcher": (
                f"{ticker} 在 {report_date.isoformat()} 的{depth_copy}研究顯示，核心業務仍具備"
                "穩定現金流與產品生態黏性，若營收品質改善，估值可獲得支撐。"
            ),
            "bear_researcher": (
                "主要壓力來自估值偏高、成長放緩與監管不確定性；若市場風險偏好下降，"
                "股價可能先反映多重壓縮。"
            ),
            "risky_analyst": (
                "風險端需追蹤毛利率、供應鏈集中度、匯率與大型科技監管議題。"
            ),
            "safe_analyst": (
                "防守端則來自資產負債表、自由現金流與分散化服務收入。"
            ),
        },
        decision=(
            "最終綜合：目前較適合列入觀察清單並等待安全邊際，"
            "本報告僅供研究用途，不構成任何買賣建議。"
        ),
        sources=["TradingAgents demo adapter", "Yahoo Finance", "Finnhub"],
        cost_cents=12 if depth is ResearchDepth.quick else 84,
    )


def _provider_key_name(provider: str) -> str | None:
    return {
        "minimax": "MINIMAX_API_KEY",
        "minimax-cn": "MINIMAX_CN_API_KEY",
        "openai": "OPENAI_API_KEY",
    }.get(provider.lower())


def _assert_provider_key_configured() -> None:
    key_name = _provider_key_name(settings.tradingagents_llm_provider)
    if key_name and not os.getenv(key_name):
        raise RuntimeError(
            f"{key_name} is not set. Add it to the API/worker environment before running TradingAgents."
        )


def _rounds_for_depth(depth: ResearchDepth) -> tuple[int, int]:
    if depth is ResearchDepth.quick:
        return 1, 1
    if depth is ResearchDepth.deep:
        return (
            max(settings.tradingagents_max_debate_rounds, 3),
            max(settings.tradingagents_max_risk_rounds, 3),
        )
    return settings.tradingagents_max_debate_rounds, settings.tradingagents_max_risk_rounds


def run_tradingagents_research(
    *,
    ticker: str,
    report_date: date,
    depth: ResearchDepth,
    analysts: list[str],
) -> TradingAgentsRawResult:
    if settings.demo_mode:
        return _demo_result(ticker, report_date, depth)

    _assert_provider_key_configured()

    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
    except ImportError as exc:
        raise RuntimeError(
            "TradingAgents is not installed. Install the pyproject dependency or set DEMO_MODE=true."
        ) from exc

    result_dir = Path(settings.tradingagents_results_dir)
    cache_dir = Path(settings.tradingagents_cache_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    debate_rounds, risk_rounds = _rounds_for_depth(depth)
    config = DEFAULT_CONFIG.copy()
    config["results_dir"] = str(result_dir)
    config["data_cache_dir"] = str(cache_dir)
    config["llm_provider"] = settings.tradingagents_llm_provider
    config["deep_think_llm"] = settings.tradingagents_deep_think_llm
    config["quick_think_llm"] = settings.tradingagents_quick_think_llm
    config["backend_url"] = settings.tradingagents_llm_backend_url or None
    config["output_language"] = settings.tradingagents_output_language
    config["checkpoint_enabled"] = settings.tradingagents_checkpoint_enabled
    config["max_debate_rounds"] = debate_rounds
    config["max_risk_discuss_rounds"] = risk_rounds

    graph = TradingAgentsGraph(selected_analysts=analysts, debug=False, config=config)
    state, decision = graph.propagate(ticker, report_date.isoformat())
    if not isinstance(state, dict):
        state = {"raw_state": str(state)}

    return TradingAgentsRawResult(
        state=state,
        decision=str(decision),
        sources=["TradingAgents", "MiniMax M3", "Finnhub", "Yahoo Finance", "Reddit"],
        cost_cents=0,
    )
