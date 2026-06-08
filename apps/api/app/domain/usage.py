from __future__ import annotations

from dataclasses import dataclass


ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}


@dataclass(frozen=True)
class PlanQuota:
    monthly_reports: int


@dataclass(frozen=True)
class SubscriptionState:
    user_id: str
    plan: str
    status: str
    period_reports_used: int
    quota: PlanQuota
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None


@dataclass(frozen=True)
class UsageDecision:
    allowed: bool
    remaining_reports: int
    message: str


class UsageLimitError(Exception):
    def __init__(self, message: str, remaining_reports: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.remaining_reports = remaining_reports


def remaining_reports(state: SubscriptionState) -> int:
    return max(state.quota.monthly_reports - state.period_reports_used, 0)


def assert_can_start_research(state: SubscriptionState) -> UsageDecision:
    remaining = remaining_reports(state)
    if state.status not in ACTIVE_SUBSCRIPTION_STATUSES:
        raise UsageLimitError("訂閱未啟用，請先更新付款方式", remaining)

    if remaining <= 0:
        raise UsageLimitError("本月研究報告額度已用完", 0)

    return UsageDecision(
        allowed=True,
        remaining_reports=remaining,
        message="可建立研究任務",
    )


def next_usage_count(state: SubscriptionState) -> int:
    assert_can_start_research(state)
    return state.period_reports_used + 1
