import pytest
from types import SimpleNamespace

from app.services import stripe_billing
from app.services.stripe_billing import StripeBillingPriceError, StripeWebhookConfigError


def test_customer_portal_url_falls_back_when_stripe_is_not_configured():
    url = stripe_billing.create_customer_portal_url(user_id="user_123", stripe_customer_id=None)

    assert url == "http://localhost:3000/billing?portal=not-configured&user=user_123"


def test_webhook_parser_requires_configured_signature_secret():
    with pytest.raises(StripeWebhookConfigError):
        stripe_billing.parse_subscription_webhook(
            b'{"type":"customer.subscription.updated"}',
            signature=None,
        )


def test_create_stripe_customer_uses_user_metadata(monkeypatch):
    calls = {}

    class FakeCustomer:
        @staticmethod
        def create(**kwargs):
            calls.update(kwargs)
            return SimpleNamespace(id="cus_created")

    fake_stripe = SimpleNamespace(
        api_key=None,
        Customer=FakeCustomer,
    )
    monkeypatch.setattr(
        "app.services.stripe_billing.settings",
        SimpleNamespace(stripe_secret_key="sk_test"),
    )
    monkeypatch.setitem(__import__("sys").modules, "stripe", fake_stripe)

    customer_id = stripe_billing.create_stripe_customer(
        user_id="00000000-0000-0000-0000-000000000011",
        email="buyer@example.test",
    )

    assert customer_id == "cus_created"
    assert calls["email"] == "buyer@example.test"
    assert calls["metadata"]["user_id"] == "00000000-0000-0000-0000-000000000011"


def test_checkout_url_uses_subscription_checkout_with_persisted_customer(monkeypatch):
    calls = {}

    class FakeSession:
        @staticmethod
        def create(**kwargs):
            calls.update(kwargs)
            return SimpleNamespace(url="https://checkout.stripe.test/session")

    fake_stripe = SimpleNamespace(
        api_key=None,
        checkout=SimpleNamespace(Session=FakeSession),
    )
    monkeypatch.setattr(
        "app.services.stripe_billing.settings",
        SimpleNamespace(
            stripe_secret_key="sk_test",
            stripe_price_pro_monthly="price_pro",
            frontend_url="https://app.example.test",
        ),
    )
    monkeypatch.setitem(__import__("sys").modules, "stripe", fake_stripe)

    url = stripe_billing.create_checkout_url(
        user_id="00000000-0000-0000-0000-000000000011",
        stripe_customer_id="cus_created",
    )

    assert url == "https://checkout.stripe.test/session"
    assert calls["mode"] == "subscription"
    assert calls["line_items"] == [{"price": "price_pro", "quantity": 1}]
    assert calls["client_reference_id"] == "00000000-0000-0000-0000-000000000011"
    assert calls["customer"] == "cus_created"
    assert calls["subscription_data"]["metadata"]["user_id"] == "00000000-0000-0000-0000-000000000011"


def test_subscription_payload_extracts_customer_status_plan_and_user(monkeypatch):
    monkeypatch.setattr(
        "app.services.stripe_billing.settings",
        SimpleNamespace(stripe_price_pro_monthly="price_pro"),
    )
    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "active",
                "metadata": {"user_id": "00000000-0000-0000-0000-000000000011"},
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    payload = stripe_billing.subscription_payload_from_event(event)

    assert payload == {
        "stripe_customer_id": "cus_123",
        "stripe_subscription_id": "sub_123",
        "status": "active",
        "plan": "pro",
        "monthly_reports": 50,
        "user_id": "00000000-0000-0000-0000-000000000011",
    }


def test_subscription_payload_rejects_unknown_price(monkeypatch):
    monkeypatch.setattr(
        "app.services.stripe_billing.settings",
        SimpleNamespace(stripe_price_pro_monthly="price_pro"),
    )
    event = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "active",
                "items": {"data": [{"price": {"id": "price_unknown"}}]},
            }
        },
    }

    with pytest.raises(StripeBillingPriceError):
        stripe_billing.subscription_payload_from_event(event)
