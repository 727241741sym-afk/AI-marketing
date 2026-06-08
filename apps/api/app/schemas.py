from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResearchDepth(str, Enum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class ResearchStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ResearchRunCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=12)
    report_date: date = Field(alias="reportDate")
    depth: ResearchDepth = ResearchDepth.standard
    analysts: list[str] = Field(default_factory=lambda: ["market", "news", "fundamentals"])

    model_config = {"populate_by_name": True}


class ResearchRunOut(BaseModel):
    id: str
    ticker: str
    report_date: date = Field(alias="reportDate")
    depth: ResearchDepth
    analysts: list[str]
    status: ResearchStatus
    created_at: datetime = Field(alias="createdAt")
    completed_at: datetime | None = Field(alias="completedAt", default=None)
    report_id: str | None = Field(alias="reportId", default=None)
    error_message: str | None = Field(alias="errorMessage", default=None)

    model_config = {"populate_by_name": True}


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    monthly_reports: int = Field(alias="monthlyReports")
    period_reports_used: int = Field(alias="periodReportsUsed")
    remaining_reports: int = Field(alias="remainingReports")
    stripe_customer_id: str | None = Field(alias="stripeCustomerId", default=None)

    model_config = {"populate_by_name": True}


class PortalOut(BaseModel):
    url: str


class WatchlistItemCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=12)
    company_name: str = Field(alias="companyName", min_length=1, max_length=120)

    model_config = {"populate_by_name": True}


class WatchlistItemOut(BaseModel):
    id: str
    ticker: str
    company_name: str = Field(alias="companyName")
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class WebhookOut(BaseModel):
    received: bool
    event_type: str = Field(alias="eventType")

    model_config = {"populate_by_name": True}
