from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Atlas Research API"
    environment: str = os.getenv("APP_ENV", "development")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://atlas:atlas@localhost:5432/atlas_research",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_price_pro_monthly: str = os.getenv("STRIPE_PRICE_PRO_MONTHLY", "")
    tradingagents_results_dir: str = os.getenv(
        "TRADINGAGENTS_RESULTS_DIR",
        "/tmp/atlas-research/tradingagents",
    )
    research_timeout_seconds: int = int(os.getenv("RESEARCH_TIMEOUT_SECONDS", "900"))
    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() == "true"


settings = Settings()
