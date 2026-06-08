from types import SimpleNamespace

from app import queue as queue_module


def test_rq_enqueue_uses_configured_timeout(monkeypatch):
    calls = []

    class FakeQueue:
        def enqueue(self, *args, **kwargs):
            calls.append((args, kwargs))

    monkeypatch.setattr(
        queue_module,
        "settings",
        SimpleNamespace(
            queue_backend="rq",
            research_timeout_seconds=321,
            rq_queue_name="atlas-research",
            redis_url="redis://example.test:6379/0",
        ),
    )
    monkeypatch.setattr(queue_module, "get_research_queue", lambda: FakeQueue())

    queue_module.enqueue_research_run("run_123")

    assert calls
    args, kwargs = calls[0]
    assert args[1] == "run_123"
    assert kwargs["job_timeout"] == 321
    assert kwargs["result_ttl"] == 86_400
    assert kwargs["failure_ttl"] == 86_400
    assert kwargs["on_failure"].__name__ == "mark_research_run_failed"
