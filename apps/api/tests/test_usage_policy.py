from app.domain.usage import (
    PlanQuota,
    SubscriptionState,
    UsageLimitError,
    assert_can_start_research,
    next_usage_count,
)


def test_active_subscription_with_available_quota_can_start_research():
    state = SubscriptionState(
        user_id="user_123",
        plan="pro",
        status="active",
        period_reports_used=38,
        quota=PlanQuota(monthly_reports=50),
    )

    decision = assert_can_start_research(state)

    assert decision.allowed is True
    assert decision.remaining_reports == 12
    assert decision.message == "可建立研究任務"


def test_quota_is_consumed_once_when_research_is_queued():
    state = SubscriptionState(
        user_id="user_123",
        plan="pro",
        status="active",
        period_reports_used=38,
        quota=PlanQuota(monthly_reports=50),
    )

    assert next_usage_count(state) == 39


def test_exhausted_quota_blocks_research_runs():
    state = SubscriptionState(
        user_id="user_123",
        plan="pro",
        status="active",
        period_reports_used=50,
        quota=PlanQuota(monthly_reports=50),
    )

    try:
        assert_can_start_research(state)
    except UsageLimitError as exc:
        assert exc.message == "本月研究報告額度已用完"
        assert exc.remaining_reports == 0
    else:
        raise AssertionError("Expected exhausted quota to raise UsageLimitError")


def test_inactive_subscription_blocks_research_runs():
    state = SubscriptionState(
        user_id="user_123",
        plan="pro",
        status="past_due",
        period_reports_used=10,
        quota=PlanQuota(monthly_reports=50),
    )

    try:
        assert_can_start_research(state)
    except UsageLimitError as exc:
        assert exc.message == "訂閱未啟用，請先更新付款方式"
    else:
        raise AssertionError("Expected inactive subscription to raise UsageLimitError")
