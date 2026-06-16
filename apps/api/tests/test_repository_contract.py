from app.repository import InMemoryRepository


def test_stripe_webhook_cannot_overwrite_existing_customer_binding():
    repo = InMemoryRepository()
    user_id = "00000000-0000-0000-0000-000000000018"

    repo.set_stripe_customer_for_user(user_id, "cus_existing")

    updated = repo.update_subscription_from_stripe(
        stripe_customer_id="cus_other",
        stripe_subscription_id="sub_other",
        status="active",
        plan="pro",
        monthly_reports=50,
        user_id=user_id,
    )

    subscription = repo.get_subscription(user_id)
    assert updated is False
    assert subscription.stripe_customer_id == "cus_existing"
    assert subscription.stripe_subscription_id is None
    assert subscription.plan == "trial"
