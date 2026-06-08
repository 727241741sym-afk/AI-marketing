from __future__ import annotations

from functools import lru_cache
from typing import Literal

from redis import Redis
from rq import Queue

from app.config import settings
from app.repository import ResearchRepository


class ResearchQueueError(RuntimeError):
    pass


QueueBackend = Literal["inline", "rq"]


@lru_cache(maxsize=1)
def get_redis_connection() -> Redis:
    return Redis.from_url(settings.redis_url)


@lru_cache(maxsize=1)
def get_research_queue() -> Queue:
    return Queue(settings.rq_queue_name, connection=get_redis_connection())


def enqueue_research_run(run_id: str, repo: ResearchRepository | None = None) -> None:
    backend = settings.queue_backend.lower()
    if backend == "inline":
        from app.worker import process_research_run

        process_research_run(run_id, repo)
        return

    if backend == "rq":
        try:
            from app.worker import mark_research_run_failed, process_research_run

            get_research_queue().enqueue(
                process_research_run,
                run_id,
                job_timeout=settings.research_timeout_seconds,
                result_ttl=86_400,
                failure_ttl=86_400,
                on_failure=mark_research_run_failed,
            )
        except Exception as exc:
            raise ResearchQueueError("背景研究任務排程失敗") from exc
        return

    raise ResearchQueueError(f"不支援的 QUEUE_BACKEND：{settings.queue_backend}")
