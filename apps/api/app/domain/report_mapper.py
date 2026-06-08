from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


DISCLAIMER = "僅供研究用途，不構成投資建議或交易建議。"


class ReportSection(BaseModel):
    title: str
    content: str


class ReportSections(BaseModel):
    bull_case: ReportSection = Field(alias="bullCase")
    bear_case: ReportSection = Field(alias="bearCase")
    risk_debate: ReportSection = Field(alias="riskDebate")
    final_synthesis: ReportSection = Field(alias="finalSynthesis")

    model_config = {"populate_by_name": True}


class ResearchReport(BaseModel):
    ticker: str
    report_date: str = Field(alias="reportDate")
    sections: ReportSections
    sources: list[str]
    cost_cents: int = Field(alias="costCents")
    disclaimer: str = DISCLAIMER

    model_config = {"populate_by_name": True}


def _first_present(state: dict[str, Any], keys: tuple[str, ...], fallback: str) -> str:
    for key in keys:
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def _nested_first_present(
    state: dict[str, Any],
    parent_key: str,
    keys: tuple[str, ...],
) -> str:
    parent = state.get(parent_key)
    if not isinstance(parent, dict):
        return ""
    for key in keys:
        value = parent.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _analyst_summary(state: dict[str, Any]) -> str:
    reports = [
        ("市場分析", state.get("market_report")),
        ("新聞分析", state.get("news_report")),
        ("基本面分析", state.get("fundamentals_report")),
        ("社群情緒", state.get("sentiment_report")),
    ]
    sections = [
        f"{title}\n{content.strip()}"
        for title, content in reports
        if isinstance(content, str) and content.strip()
    ]
    return "\n\n".join(sections)


def map_tradingagents_result(
    *,
    ticker: str,
    report_date: str,
    state: dict[str, Any],
    decision: str,
    sources: list[str],
    cost_cents: int,
) -> ResearchReport:
    analyst_summary = _analyst_summary(state)
    bull_case = _first_present(
        state,
        ("bull_researcher", "bull_case", "bull", "positive_research"),
        "",
    ) or _nested_first_present(
        state,
        "investment_debate_state",
        ("bull_history", "current_response"),
    ) or analyst_summary or "此代理尚未提供輸出。"
    bear_case = _first_present(
        state,
        ("bear_researcher", "bear_case", "bear", "negative_research"),
        "",
    ) or _nested_first_present(
        state,
        "investment_debate_state",
        ("bear_history", "history"),
    ) or "此代理尚未提供輸出。"
    risky = _first_present(
        state,
        ("risky_analyst", "risk_debate", "risky_analysis"),
        "",
    ) or _nested_first_present(
        state,
        "risk_debate_state",
        ("risky_history", "current_risky_response", "history"),
    )
    safe = _first_present(
        state,
        ("safe_analyst", "safe_analysis"),
        "",
    ) or _nested_first_present(
        state,
        "risk_debate_state",
        ("safe_history", "current_safe_response"),
    )
    neutral = _nested_first_present(
        state,
        "risk_debate_state",
        ("neutral_history", "current_neutral_response"),
    )
    risk_judgement = _nested_first_present(
        state,
        "risk_debate_state",
        ("judge_decision",),
    )
    risk_debate = "\n\n".join(
        part for part in (risky, safe, neutral, risk_judgement) if part
    ).strip() or "此代理尚未提供輸出。"
    final_synthesis = (
        decision.strip()
        or _first_present(
            state,
            ("final_trade_decision", "trader_investment_plan", "investment_plan"),
            "",
        )
        or _nested_first_present(
            state,
            "investment_debate_state",
            ("judge_decision",),
        )
        or "尚未生成最終綜合。"
    )

    return ResearchReport(
        ticker=ticker.upper(),
        reportDate=report_date,
        sections=ReportSections(
            bullCase=ReportSection(title="多頭觀點", content=bull_case),
            bearCase=ReportSection(title="空頭觀點", content=bear_case),
            riskDebate=ReportSection(title="風險辯論", content=risk_debate),
            finalSynthesis=ReportSection(
                title="最終綜合",
                content=final_synthesis,
            ),
        ),
        sources=sources,
        costCents=max(cost_cents, 0),
        disclaimer=DISCLAIMER,
    )
