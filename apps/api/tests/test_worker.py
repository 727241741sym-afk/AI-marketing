from datetime import date

from app import worker as worker_module
from app.repository import InMemoryRepository
from app.schemas import ResearchDepth, ResearchRunCreate
from app.services.tradingagents_client import TradingAgentsRawResult


def create_run(repo: InMemoryRepository) -> str:
    run, _subscription = repo.create_run_with_usage(
        "00000000-0000-0000-0000-000000000010",
        ResearchRunCreate(
            ticker="AAPL",
            reportDate=date(2026, 6, 6),
            depth=ResearchDepth.standard,
            analysts=["market", "news", "fundamentals"],
        ),
    )
    return run.id


def test_worker_completes_research_run(monkeypatch):
    repo = InMemoryRepository()
    run_id = create_run(repo)

    def fake_research(**_kwargs) -> TradingAgentsRawResult:
        return TradingAgentsRawResult(
            state={
                "bull_researcher": "營收與現金流具備韌性。",
                "bear_researcher": "估值與監管仍是主要壓力。",
                "risky_analyst": "需追蹤供應鏈與市場風險。",
            },
            decision="維持觀察，本報告僅供研究用途。",
            sources=["TradingAgents", "MiniMax M3"],
            cost_cents=0,
        )

    monkeypatch.setattr(worker_module, "run_tradingagents_research", fake_research)

    worker_module.process_research_run(run_id, repo)

    run = repo.get_run_for_user("00000000-0000-0000-0000-000000000010", run_id)
    assert run is not None
    assert run.status == "completed"
    assert run.report_id is not None


def test_worker_marks_run_failed_on_timeout(monkeypatch):
    repo = InMemoryRepository()
    run_id = create_run(repo)

    def timeout_research(**_kwargs):
        raise TimeoutError("research timed out")

    monkeypatch.setattr(worker_module, "run_tradingagents_research", timeout_research)

    worker_module.process_research_run(run_id, repo)

    run = repo.get_run_for_user("00000000-0000-0000-0000-000000000010", run_id)
    assert run is not None
    assert run.status == "failed"
    assert run.error_message == "research timed out"


def test_work_horse_killed_marks_run_failed(monkeypatch):
    repo = InMemoryRepository()
    run_id = create_run(repo)
    monkeypatch.setattr(worker_module, "repository", repo)

    class FakeJob:
        args = [run_id]

    worker_module.mark_research_run_killed(FakeJob(), None, None, None)

    run = repo.get_run_for_user("00000000-0000-0000-0000-000000000010", run_id)
    assert run is not None
    assert run.status == "failed"
    assert "超過執行時間限制" in (run.error_message or "")
