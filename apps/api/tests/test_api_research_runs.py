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

    subscription = client.get("/api/subscription").json()
    assert subscription["periodReportsUsed"] == 1
    assert subscription["remainingReports"] == 4


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
    subscription = isolated_app.get_subscription("00000000-0000-0000-0000-000000000006")
    assert subscription.period_reports_used == 0


def test_invalid_research_payload_is_rejected_before_queueing():
    use_user("00000000-0000-0000-0000-000000000007")

    response = client.post(
        "/api/research-runs",
        json={
            "ticker": "AAPL;DROP",
            "reportDate": "2026-06-06",
            "depth": "standard",
            "analysts": ["market", "unknown", "risk", "social", "news", "fundamentals"],
        },
    )

    assert response.status_code == 422


def test_report_date_outside_reasonable_range_is_rejected():
    use_user("00000000-0000-0000-0000-000000000014")

    too_old = client.post(
        "/api/research-runs",
        json={
            "ticker": "AAPL",
            "reportDate": "1980-01-01",
            "depth": "standard",
            "analysts": ["market"],
        },
    )
    far_future = client.post(
        "/api/research-runs",
        json={
            "ticker": "AAPL",
            "reportDate": "2099-01-01",
            "depth": "standard",
            "analysts": ["market"],
        },
    )

    assert too_old.status_code == 422
    assert far_future.status_code == 422


def test_active_run_reservations_block_over_quota_scheduling(monkeypatch, isolated_app):
    user_id = "00000000-0000-0000-0000-000000000015"
    use_user(user_id)
    enqueued: list[str] = []
    provider_calls = 0

    def reserve_only(run_id, *_args, **_kwargs):
        enqueued.append(run_id)

    def count_provider_calls(**_kwargs):
        nonlocal provider_calls
        provider_calls += 1
        return fake_research()

    monkeypatch.setattr(main_module, "enqueue_research_run", reserve_only)
    monkeypatch.setattr(worker_module, "run_tradingagents_research", count_provider_calls)

    for index in range(5):
        response = client.post(
            "/api/research-runs",
            json={
                "ticker": f"AAPL{index}",
                "reportDate": "2026-06-06",
                "depth": "quick",
                "analysts": ["market"],
            },
        )
        assert response.status_code == 202

    blocked = client.post(
        "/api/research-runs",
        json={
            "ticker": "MSFT",
            "reportDate": "2026-06-06",
            "depth": "quick",
            "analysts": ["market"],
        },
    )

    assert blocked.status_code == 402
    assert len(enqueued) == 5
    assert provider_calls == 0
    assert isolated_app.get_subscription(user_id).period_reports_used == 0


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


def test_repeated_watchlist_item_updates_company_name():
    user_id = "00000000-0000-0000-0000-000000000008"
    use_user(user_id)

    first = client.post(
        "/api/watchlist",
        json={"ticker": "nvda", "companyName": "NVIDIA"},
    )
    second = client.post(
        "/api/watchlist",
        json={"ticker": "NVDA", "companyName": "NVIDIA Corporation"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    items = client.get("/api/watchlist").json()
    assert len(items) == 1
    assert items[0]["companyName"] == "NVIDIA Corporation"


def test_billing_checkout_creates_and_persists_customer(monkeypatch, isolated_app):
    user_id = "00000000-0000-0000-0000-000000000016"
    use_user(user_id)
    checkout_kwargs = {}

    monkeypatch.setattr(
        main_module,
        "create_stripe_customer",
        lambda *, user_id, email: "cus_created",
    )

    def fake_checkout_url(**kwargs):
        checkout_kwargs.update(kwargs)
        return "https://checkout.stripe.test/session"

    monkeypatch.setattr(main_module, "create_checkout_url", fake_checkout_url)

    response = client.post("/api/billing/checkout")

    assert response.status_code == 200
    assert response.json()["url"] == "https://checkout.stripe.test/session"
    assert checkout_kwargs["stripe_customer_id"] == "cus_created"
    assert isolated_app.get_subscription(user_id).stripe_customer_id == "cus_created"


def test_billing_checkout_reuses_existing_customer(monkeypatch, isolated_app):
    user_id = "00000000-0000-0000-0000-000000000017"
    use_user(user_id)
    isolated_app.set_stripe_customer_for_user(user_id, "cus_existing")
    checkout_kwargs = {}

    def fail_customer_create(**_kwargs):
        raise AssertionError("existing Stripe customers should be reused")

    def fake_checkout_url(**kwargs):
        checkout_kwargs.update(kwargs)
        return "https://checkout.stripe.test/session"

    monkeypatch.setattr(main_module, "create_stripe_customer", fail_customer_create)
    monkeypatch.setattr(main_module, "create_checkout_url", fake_checkout_url)

    response = client.post("/api/billing/checkout")

    assert response.status_code == 200
    assert checkout_kwargs["stripe_customer_id"] == "cus_existing"
