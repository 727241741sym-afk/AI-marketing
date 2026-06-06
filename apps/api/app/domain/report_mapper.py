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


def map_tradingagents_result(
    *,
    ticker: str,
    report_date: str,
    state: dict[str, Any],
    decision: str,
    sources: list[str],
    cost_cents: int,
) -> ResearchReport:
    bull_case = _first_present(
        state,
        ("bull_researcher", "bull_case", "bull", "positive_research"),
        "此代理尚未提供輸出。",
    )
    bear_case = _first_present(
        state,
        ("bear_researcher", "bear_case", "bear", "negative_research"),
        "此代理尚未提供輸出。",
    )
    risky = _first_present(
        state,
        ("risky_analyst", "risk_debate", "risky_analysis"),
        "此代理尚未提供輸出。",
    )
    safe = _first_present(
        state,
        ("safe_analyst", "safe_analysis"),
        "",
    )
    risk_debate = f"{risky}\n\n{safe}".strip()

    return ResearchReport(
        ticker=ticker.upper(),
        reportDate=report_date,
        sections=ReportSections(
            bullCase=ReportSection(title="多頭觀點", content=bull_case),
            bearCase=ReportSection(title="空頭觀點", content=bear_case),
            riskDebate=ReportSection(title="風險辯論", content=risk_debate),
            finalSynthesis=ReportSection(
                title="最終綜合",
                content=decision.strip() or "尚未生成最終綜合。",
            ),
        ),
        sources=sources,
        costCents=max(cost_cents, 0),
        disclaimer=DISCLAIMER,
    )
