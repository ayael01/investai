import pytest
from pydantic import ValidationError

from app.services.report_validator import validate_report


def test_valid_report_validation(valid_report_data):
    report = validate_report(valid_report_data)

    assert report.summary.current_value_ils == 297384
    assert report.report_type == "virtual_portfolio_daily_report"


def test_missing_summary_validation_error(valid_report_data):
    valid_report_data.pop("summary")

    with pytest.raises(ValidationError) as exc_info:
        validate_report(valid_report_data)

    assert "summary" in str(exc_info.value)


def test_holdings_with_cash_null_prices(valid_report_data):
    report = validate_report(valid_report_data)
    cash = next(holding for holding in report.holdings if holding.ticker == "CASH")

    assert cash.quantity is None
    assert cash.purchase_price is None
    assert cash.current_price is None

