from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_research_run_returns_completed_report_in_demo_mode():
    response = client.post(
        "/api/research-runs",
        headers={"X-User-Id": "api-test-user"},
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

    status_response = client.get(
        f"/api/research-runs/{run['id']}",
        headers={"X-User-Id": "api-test-user"},
    )
    assert status_response.status_code == 200
    completed = status_response.json()
    assert completed["status"] == "completed"
    assert completed["reportId"].startswith("report_")

    report_response = client.get(
        f"/api/reports/{completed['reportId']}",
        headers={"X-User-Id": "api-test-user"},
    )
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["ticker"] == "AAPL"
    assert report["sections"]["bullCase"]["title"] == "多頭觀點"
    assert report["disclaimer"] == "僅供研究用途，不構成投資建議或交易建議。"


def test_report_access_is_isolated_by_user_id():
    response = client.post(
        "/api/research-runs",
        headers={"X-User-Id": "owner-user"},
        json={
            "ticker": "msft",
            "reportDate": "2026-06-06",
            "depth": "quick",
            "analysts": ["market"],
        },
    )
    run = response.json()
    completed = client.get(
        f"/api/research-runs/{run['id']}",
        headers={"X-User-Id": "owner-user"},
    ).json()

    blocked = client.get(
        f"/api/reports/{completed['reportId']}",
        headers={"X-User-Id": "other-user"},
    )

    assert blocked.status_code == 404
