import pytest

from app.services.stripe_billing import (
    StripeWebhookConfigError,
    create_customer_portal_url,
    parse_subscription_webhook,
    subscription_payload_from_event,
)


def test_customer_portal_url_falls_back_when_stripe_is_not_configured():
    url = create_customer_portal_url(user_id="user_123", stripe_customer_id=None)

    assert url == "http://localhost:3000/billing?portal=not-configured&user=user_123"


def test_webhook_parser_requires_configured_signature_secret():
    with pytest.raises(StripeWebhookConfigError):
        parse_subscription_webhook(
            b'{"type":"customer.subscription.updated"}',
            signature=None,
        )


def test_subscription_payload_extracts_customer_status_and_plan():
    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "active",
                "items": {"data": [{"price": {"id": "not-configured-pro-price"}}]},
            }
        },
    }

    payload = subscription_payload_from_event(event)

    assert payload == {
        "stripe_customer_id": "cus_123",
        "stripe_subscription_id": "sub_123",
        "status": "active",
        "plan": "trial",
        "monthly_reports": 5,
    }
