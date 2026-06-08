import pytest
from fastapi.testclient import TestClient

from app import auth as auth_module
from app import main as main_module
from app import worker as worker_module
from app.auth import AuthenticatedUser, get_current_user
from app.queue import ResearchQueueError
from app.repository import InMemoryRepository
from app.services.tradingagents_client import TradingAgentsRawResult


client = TestClient(main_module.app)


@pytest.fixture(autouse=True)
def isolated_app(monkeypatch):
    repo = InMemoryRepository()
    monkeypatch.setattr(main_module, "repository", repo)
    monkeypatch.setattr(worker_module, "run_tradingagents_research", fake_research)
    main_module.app.dependency_overrides.clear()
    yield repo
    main_module.app.dependency_overrides.clear()


def use_user(user_id: str) -> None:
    main_module.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=user_id,
        email=f"{user_id}@example.test",
    )


def fake_research(**_kwargs) -> TradingAgentsRawResult:
    return TradingAgentsRawResult(
        state={
            "bull_researcher": "營收與現金流具備韌性。",
            "bear_researcher": "估值與監管仍是主要壓力。",
            "risky_analyst": "需追蹤供應鏈與市場風險。",
            "safe_analyst": "資產負債表提供防守性。",
        },
        decision="維持觀察，本報告僅供研究用途。",
        sources=["TradingAgents test adapter"],
        cost_cents=12,
    )


def test_missing_authentication_is_rejected():
    response = client.get("/api/subscription")

    assert response.status_code == 401
    assert response.json()["detail"] == "請先登入"


def test_invalid_supabase_token_is_rejected(monkeypatch):
    monkeypatch.setattr(auth_module, "verify_supabase_token", lambda _token: None)

    response = client.get(
        "/api/subscription",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "登入憑證無效或已過期"


def test_create_research_run_returns_completed_report_for_authenticated_user():
    use_user("00000000-0000-0000-0000-000000000001")

    response = client.post(
        "/api/research-runs",
        json={
            "ticker": "aapl",
            "reportDate": "2026-06-06",
            "depth": "standard",
            "analysts": ["market", "news", "fundamentals"],
        },
    )

    assert response.status_code == 202
    run = response.json()
    assert run["ticker"] == "AAPL"
    assert run["status"] == "queued"

    status_response = client.get(f"/api/research-runs/{run['id']}")
    assert status_response.status_code == 200
    completed = status_response.json()
    assert completed["status"] == "completed"
    assert completed["reportId"].startswith("report_")

    report_response = client.get(f"/api/reports/{completed['reportId']}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["ticker"] == "AAPL"
    assert report["sections"]["bullCase"]["title"] == "多頭觀點"
    assert report["disclaimer"] == "僅供研究用途，不構成投資建議或交易建議。"


def test_enqueue_failure_marks_run_failed(monkeypatch, isolated_app):
    use_user("00000000-0000-0000-0000-000000000006")

    def fail_enqueue(*_args, **_kwargs):
        raise ResearchQueueError("Redis unavailable")

    monkeypatch.setattr(main_module, "enqueue_research_run", fail_enqueue)

    response = client.post(
        "/api/research-runs",
        json={
            "ticker": "aapl",
            "reportDate": "2026-06-06",
            "depth": "standard",
            "analysts": ["market", "news", "fundamentals"],
        },
    )

    assert response.status_code == 503
    runs = isolated_app.list_runs_for_user("00000000-0000-0000-0000-000000000006")
    assert runs[0].status == "failed"
    assert runs[0].error_message == "Redis unavailable"


def test_report_access_is_isolated_by_authenticated_user():
    owner_id = "00000000-0000-0000-0000-000000000002"
    other_id = "00000000-0000-0000-0000-000000000003"
    use_user(owner_id)
    response = client.post(
        "/api/research-runs",
        json={
            "ticker": "msft",
            "reportDate": "2026-06-06",
            "depth": "quick",
            "analysts": ["market"],
        },
    )
    run = response.json()
    completed = client.get(f"/api/research-runs/{run['id']}").json()

    use_user(other_id)
    blocked = client.get(f"/api/reports/{completed['reportId']}")

    assert blocked.status_code == 404


def test_watchlist_items_are_isolated_by_authenticated_user():
    owner_id = "00000000-0000-0000-0000-000000000004"
    other_id = "00000000-0000-0000-0000-000000000005"
    use_user(owner_id)
    created = client.post(
        "/api/watchlist",
        json={"ticker": "nvda", "companyName": "NVIDIA"},
    )

    assert created.status_code == 201
    assert created.json()["ticker"] == "NVDA"
    assert client.get("/api/watchlist").json()[0]["ticker"] == "NVDA"

    use_user(other_id)
    assert client.get("/api/watchlist").json() == []
