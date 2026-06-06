from app.domain.report_mapper import map_tradingagents_result


def test_tradingagents_result_is_mapped_to_traditional_chinese_report_sections():
    state = {
        "bull_researcher": "Revenue growth remains resilient and services margin expanded.",
        "bear_researcher": "Valuation leaves little room for multiple compression.",
        "risky_analyst": "Supply-chain concentration and regulatory pressure remain material.",
        "safe_analyst": "Balance sheet strength offsets near-term demand volatility.",
    }
    decision = "Hold. The debate favors disciplined sizing rather than aggressive entry."

    report = map_tradingagents_result(
        ticker="AAPL",
        report_date="2026-06-06",
        state=state,
        decision=decision,
        sources=["Finnhub", "Yahoo Finance"],
        cost_cents=84,
    )

    assert report.ticker == "AAPL"
    assert report.report_date == "2026-06-06"
    assert report.sections.bull_case.title == "多頭觀點"
    assert "Revenue growth" in report.sections.bull_case.content
    assert report.sections.bear_case.title == "空頭觀點"
    assert "Valuation" in report.sections.bear_case.content
    assert report.sections.risk_debate.title == "風險辯論"
    assert "Supply-chain" in report.sections.risk_debate.content
    assert report.sections.final_synthesis.title == "最終綜合"
    assert "Hold" in report.sections.final_synthesis.content
    assert report.disclaimer == "僅供研究用途，不構成投資建議或交易建議。"
    assert report.sources == ["Finnhub", "Yahoo Finance"]
    assert report.cost_cents == 84


def test_missing_agent_output_uses_clear_pending_copy():
    report = map_tradingagents_result(
        ticker="MSFT",
        report_date="2026-06-06",
        state={},
        decision="",
        sources=[],
        cost_cents=0,
    )

    assert report.sections.bull_case.content == "此代理尚未提供輸出。"
    assert report.sections.final_synthesis.content == "尚未生成最終綜合。"
