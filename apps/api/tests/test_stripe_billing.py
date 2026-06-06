from app.services.stripe_billing import create_customer_portal_url, parse_subscription_webhook


def test_customer_portal_url_falls_back_when_stripe_is_not_configured():
    url = create_customer_portal_url(user_id="demo-user")

    assert url == "http://localhost:3000/billing?portal=not-configured&user=demo-user"


def test_demo_webhook_parser_accepts_json_payload_without_signature():
    event_type, event = parse_subscription_webhook(
        b'{"type":"customer.subscription.updated","data":{"object":{"status":"active"}}}',
        signature=None,
    )

    assert event_type == "customer.subscription.updated"
    assert event["data"]["object"]["status"] == "active"
