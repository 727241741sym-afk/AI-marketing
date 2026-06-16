from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from threading import RLock
from typing import Any, Protocol
from uuid import uuid4

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from app.config import settings
from app.domain.report_mapper import ResearchReport
from app.domain.usage import PlanQuota, SubscriptionState, assert_can_start_research, next_usage_count
from app.schemas import ResearchDepth, ResearchRunCreate, ResearchStatus, WatchlistItemCreate


TRIAL_MONTHLY_REPORTS = 5
PRO_MONTHLY_REPORTS = 50


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


@dataclass
class WatchlistItemRecord:
    id: str
    user_id: str
    ticker: str
    company_name: str
    created_at: datetime


class ResearchRepository(Protocol):
    def get_subscription(self, user_id: str) -> SubscriptionState:
        ...

    def create_run_with_usage(
        self,
        user_id: str,
        payload: ResearchRunCreate,
    ) -> tuple[ResearchRunRecord, SubscriptionState]:
        ...

    def get_run_for_user(self, user_id: str, run_id: str) -> ResearchRunRecord | None:
        ...

    def list_runs_for_user(self, user_id: str) -> list[ResearchRunRecord]:
        ...

    def mark_running(self, run_id: str) -> ResearchRunRecord:
        ...

    def complete_run(self, run_id: str, report: ResearchReport) -> ResearchRunRecord:
        ...

    def fail_run(self, run_id: str, message: str) -> ResearchRunRecord:
        ...

    def get_report_for_user(self, user_id: str, report_id: str) -> ReportRecord | None:
        ...

    def list_watchlist_for_user(self, user_id: str) -> list[WatchlistItemRecord]:
        ...

    def create_watchlist_item(
        self,
        user_id: str,
        payload: WatchlistItemCreate,
    ) -> WatchlistItemRecord:
        ...

    def delete_watchlist_item(self, user_id: str, item_id: str) -> bool:
        ...

    def update_subscription_from_stripe(
        self,
        *,
        stripe_customer_id: str,
        stripe_subscription_id: str | None,
        status: str,
        plan: str,
        monthly_reports: int,
        user_id: str | None = None,
    ) -> bool:
        ...

    def set_stripe_customer_for_user(
        self,
        user_id: str,
        stripe_customer_id: str,
    ) -> SubscriptionState:
        ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._subscriptions: dict[str, SubscriptionState] = {}
        self._runs: dict[str, ResearchRunRecord] = {}
        self._reports: dict[str, ReportRecord] = {}
        self._watchlist: dict[str, WatchlistItemRecord] = {}

    def get_subscription(self, user_id: str) -> SubscriptionState:
        with self._lock:
            return self._subscriptions.setdefault(
                user_id,
                SubscriptionState(
                    user_id=user_id,
                    plan="trial",
                    status="trialing",
                    period_reports_used=0,
                    quota=PlanQuota(monthly_reports=TRIAL_MONTHLY_REPORTS),
                ),
            )

    def create_run_with_usage(
        self,
        user_id: str,
        payload: ResearchRunCreate,
    ) -> tuple[ResearchRunRecord, SubscriptionState]:
        with self._lock:
            current = self.get_subscription(user_id)
            reserved_reports = self._active_run_count(user_id)
            assert_can_start_research(current, reserved_reports=reserved_reports)
            run = ResearchRunRecord(
                id=f"run_{uuid4().hex[:12]}",
                user_id=user_id,
                ticker=payload.ticker,
                report_date=payload.report_date,
                depth=payload.depth,
                analysts=payload.analysts,
                status=ResearchStatus.queued,
                created_at=utc_now(),
            )
            self._runs[run.id] = run
            return run, current

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
            current = self.get_subscription(run.user_id)
            self._subscriptions[run.user_id] = SubscriptionState(
                user_id=current.user_id,
                plan=current.plan,
                status=current.status,
                period_reports_used=next_usage_count(current),
                quota=current.quota,
                stripe_customer_id=current.stripe_customer_id,
                stripe_subscription_id=current.stripe_subscription_id,
            )
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

    def list_watchlist_for_user(self, user_id: str) -> list[WatchlistItemRecord]:
        return sorted(
            [item for item in self._watchlist.values() if item.user_id == user_id],
            key=lambda item: item.created_at,
            reverse=True,
        )

    def create_watchlist_item(
        self,
        user_id: str,
        payload: WatchlistItemCreate,
    ) -> WatchlistItemRecord:
        ticker = payload.ticker
        company_name = payload.company_name
        with self._lock:
            for item in self._watchlist.values():
                if item.user_id == user_id and item.ticker == ticker:
                    item.company_name = company_name
                    return item

            item = WatchlistItemRecord(
                id=f"watch_{uuid4().hex[:12]}",
                user_id=user_id,
                ticker=ticker,
                company_name=company_name,
                created_at=utc_now(),
            )
            self._watchlist[item.id] = item
            return item

    def delete_watchlist_item(self, user_id: str, item_id: str) -> bool:
        with self._lock:
            item = self._watchlist.get(item_id)
            if item is None or item.user_id != user_id:
                return False
            del self._watchlist[item_id]
            return True

    def update_subscription_from_stripe(
        self,
        *,
        stripe_customer_id: str,
        stripe_subscription_id: str | None,
        status: str,
        plan: str,
        monthly_reports: int,
        user_id: str | None = None,
    ) -> bool:
        with self._lock:
            for existing_user_id, current in self._subscriptions.items():
                if (
                    current.stripe_customer_id == stripe_customer_id
                    or (
                        stripe_subscription_id is not None
                        and current.stripe_subscription_id == stripe_subscription_id
                    )
                ):
                    self._subscriptions[existing_user_id] = SubscriptionState(
                        user_id=current.user_id,
                        plan=plan,
                        status=status,
                        period_reports_used=current.period_reports_used,
                        quota=PlanQuota(monthly_reports=monthly_reports),
                        stripe_customer_id=stripe_customer_id,
                        stripe_subscription_id=stripe_subscription_id
                        or current.stripe_subscription_id,
                    )
                    return True
            if user_id:
                current = self.get_subscription(user_id)
                if (
                    current.stripe_customer_id
                    and current.stripe_customer_id != stripe_customer_id
                ):
                    return False
                self._subscriptions[user_id] = SubscriptionState(
                    user_id=current.user_id,
                    plan=plan,
                    status=status,
                    period_reports_used=current.period_reports_used,
                    quota=PlanQuota(monthly_reports=monthly_reports),
                    stripe_customer_id=stripe_customer_id,
                    stripe_subscription_id=stripe_subscription_id,
                )
                return True
        return False

    def set_stripe_customer_for_user(
        self,
        user_id: str,
        stripe_customer_id: str,
    ) -> SubscriptionState:
        with self._lock:
            for existing_user_id, current in self._subscriptions.items():
                if (
                    existing_user_id != user_id
                    and current.stripe_customer_id == stripe_customer_id
                ):
                    raise ValueError("Stripe customer 已綁定其他使用者")

            current = self.get_subscription(user_id)
            if current.stripe_customer_id:
                return current

            updated = SubscriptionState(
                user_id=current.user_id,
                plan=current.plan,
                status=current.status,
                period_reports_used=current.period_reports_used,
                quota=current.quota,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=current.stripe_subscription_id,
            )
            self._subscriptions[user_id] = updated
            return updated

    def _active_run_count(self, user_id: str) -> int:
        return sum(
            1
            for run in self._runs.values()
            if run.user_id == user_id
            and run.status in {ResearchStatus.queued, ResearchStatus.running}
        )


class PostgresRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool: ConnectionPool | None = None
        self._lock = RLock()

    @property
    def pool(self) -> ConnectionPool:
        with self._lock:
            if self._pool is None:
                self._pool = ConnectionPool(
                    conninfo=self._database_url,
                    min_size=1,
                    max_size=8,
                    kwargs={"row_factory": dict_row},
                )
            return self._pool

    def get_subscription(self, user_id: str) -> SubscriptionState:
        with self.pool.connection() as conn:
            with conn.transaction():
                self._ensure_subscription(conn, user_id)
                row = conn.execute(
                    """
                    select user_id, plan, status, period_reports_used, monthly_reports,
                           stripe_customer_id, stripe_subscription_id
                    from public.atlas_subscriptions
                    where user_id = %s
                    """,
                    (user_id,),
                ).fetchone()
        return _subscription_from_row(row)

    def create_run_with_usage(
        self,
        user_id: str,
        payload: ResearchRunCreate,
    ) -> tuple[ResearchRunRecord, SubscriptionState]:
        run = ResearchRunRecord(
            id=f"run_{uuid4().hex[:12]}",
            user_id=user_id,
            ticker=payload.ticker,
            report_date=payload.report_date,
            depth=payload.depth,
            analysts=payload.analysts,
            status=ResearchStatus.queued,
            created_at=utc_now(),
        )

        with self.pool.connection() as conn:
            with conn.transaction():
                self._ensure_subscription(conn, user_id)
                row = conn.execute(
                    """
                    select user_id, plan, status, period_reports_used, monthly_reports,
                           stripe_customer_id, stripe_subscription_id
                    from public.atlas_subscriptions
                    where user_id = %s
                    for update
                    """,
                    (user_id,),
                ).fetchone()
                current = _subscription_from_row(row)
                active_run_count = conn.execute(
                    """
                    select count(*) as active_count
                    from public.atlas_research_runs
                    where user_id = %s
                      and status in ('queued', 'running')
                    """,
                    (user_id,),
                ).fetchone()["active_count"]
                assert_can_start_research(
                    current,
                    reserved_reports=int(active_run_count),
                )
                conn.execute(
                    """
                    insert into public.atlas_research_runs (
                      id, user_id, ticker, report_date, depth, analysts, status, created_at
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run.id,
                        user_id,
                        run.ticker,
                        run.report_date,
                        run.depth.value,
                        run.analysts,
                        run.status.value,
                        run.created_at,
                    ),
                )

        return run, current

    def get_run_for_user(self, user_id: str, run_id: str) -> ResearchRunRecord | None:
        with self.pool.connection() as conn:
            row = conn.execute(
                """
                select *
                from public.atlas_research_runs
                where user_id = %s and id = %s
                """,
                (user_id, run_id),
            ).fetchone()
        return _run_from_row(row) if row else None

    def list_runs_for_user(self, user_id: str) -> list[ResearchRunRecord]:
        with self.pool.connection() as conn:
            rows = conn.execute(
                """
                select *
                from public.atlas_research_runs
                where user_id = %s
                order by created_at desc
                limit 100
                """,
                (user_id,),
            ).fetchall()
        return [_run_from_row(row) for row in rows]

    def mark_running(self, run_id: str) -> ResearchRunRecord:
        with self.pool.connection() as conn:
            row = conn.execute(
                """
                update public.atlas_research_runs
                set status = 'running'
                where id = %s
                returning *
                """,
                (run_id,),
            ).fetchone()
            conn.commit()
        return _run_from_row(row)

    def complete_run(self, run_id: str, report: ResearchReport) -> ResearchRunRecord:
        report_id = f"report_{uuid4().hex[:12]}"
        with self.pool.connection() as conn:
            with conn.transaction():
                run_row = conn.execute(
                    """
                    select *
                    from public.atlas_research_runs
                    where id = %s
                    for update
                    """,
                    (run_id,),
                ).fetchone()
                run = _run_from_row(run_row)
                subscription_row = conn.execute(
                    """
                    select user_id, plan, status, period_reports_used, monthly_reports,
                           stripe_customer_id, stripe_subscription_id
                    from public.atlas_subscriptions
                    where user_id = %s
                    for update
                    """,
                    (run.user_id,),
                ).fetchone()
                current = _subscription_from_row(subscription_row)
                used = next_usage_count(current)
                conn.execute(
                    """
                    update public.atlas_subscriptions
                    set period_reports_used = %s,
                        updated_at = now()
                    where user_id = %s
                    """,
                    (used, run.user_id),
                )
                conn.execute(
                    """
                    insert into public.atlas_reports (id, user_id, run_id, report, created_at)
                    values (%s, %s, %s, %s, %s)
                    """,
                    (
                        report_id,
                        run.user_id,
                        run.id,
                        Jsonb(report.model_dump(mode="json", by_alias=True)),
                        utc_now(),
                    ),
                )
                row = conn.execute(
                    """
                    update public.atlas_research_runs
                    set status = 'completed',
                        completed_at = %s,
                        report_id = %s,
                        error_message = null
                    where id = %s
                    returning *
                    """,
                    (utc_now(), report_id, run_id),
                ).fetchone()
                conn.execute(
                    """
                    insert into public.atlas_usage_events (
                      user_id, research_run_id, event_type, quantity, cost_cents, metadata
                    )
                    values (%s, %s, 'research_report_completed', 1, %s, %s)
                    """,
                    (
                        run.user_id,
                        run.id,
                        report.cost_cents,
                        Jsonb({
                            "ticker": run.ticker,
                            "depth": run.depth.value,
                            "analysts": run.analysts,
                            "reportId": report_id,
                        }),
                    ),
                )
        return _run_from_row(row)

    def fail_run(self, run_id: str, message: str) -> ResearchRunRecord:
        with self.pool.connection() as conn:
            row = conn.execute(
                """
                update public.atlas_research_runs
                set status = 'failed',
                    completed_at = %s,
                    error_message = %s
                where id = %s
                returning *
                """,
                (utc_now(), message, run_id),
            ).fetchone()
            conn.commit()
        return _run_from_row(row)

    def get_report_for_user(self, user_id: str, report_id: str) -> ReportRecord | None:
        with self.pool.connection() as conn:
            row = conn.execute(
                """
                select *
                from public.atlas_reports
                where user_id = %s and id = %s
                """,
                (user_id, report_id),
            ).fetchone()
        return _report_from_row(row) if row else None

    def list_watchlist_for_user(self, user_id: str) -> list[WatchlistItemRecord]:
        with self.pool.connection() as conn:
            rows = conn.execute(
                """
                select *
                from public.atlas_watchlist_items
                where user_id = %s
                order by created_at desc
                """,
                (user_id,),
            ).fetchall()
        return [_watchlist_from_row(row) for row in rows]

    def create_watchlist_item(
        self,
        user_id: str,
        payload: WatchlistItemCreate,
    ) -> WatchlistItemRecord:
        ticker = payload.ticker
        company_name = payload.company_name
        with self.pool.connection() as conn:
            row = conn.execute(
                """
                insert into public.atlas_watchlist_items (user_id, ticker, company_name)
                values (%s, %s, %s)
                on conflict (user_id, ticker)
                do update set company_name = excluded.company_name
                returning *
                """,
                (user_id, ticker, company_name),
            ).fetchone()
            conn.commit()
        return _watchlist_from_row(row)

    def delete_watchlist_item(self, user_id: str, item_id: str) -> bool:
        with self.pool.connection() as conn:
            cursor = conn.execute(
                """
                delete from public.atlas_watchlist_items
                where user_id = %s and id = %s
                """,
                (user_id, item_id),
            )
            conn.commit()
        return cursor.rowcount > 0

    def update_subscription_from_stripe(
        self,
        *,
        stripe_customer_id: str,
        stripe_subscription_id: str | None,
        status: str,
        plan: str,
        monthly_reports: int,
        user_id: str | None = None,
    ) -> bool:
        with self.pool.connection() as conn:
            with conn.transaction():
                cursor = conn.execute(
                    """
                    update public.atlas_subscriptions
                    set stripe_customer_id = %s,
                        stripe_subscription_id = coalesce(%s, stripe_subscription_id),
                        status = %s,
                        plan = %s,
                        monthly_reports = %s,
                        updated_at = now()
                    where stripe_customer_id = %s
                       or stripe_subscription_id = %s
                    """,
                    (
                        stripe_customer_id,
                        stripe_subscription_id,
                        status,
                        plan,
                        monthly_reports,
                        stripe_customer_id,
                        stripe_subscription_id,
                    ),
                )
                if cursor.rowcount > 0:
                    return True
                if not user_id:
                    return False
                self._ensure_subscription(conn, user_id)
                subscription_row = conn.execute(
                    """
                    select user_id, plan, status, period_reports_used, monthly_reports,
                           stripe_customer_id, stripe_subscription_id
                    from public.atlas_subscriptions
                    where user_id = %s
                    for update
                    """,
                    (user_id,),
                ).fetchone()
                current = _subscription_from_row(subscription_row)
                if (
                    current.stripe_customer_id
                    and current.stripe_customer_id != stripe_customer_id
                ):
                    return False
                conn.execute(
                    """
                    update public.atlas_subscriptions
                    set stripe_customer_id = %s,
                        stripe_subscription_id = %s,
                        status = %s,
                        plan = %s,
                        monthly_reports = %s,
                        updated_at = now()
                    where user_id = %s
                    """,
                    (
                        stripe_customer_id,
                        stripe_subscription_id,
                        status,
                        plan,
                        monthly_reports,
                        user_id,
                    ),
                )
                return True

    def set_stripe_customer_for_user(
        self,
        user_id: str,
        stripe_customer_id: str,
    ) -> SubscriptionState:
        with self.pool.connection() as conn:
            with conn.transaction():
                self._ensure_subscription(conn, user_id)
                row = conn.execute(
                    """
                    select user_id, plan, status, period_reports_used, monthly_reports,
                           stripe_customer_id, stripe_subscription_id
                    from public.atlas_subscriptions
                    where user_id = %s
                    for update
                    """,
                    (user_id,),
                ).fetchone()
                current = _subscription_from_row(row)
                if current.stripe_customer_id:
                    return current

                owner = conn.execute(
                    """
                    select user_id
                    from public.atlas_subscriptions
                    where stripe_customer_id = %s
                      and user_id <> %s
                    """,
                    (stripe_customer_id, user_id),
                ).fetchone()
                if owner:
                    raise ValueError("Stripe customer 已綁定其他使用者")

                updated_row = conn.execute(
                    """
                    update public.atlas_subscriptions
                    set stripe_customer_id = %s,
                        updated_at = now()
                    where user_id = %s
                    returning user_id, plan, status, period_reports_used, monthly_reports,
                              stripe_customer_id, stripe_subscription_id
                    """,
                    (stripe_customer_id, user_id),
                ).fetchone()
                return _subscription_from_row(updated_row)

    def _ensure_subscription(self, conn: Any, user_id: str) -> None:
        conn.execute(
            """
            insert into public.atlas_profiles (id)
            values (%s)
            on conflict (id) do nothing
            """,
            (user_id,),
        )
        conn.execute(
            """
            insert into public.atlas_subscriptions (
              user_id, plan, status, monthly_reports, period_reports_used
            )
            values (%s, 'trial', 'trialing', %s, 0)
            on conflict (user_id) do nothing
            """,
            (user_id, TRIAL_MONTHLY_REPORTS),
        )


def _subscription_from_row(row: dict[str, Any]) -> SubscriptionState:
    return SubscriptionState(
        user_id=str(row["user_id"]),
        plan=str(row["plan"]),
        status=str(row["status"]),
        period_reports_used=int(row["period_reports_used"]),
        quota=PlanQuota(monthly_reports=int(row["monthly_reports"])),
        stripe_customer_id=row.get("stripe_customer_id"),
        stripe_subscription_id=row.get("stripe_subscription_id"),
    )


def _run_from_row(row: dict[str, Any]) -> ResearchRunRecord:
    return ResearchRunRecord(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        ticker=str(row["ticker"]),
        report_date=row["report_date"],
        depth=ResearchDepth(str(row["depth"])),
        analysts=list(row["analysts"] or []),
        status=ResearchStatus(str(row["status"])),
        created_at=row["created_at"],
        completed_at=row.get("completed_at"),
        report_id=row.get("report_id"),
        error_message=row.get("error_message"),
    )


def _report_from_row(row: dict[str, Any]) -> ReportRecord:
    return ReportRecord(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        run_id=str(row["run_id"]),
        report=ResearchReport.model_validate(row["report"]),
        created_at=row["created_at"],
    )


def _watchlist_from_row(row: dict[str, Any]) -> WatchlistItemRecord:
    return WatchlistItemRecord(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        ticker=str(row["ticker"]),
        company_name=str(row["company_name"]),
        created_at=row["created_at"],
    )


def build_repository() -> ResearchRepository:
    if settings.demo_mode or settings.repository_backend == "memory":
        return InMemoryRepository()
    return PostgresRepository(settings.psycopg_database_url)


repository: ResearchRepository = build_repository()
