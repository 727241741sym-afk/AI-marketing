from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from threading import RLock
from uuid import uuid4

from app.domain.report_mapper import ResearchReport
from app.domain.usage import PlanQuota, SubscriptionState, next_usage_count
from app.schemas import ResearchDepth, ResearchRunCreate, ResearchStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ResearchRunRecord:
    id: str
    user_id: str
    ticker: str
    report_date: date
    depth: ResearchDepth
    analysts: list[str]
    status: ResearchStatus
    created_at: datetime
    completed_at: datetime | None = None
    report_id: str | None = None
    error_message: str | None = None


@dataclass
class ReportRecord:
    id: str
    user_id: str
    run_id: str
    report: ResearchReport
    created_at: datetime


class InMemoryRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._subscriptions: dict[str, SubscriptionState] = {
            "demo-user": SubscriptionState(
                user_id="demo-user",
                plan="pro",
                status="active",
                period_reports_used=38,
                quota=PlanQuota(monthly_reports=50),
            )
        }
        self._runs: dict[str, ResearchRunRecord] = {}
        self._reports: dict[str, ReportRecord] = {}

    def get_subscription(self, user_id: str) -> SubscriptionState:
        with self._lock:
            return self._subscriptions.setdefault(
                user_id,
                SubscriptionState(
                    user_id=user_id,
                    plan="trial",
                    status="trialing",
                    period_reports_used=0,
                    quota=PlanQuota(monthly_reports=5),
                ),
            )

    def increment_usage(self, user_id: str) -> SubscriptionState:
        with self._lock:
            current = self.get_subscription(user_id)
            updated = SubscriptionState(
                user_id=current.user_id,
                plan=current.plan,
                status=current.status,
                period_reports_used=next_usage_count(current),
                quota=current.quota,
            )
            self._subscriptions[user_id] = updated
            return updated

    def create_run(self, user_id: str, payload: ResearchRunCreate) -> ResearchRunRecord:
        with self._lock:
            run = ResearchRunRecord(
                id=f"run_{uuid4().hex[:12]}",
                user_id=user_id,
                ticker=payload.ticker.strip().upper(),
                report_date=payload.report_date,
                depth=payload.depth,
                analysts=payload.analysts,
                status=ResearchStatus.queued,
                created_at=utc_now(),
            )
            self._runs[run.id] = run
            return run

    def get_run_for_user(self, user_id: str, run_id: str) -> ResearchRunRecord | None:
        run = self._runs.get(run_id)
        if run is None or run.user_id != user_id:
            return None
        return run

    def list_runs_for_user(self, user_id: str) -> list[ResearchRunRecord]:
        return sorted(
            [run for run in self._runs.values() if run.user_id == user_id],
            key=lambda run: run.created_at,
            reverse=True,
        )

    def mark_running(self, run_id: str) -> ResearchRunRecord:
        with self._lock:
            run = self._runs[run_id]
            run.status = ResearchStatus.running
            return run

    def complete_run(self, run_id: str, report: ResearchReport) -> ResearchRunRecord:
        with self._lock:
            run = self._runs[run_id]
            report_record = ReportRecord(
                id=f"report_{uuid4().hex[:12]}",
                user_id=run.user_id,
                run_id=run.id,
                report=report,
                created_at=utc_now(),
            )
            self._reports[report_record.id] = report_record
            run.status = ResearchStatus.completed
            run.completed_at = utc_now()
            run.report_id = report_record.id
            return run

    def fail_run(self, run_id: str, message: str) -> ResearchRunRecord:
        with self._lock:
            run = self._runs[run_id]
            run.status = ResearchStatus.failed
            run.completed_at = utc_now()
            run.error_message = message
            return run

    def get_report_for_user(self, user_id: str, report_id: str) -> ReportRecord | None:
        report = self._reports.get(report_id)
        if report is None or report.user_id != user_id:
            return None
        return report


repository = InMemoryRepository()
