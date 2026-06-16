from __future__ import annotations

import json
from typing import Any

from app.config import settings
from app.repository import PRO_MONTHLY_REPORTS, TRIAL_MONTHLY_REPORTS


class StripeWebhookConfigError(Exception):
    pass


class StripeWebhookSignatureError(Exception):
    pass


class StripeBillingCustomerError(Exception):
    pass


class StripeBillingPriceError(Exception):
    pass


def create_stripe_customer(
    *,
    user_id: str,
    email: str | None,
) -> str | None:
    if not settings.stripe_secret_key:
        return None

    import stripe

    stripe.api_key = settings.stripe_secret_key
    customer = stripe.Customer.create(
        email=email,
        metadata={"user_id": user_id},
    )
    return str(customer.id)


def create_checkout_url(
    *,
    user_id: str,
    stripe_customer_id: str | None,
) -> str:
    if not settings.stripe_secret_key:
        return f"{settings.frontend_url}/billing?checkout=not-configured&user={user_id}"

    if not settings.stripe_price_pro_monthly:
        raise StripeBillingPriceError("Stripe Pro price id 尚未設定")
    if not stripe_customer_id:
        raise StripeBillingCustomerError("尚未建立 Stripe customer，請先稍後再試")

    import stripe

    stripe.api_key = settings.stripe_secret_key
    session_params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": settings.stripe_price_pro_monthly, "quantity": 1}],
        "success_url": f"{settings.frontend_url}/billing?checkout=success",
        "cancel_url": f"{settings.frontend_url}/billing?checkout=cancelled",
        "client_reference_id": user_id,
        "metadata": {"user_id": user_id},
        "subscription_data": {"metadata": {"user_id": user_id}},
        "customer": stripe_customer_id,
    }

    session = stripe.checkout.Session.create(**session_params)
    return str(session.url)


def create_customer_portal_url(
    *,
    user_id: str,
    stripe_customer_id: str | None,
) -> str:
    if not settings.stripe_secret_key:
        return f"{settings.frontend_url}/billing?portal=not-configured&user={user_id}"

    if not stripe_customer_id:
        raise StripeBillingCustomerError("尚未建立 Stripe customer，請先升級方案")

    import stripe

    stripe.api_key = settings.stripe_secret_key
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{settings.frontend_url}/billing",
    )
    return str(session.url)


def parse_subscription_webhook(payload: bytes, signature: str | None) -> tuple[str, dict]:
    if not settings.stripe_webhook_secret:
        if settings.demo_mode:
            event = json.loads(payload.decode("utf-8") or "{}")
            return str(event.get("type", "demo.event")), event
        raise StripeWebhookConfigError("Stripe webhook secret 尚未設定")

    try:
        import stripe

        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )
    except Exception as exc:
        raise StripeWebhookSignatureError("Stripe webhook signature verification failed") from exc

    return str(event["type"]), dict(event)


def subscription_payload_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    event_type = str(event.get("type", ""))
    if not event_type.startswith("customer.subscription."):
        return None

    obj = event.get("data", {}).get("object", {})
    if not isinstance(obj, dict):
        return None

    stripe_customer_id = obj.get("customer")
    if not isinstance(stripe_customer_id, str) or not stripe_customer_id:
        return None

    stripe_subscription_id = obj.get("id")
    status = obj.get("status")
    price_id = _first_price_id(obj)
    if not price_id or price_id != settings.stripe_price_pro_monthly:
        raise StripeBillingPriceError(f"Stripe price id 未設定或不支援：{price_id or 'missing'}")

    metadata = obj.get("metadata", {})
    user_id = metadata.get("user_id") if isinstance(metadata, dict) else None

    return {
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id if isinstance(stripe_subscription_id, str) else None,
        "status": status if isinstance(status, str) else "incomplete",
        "plan": "pro",
        "monthly_reports": PRO_MONTHLY_REPORTS,
        "user_id": user_id if isinstance(user_id, str) and user_id else None,
    }


def _first_price_id(subscription: dict[str, Any]) -> str | None:
    items = subscription.get("items", {}).get("data", [])
    if not isinstance(items, list) or not items:
        return None
    price = items[0].get("price", {}) if isinstance(items[0], dict) else {}
    price_id = price.get("id") if isinstance(price, dict) else None
    return price_id if isinstance(price_id, str) else None
