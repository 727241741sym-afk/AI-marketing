from __future__ import annotations

from redis import Redis
from rq import Worker
from rq.job import Job

from app.config import settings
from app.domain.report_mapper import map_tradingagents_result
from app.repository import ResearchRepository, repository
from app.services.tradingagents_client import run_tradingagents_research


def process_research_run(run_id: str, repo: ResearchRepository | None = None) -> None:
    active_repo = repo or repository
    run = active_repo.mark_running(run_id)
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
        active_repo.complete_run(run_id, report)
    except Exception as exc:
        active_repo.fail_run(run_id, str(exc))


def mark_research_run_failed(
    job: Job,
    _connection: Redis,
    exception_type: type[BaseException],
    exception_value: BaseException,
    _traceback: object,
) -> None:
    if not job.args:
        return
    run_id = str(job.args[0])
    repository.fail_run(run_id, f"{exception_type.__name__}: {exception_value}")


def run_worker() -> None:
    connection = Redis.from_url(settings.redis_url)
    worker = Worker([settings.rq_queue_name], connection=connection)
    worker.work()


if __name__ == "__main__":
    run_worker()
