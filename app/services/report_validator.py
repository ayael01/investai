from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class MarketData(FlexibleModel):
    prices_available: bool
    price_mode: str
    source: str
    timestamp: datetime
    is_realtime: bool
    is_delayed: bool
    usd_ils: float | None = None
    notes: str | None = None


class Summary(FlexibleModel):
    starting_value_ils: float
    current_value_ils: float
    cash_ils: float
    securities_value_ils: float
    total_pl_ils: float
    total_pl_pct: float
    recommendation: str


class Holding(FlexibleModel):
    ticker: str
    name: str
    quantity: float | None = None
    purchase_price: float | None = None
    current_price: float | None = None
    currency: str
    current_value_ils: float
    pl_ils: float
    pl_pct: float
    status: str
    price_confidence: str
    note: str | None = None


class Transaction(FlexibleModel):
    date: date
    action: str
    ticker: str
    quantity: float | None = None
    execution_price: float | None = None
    currency: str
    amount_ils: float
    original_purchase_price: float | None = None
    realized_pl_ils: float | None = None
    realized_pl_pct: float | None = None
    reason: str | None = None


class ThesisCheck(FlexibleModel):
    broken_thesis: bool
    notes: list[str] = Field(default_factory=list)


class Recommendation(FlexibleModel):
    action: str
    reason: str


class OperationalStatus(FlexibleModel):
    email_sent: bool | None = None
    google_doc_updated: bool | None = None
    google_doc_verified: bool | None = None
    notes: str | None = None


class PortfolioReport(FlexibleModel):
    schema_version: str
    report_type: Literal["virtual_portfolio_daily_report"] | str
    generated_at: datetime
    timezone: str
    portfolio_currency: str
    market_data: MarketData
    summary: Summary
    holdings: list[Holding]
    transactions: list[Transaction]
    actions_today: list[Any] = Field(default_factory=list)
    thesis_check: ThesisCheck
    recommendation: Recommendation
    operational_status: OperationalStatus | None = None


def validate_report(data: dict[str, Any]) -> PortfolioReport:
    return PortfolioReport.model_validate(data)

