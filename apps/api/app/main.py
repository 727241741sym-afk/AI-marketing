from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from app.config import settings
from app.domain.usage import UsageLimitError, assert_can_start_research, remaining_reports
from app.repository import repository
from app.schemas import (
    PortalOut,
    ResearchRunCreate,
    ResearchRunOut,
    SubscriptionOut,
    WebhookOut,
)
from app.services.stripe_billing import create_customer_portal_url, parse_subscription_webhook
from app.worker import process_research_run


app = FastAPI(title=settings.app_name)


def current_user_id(x_user_id: str | None = Header(default="demo-user")) -> str:
    return x_user_id or "demo-user"


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/subscription", response_model=SubscriptionOut)
def subscription(user_id: str = Header(default="demo-user", alias="X-User-Id")) -> SubscriptionOut:
    state = repository.get_subscription(user_id)
    return SubscriptionOut(
        plan=state.plan,
        status=state.status,
        monthlyReports=state.quota.monthly_reports,
        periodReportsUsed=state.period_reports_used,
        remainingReports=remaining_reports(state),
    )


@app.post("/api/research-runs", response_model=ResearchRunOut, status_code=202)
def create_research_run(
    payload: ResearchRunCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Header(default="demo-user", alias="X-User-Id"),
) -> ResearchRunOut:
    state = repository.get_subscription(user_id)
    try:
        assert_can_start_research(state)
    except UsageLimitError as exc:
        raise HTTPException(
            status_code=402,
            detail={"message": exc.message, "remainingReports": exc.remaining_reports},
        ) from exc

    repository.increment_usage(user_id)
    run = repository.create_run(user_id, payload)
    background_tasks.add_task(process_research_run, run.id)
    return ResearchRunOut.model_validate(run.__dict__)


@app.get("/api/research-runs", response_model=list[ResearchRunOut])
def list_research_runs(
    user_id: str = Header(default="demo-user", alias="X-User-Id"),
) -> list[ResearchRunOut]:
    return [ResearchRunOut.model_validate(run.__dict__) for run in repository.list_runs_for_user(user_id)]


@app.get("/api/research-runs/{run_id}", response_model=ResearchRunOut)
def get_research_run(
    run_id: str,
    user_id: str = Header(default="demo-user", alias="X-User-Id"),
) -> ResearchRunOut:
    run = repository.get_run_for_user(user_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="找不到研究任務")
    return ResearchRunOut.model_validate(run.__dict__)


@app.get("/api/reports/{report_id}")
def get_report(
    report_id: str,
    user_id: str = Header(default="demo-user", alias="X-User-Id"),
) -> dict:
    report = repository.get_report_for_user(user_id, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="找不到研究報告")
    return report.report.model_dump(by_alias=True)


@app.get("/api/billing/portal", response_model=PortalOut)
def billing_portal(user_id: str = Header(default="demo-user", alias="X-User-Id")) -> PortalOut:
    return PortalOut(url=create_customer_portal_url(user_id=user_id))


@app.post("/api/stripe/webhook", response_model=WebhookOut)
async def stripe_webhook(request: Request) -> WebhookOut:
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    event_type, _event = parse_subscription_webhook(payload, signature)
    return WebhookOut(received=True, eventType=event_type)
