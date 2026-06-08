from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.auth import AuthenticatedUser, get_current_user
from app.config import settings
from app.domain.usage import UsageLimitError, remaining_reports
from app.queue import ResearchQueueError, enqueue_research_run
from app.repository import repository
from app.schemas import (
    PortalOut,
    ResearchRunCreate,
    ResearchRunOut,
    SubscriptionOut,
    WatchlistItemCreate,
    WatchlistItemOut,
    WebhookOut,
)
from app.services.stripe_billing import (
    StripeWebhookConfigError,
    StripeWebhookSignatureError,
    create_customer_portal_url,
    parse_subscription_webhook,
    subscription_payload_from_event,
)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/subscription", response_model=SubscriptionOut)
def subscription(user: AuthenticatedUser = Depends(get_current_user)) -> SubscriptionOut:
    state = repository.get_subscription(user.id)
    return SubscriptionOut(
        plan=state.plan,
        status=state.status,
        monthlyReports=state.quota.monthly_reports,
        periodReportsUsed=state.period_reports_used,
        remainingReports=remaining_reports(state),
        stripeCustomerId=state.stripe_customer_id,
    )


@app.post("/api/research-runs", response_model=ResearchRunOut, status_code=202)
def create_research_run(
    payload: ResearchRunCreate,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ResearchRunOut:
    try:
        run, _updated_subscription = repository.create_run_with_usage(user.id, payload)
    except UsageLimitError as exc:
        raise HTTPException(
            status_code=402,
            detail={"message": exc.message, "remainingReports": exc.remaining_reports},
        ) from exc

    response = ResearchRunOut.model_validate(run.__dict__)
    try:
        enqueue_research_run(run.id, repository)
    except ResearchQueueError as exc:
        repository.fail_run(run.id, str(exc))
        raise HTTPException(status_code=503, detail="背景研究任務排程失敗，請稍後再試") from exc
    return response


@app.get("/api/research-runs", response_model=list[ResearchRunOut])
def list_research_runs(
    user: AuthenticatedUser = Depends(get_current_user),
) -> list[ResearchRunOut]:
    return [
        ResearchRunOut.model_validate(run.__dict__)
        for run in repository.list_runs_for_user(user.id)
    ]


@app.get("/api/research-runs/{run_id}", response_model=ResearchRunOut)
def get_research_run(
    run_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ResearchRunOut:
    run = repository.get_run_for_user(user.id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="找不到研究任務")
    return ResearchRunOut.model_validate(run.__dict__)


@app.get("/api/reports/{report_id}")
def get_report(
    report_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    report = repository.get_report_for_user(user.id, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="找不到研究報告")
    return report.report.model_dump(by_alias=True)


@app.get("/api/watchlist", response_model=list[WatchlistItemOut])
def list_watchlist(
    user: AuthenticatedUser = Depends(get_current_user),
) -> list[WatchlistItemOut]:
    return [
        WatchlistItemOut.model_validate(item.__dict__)
        for item in repository.list_watchlist_for_user(user.id)
    ]


@app.post("/api/watchlist", response_model=WatchlistItemOut, status_code=201)
def create_watchlist_item(
    payload: WatchlistItemCreate,
    user: AuthenticatedUser = Depends(get_current_user),
) -> WatchlistItemOut:
    item = repository.create_watchlist_item(user.id, payload)
    return WatchlistItemOut.model_validate(item.__dict__)


@app.delete("/api/watchlist/{item_id}", status_code=204)
def delete_watchlist_item(
    item_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    deleted = repository.delete_watchlist_item(user.id, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="找不到觀察標的")


@app.get("/api/billing/portal", response_model=PortalOut)
def billing_portal(user: AuthenticatedUser = Depends(get_current_user)) -> PortalOut:
    state = repository.get_subscription(user.id)
    return PortalOut(
        url=create_customer_portal_url(
            user_id=user.id,
            stripe_customer_id=state.stripe_customer_id,
        )
    )


@app.post("/api/stripe/webhook", response_model=WebhookOut)
async def stripe_webhook(request: Request) -> WebhookOut:
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        event_type, event = parse_subscription_webhook(payload, signature)
    except StripeWebhookSignatureError as exc:
        raise HTTPException(status_code=400, detail="Stripe webhook 簽章無效") from exc
    except StripeWebhookConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    subscription_update = subscription_payload_from_event(event)
    if subscription_update is not None:
        repository.update_subscription_from_stripe(**subscription_update)

    return WebhookOut(received=True, eventType=event_type)
