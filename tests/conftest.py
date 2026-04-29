import pytest


@pytest.fixture
def valid_report_data():
    return {
        "schema_version": "1.0",
        "report_type": "virtual_portfolio_daily_report",
        "generated_at": "2026-04-29T12:19:00+03:00",
        "timezone": "Asia/Jerusalem",
        "portfolio_currency": "ILS",
        "market_data": {
            "prices_available": True,
            "price_mode": "latest_available_or_last_close",
            "source": "external_web_sources",
            "timestamp": "2026-04-29T12:19:00+03:00",
            "is_realtime": False,
            "is_delayed": True,
            "usd_ils": 3.0376,
            "notes": "Report generated before regular US market hours.",
        },
        "summary": {
            "starting_value_ils": 300000,
            "current_value_ils": 297384,
            "cash_ils": 31405,
            "securities_value_ils": 265979,
            "total_pl_ils": -2616,
            "total_pl_pct": -0.0087,
            "recommendation": "HOLD",
        },
        "holdings": [
            {
                "ticker": "SPY",
                "name": "SPDR S&P 500 ETF Trust",
                "quantity": 55,
                "purchase_price": 715.23,
                "current_price": 711.69,
                "currency": "USD",
                "current_value_ils": 118901,
                "pl_ils": -591,
                "pl_pct": -0.0049,
                "status": "HOLD",
                "price_confidence": "latest_available",
                "note": "Price obtained from external source.",
            },
            {
                "ticker": "CASH",
                "name": "Cash",
                "quantity": None,
                "purchase_price": None,
                "current_price": None,
                "currency": "ILS",
                "current_value_ils": 31405,
                "pl_ils": 0,
                "pl_pct": 0,
                "status": "AVAILABLE",
                "price_confidence": "not_applicable",
                "note": "Cash balance.",
            },
        ],
        "transactions": [
            {
                "date": "2026-04-27",
                "action": "BUY",
                "ticker": "SPY",
                "quantity": 55,
                "execution_price": 715.23,
                "currency": "USD",
                "amount_ils": 119492,
                "original_purchase_price": 715.23,
                "realized_pl_ils": None,
                "realized_pl_pct": None,
                "reason": "Initial broad US market exposure",
            }
        ],
        "actions_today": [],
        "thesis_check": {
            "broken_thesis": False,
            "notes": ["No thesis break identified."],
        },
        "recommendation": {
            "action": "HOLD",
            "reason": "Current drawdown is within normal volatility.",
        },
        "operational_status": {
            "email_sent": False,
            "google_doc_updated": True,
            "google_doc_verified": False,
            "notes": "Verification should be completed after write.",
        },
    }

