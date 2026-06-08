from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Atlas Research API"
    environment: str = os.getenv("APP_ENV", "development")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    repository_backend: str = os.getenv("REPOSITORY_BACKEND", "postgres")
    queue_backend: str = os.getenv("QUEUE_BACKEND", "inline")
    rq_queue_name: str = os.getenv("RQ_QUEUE_NAME", "atlas-research")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://atlas:atlas@localhost:5432/atlas_research",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_publishable_key: str = os.getenv(
        "SUPABASE_PUBLISHABLE_KEY",
        os.getenv("SUPABASE_ANON_KEY", ""),
    )
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_price_pro_monthly: str = os.getenv("STRIPE_PRICE_PRO_MONTHLY", "")
    tradingagents_results_dir: str = os.getenv(
        "TRADINGAGENTS_RESULTS_DIR",
        "/tmp/atlas-research/tradingagents",
    )
    tradingagents_cache_dir: str = os.getenv(
        "TRADINGAGENTS_CACHE_DIR",
        "/tmp/atlas-research/tradingagents-cache",
    )
    tradingagents_llm_provider: str = os.getenv(
        "TRADINGAGENTS_LLM_PROVIDER",
        "minimax",
    )
    tradingagents_deep_think_llm: str = os.getenv(
        "TRADINGAGENTS_DEEP_THINK_LLM",
        "MiniMax-M3",
    )
    tradingagents_quick_think_llm: str = os.getenv(
        "TRADINGAGENTS_QUICK_THINK_LLM",
        "MiniMax-M3",
    )
    tradingagents_llm_backend_url: str = os.getenv(
        "TRADINGAGENTS_LLM_BACKEND_URL",
        "https://api.minimax.io/v1",
    )
    tradingagents_output_language: str = os.getenv(
        "TRADINGAGENTS_OUTPUT_LANGUAGE",
        "Traditional Chinese",
    )
    tradingagents_checkpoint_enabled: bool = (
        os.getenv("TRADINGAGENTS_CHECKPOINT_ENABLED", "true").lower() == "true"
    )
    tradingagents_max_debate_rounds: int = int(
        os.getenv("TRADINGAGENTS_MAX_DEBATE_ROUNDS", "2")
    )
    tradingagents_max_risk_rounds: int = int(
        os.getenv("TRADINGAGENTS_MAX_RISK_ROUNDS", "2")
    )
    research_timeout_seconds: int = int(os.getenv("RESEARCH_TIMEOUT_SECONDS", "900"))
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    @property
    def psycopg_database_url(self) -> str:
        return self.database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    @property
    def cors_origins(self) -> list[str]:
        raw_origins = os.getenv("CORS_ORIGINS", self.frontend_url)
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        raw_regex = os.getenv("CORS_ORIGIN_REGEX", "").strip()
        return raw_regex or None


settings = Settings()
