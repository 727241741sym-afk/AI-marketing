from __future__ import annotations

from app.domain.report_mapper import map_tradingagents_result
from app.repository import InMemoryRepository, repository
from app.services.tradingagents_client import run_tradingagents_research


def process_research_run(run_id: str, repo: InMemoryRepository = repository) -> None:
    run = repo.mark_running(run_id)
    try:
        raw = run_tradingagents_research(
            ticker=run.ticker,
            report_date=run.report_date,
            depth=run.depth,
            analysts=run.analysts,
        )
        report = map_tradingagents_result(
            ticker=run.ticker,
            report_date=run.report_date.isoformat(),
            state=raw.state,
            decision=raw.decision,
            sources=raw.sources,
            cost_cents=raw.cost_cents,
        )
        repo.complete_run(run_id, report)
    except Exception as exc:
        repo.fail_run(run_id, str(exc))
