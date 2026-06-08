import sys
import types
from datetime import date
from types import SimpleNamespace

import pytest

from app.schemas import ResearchDepth
from app.services import tradingagents_client


def fake_settings(tmp_path, **overrides):
    values = {
        "demo_mode": False,
        "tradingagents_results_dir": str(tmp_path / "results"),
        "tradingagents_cache_dir": str(tmp_path / "cache"),
        "tradingagents_llm_provider": "minimax",
        "tradingagents_deep_think_llm": "MiniMax-M3",
        "tradingagents_quick_think_llm": "MiniMax-M3",
        "tradingagents_llm_backend_url": "https://api.minimax.io/v1",
        "tradingagents_output_language": "Traditional Chinese",
        "tradingagents_checkpoint_enabled": True,
        "tradingagents_max_debate_rounds": 2,
        "tradingagents_max_risk_rounds": 2,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def install_fake_tradingagents(monkeypatch, captured):
    tradingagents = types.ModuleType("tradingagents")
    default_config = types.ModuleType("tradingagents.default_config")
    default_config.DEFAULT_CONFIG = {
        "results_dir": "",
        "data_cache_dir": "",
        "llm_provider": "openai",
        "deep_think_llm": "gpt-5.5",
        "quick_think_llm": "gpt-5.4-mini",
        "backend_url": None,
        "output_language": "English",
        "checkpoint_enabled": False,
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
    }
    graph_package = types.ModuleType("tradingagents.graph")
    trading_graph = types.ModuleType("tradingagents.graph.trading_graph")

    class FakeTradingAgentsGraph:
        def __init__(self, *, selected_analysts, debug, config):
            captured["analysts"] = selected_analysts
            captured["debug"] = debug
            captured["config"] = config

        def propagate(self, ticker, report_date):
            captured["ticker"] = ticker
            captured["report_date"] = report_date
            return {"bull_researcher": "MiniMax M3 研究摘要"}, "最終綜合"

    trading_graph.TradingAgentsGraph = FakeTradingAgentsGraph
    monkeypatch.setitem(sys.modules, "tradingagents", tradingagents)
    monkeypatch.setitem(sys.modules, "tradingagents.default_config", default_config)
    monkeypatch.setitem(sys.modules, "tradingagents.graph", graph_package)
    monkeypatch.setitem(sys.modules, "tradingagents.graph.trading_graph", trading_graph)


def test_minimax_m3_settings_are_written_to_tradingagents_config(monkeypatch, tmp_path):
    captured = {}
    install_fake_tradingagents(monkeypatch, captured)
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setattr(tradingagents_client, "settings", fake_settings(tmp_path))

    result = tradingagents_client.run_tradingagents_research(
        ticker="AAPL",
        report_date=date(2026, 6, 6),
        depth=ResearchDepth.standard,
        analysts=["market", "news", "fundamentals"],
    )

    config = captured["config"]
    assert config["llm_provider"] == "minimax"
    assert config["deep_think_llm"] == "MiniMax-M3"
    assert config["quick_think_llm"] == "MiniMax-M3"
    assert config["backend_url"] == "https://api.minimax.io/v1"
    assert config["output_language"] == "Traditional Chinese"
    assert config["checkpoint_enabled"] is True
    assert config["max_debate_rounds"] == 2
    assert config["max_risk_discuss_rounds"] == 2
    assert captured["ticker"] == "AAPL"
    assert captured["report_date"] == "2026-06-06"
    assert "MiniMax M3" in result.sources


def test_missing_minimax_key_fails_before_importing_tradingagents(monkeypatch, tmp_path):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setattr(tradingagents_client, "settings", fake_settings(tmp_path))

    with pytest.raises(RuntimeError, match="MINIMAX_API_KEY is not set"):
        tradingagents_client.run_tradingagents_research(
            ticker="AAPL",
            report_date=date(2026, 6, 6),
            depth=ResearchDepth.standard,
            analysts=["market"],
        )


def test_deep_research_uses_high_quality_rounds(monkeypatch, tmp_path):
    captured = {}
    install_fake_tradingagents(monkeypatch, captured)
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setattr(
        tradingagents_client,
        "settings",
        fake_settings(
            tmp_path,
            tradingagents_max_debate_rounds=2,
            tradingagents_max_risk_rounds=2,
        ),
    )

    tradingagents_client.run_tradingagents_research(
        ticker="NVDA",
        report_date=date(2026, 6, 6),
        depth=ResearchDepth.deep,
        analysts=["market", "news", "fundamentals", "risk"],
    )

    assert captured["config"]["max_debate_rounds"] == 3
    assert captured["config"]["max_risk_discuss_rounds"] == 3
