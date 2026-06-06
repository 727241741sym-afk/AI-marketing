from __future__ import annotations

import json

from app.config import settings


def create_customer_portal_url(*, user_id: str) -> str:
    if not settings.stripe_secret_key:
        return f"{settings.frontend_url}/billing?portal=not-configured&user={user_id}"

    import stripe

    stripe.api_key = settings.stripe_secret_key
    session = stripe.billing_portal.Session.create(
        customer=user_id,
        return_url=f"{settings.frontend_url}/billing",
    )
    return str(session.url)


def parse_subscription_webhook(payload: bytes, signature: str | None) -> tuple[str, dict]:
    if settings.stripe_secret_key and settings.stripe_webhook_secret:
        import stripe

        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )
        return str(event["type"]), dict(event)

    event = json.loads(payload.decode("utf-8") or "{}")
    return str(event.get("type", "demo.event")), event
