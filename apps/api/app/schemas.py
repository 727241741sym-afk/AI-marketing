from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
import re

from pydantic import BaseModel, Field, field_validator


class ResearchDepth(str, Enum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class ResearchStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


VALID_ANALYSTS = {"market", "news", "fundamentals", "social", "risk"}
TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,11}$")
MIN_REPORT_DATE = date(1990, 1, 1)
MAX_REPORT_DATE_DRIFT_DAYS = 1


def normalize_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not TICKER_PATTERN.fullmatch(ticker):
        raise ValueError("股票代號只能包含英文字母、數字、點號或連字號，且需以英文字母開頭")
    return ticker


class ResearchRunCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=12)
    report_date: date = Field(alias="reportDate")
    depth: ResearchDepth = ResearchDepth.standard
    analysts: list[str] = Field(
        default_factory=lambda: ["market", "news", "fundamentals"],
        min_length=1,
        max_length=5,
    )

    model_config = {"populate_by_name": True}

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        return normalize_ticker(value)

    @field_validator("report_date")
    @classmethod
    def validate_report_date(cls, value: date) -> date:
        latest_allowed = date.today() + timedelta(days=MAX_REPORT_DATE_DRIFT_DAYS)
        if value < MIN_REPORT_DATE:
            raise ValueError("報告日期不可早於 1990-01-01")
        if value > latest_allowed:
            raise ValueError("報告日期不可晚於明日")
        return value

    @field_validator("analysts")
    @classmethod
    def validate_analysts(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower() for item in value]
        invalid = [item for item in normalized if item not in VALID_ANALYSTS]
        if invalid:
            raise ValueError(f"不支援的分析代理：{', '.join(invalid)}")
        if len(set(normalized)) != len(normalized):
            raise ValueError("分析代理不可重複")
        return normalized


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


class CheckoutOut(BaseModel):
    url: str


class WatchlistItemCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=12)
    company_name: str = Field(alias="companyName", min_length=1, max_length=120)

    model_config = {"populate_by_name": True}

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        return normalize_ticker(value)

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        company_name = value.strip()
        if not company_name:
            raise ValueError("公司名稱不可空白")
        return company_name


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
