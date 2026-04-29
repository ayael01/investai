from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import main
from app.services.formatters import (
    calculate_allocation,
    display_list,
    display_text,
    format_ils,
    format_percent,
    format_usd,
)
from app.services.report_validator import validate_report


def test_percent_formatting():
    assert format_percent(-0.0087) == "-0.87%"


def test_ils_formatting():
    assert format_ils(297384) == '297,384 ש"ח'


def test_usd_formatting():
    assert format_usd(711.69) == "$711.69"


def test_token_protection_behavior(monkeypatch):
    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(
            dashboard_access_token="secret",
            google_doc_id="doc",
            google_application_credentials=None,
            cache_ttl_seconds=300,
        ),
    )
    main.cache.clear()
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 403
    assert client.get("/healthz").status_code == 200


def test_allocation_calculation():
    assert calculate_allocation(31405, 297384) == 10.56
    assert calculate_allocation(100, 0) == 0.0


def test_display_text_prefers_hebrew_field():
    value = {"reason": "English reason", "reason_he": "סיבה בעברית"}

    assert display_text(value, "reason") == "סיבה בעברית"
    assert display_text({"reason": "English reason"}, "reason") == "English reason"


def test_display_list_prefers_hebrew_field():
    value = {"notes": ["English note"], "notes_he": ["הערה בעברית"]}

    assert display_list(value, "notes") == ["הערה בעברית"]


def test_dashboard_renders_hebrew_html(monkeypatch, valid_report_data):
    report = validate_report(valid_report_data)
    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(
            dashboard_access_token=None,
            google_doc_id="doc",
            google_application_credentials=None,
            cache_ttl_seconds=300,
        ),
    )
    monkeypatch.setattr(main, "load_report", lambda force=False: report)
    main.cache.clear()
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'lang="he" dir="rtl"' in response.text
    assert "דוח תיק מודל וירטואלי" in response.text


def test_dashboard_prefers_hebrew_display_fields(monkeypatch, valid_report_data):
    valid_report_data["title"] = "Portfolio Model Dashboard"
    valid_report_data["title_he"] = "דשבורד תיק מודל"
    valid_report_data["subtitle"] = "Virtual Model Portfolio"
    valid_report_data["subtitle_he"] = "תיק מודל וירטואלי"
    valid_report_data["description"] = "English dashboard description"
    valid_report_data["description_he"] = "תיאור דשבורד בעברית"
    valid_report_data["disclaimer"] = "English disclaimer"
    valid_report_data["disclaimer_he"] = "הבהרה בעברית"
    valid_report_data["market_data"]["notes"] = "English market note"
    valid_report_data["market_data"]["notes_he"] = "הערת שוק בעברית"
    valid_report_data["market_data"]["price_mode_he"] = "מחיר אחרון זמין"
    valid_report_data["holdings"][0]["display_name_he"] = "קרן סל שוק רחב"
    valid_report_data["holdings"][0]["note"] = "Price obtained from external source as latest available price."
    valid_report_data["holdings"][0]["note_he"] = "המחיר נלקח ממקור חיצוני כמחיר אחרון זמין."
    valid_report_data["holdings"][0]["status_he"] = "החזק"
    valid_report_data["holdings"][0]["price_confidence_he"] = "מחיר אחרון זמין"
    valid_report_data["transactions"][0]["action_he"] = "קנייה"
    valid_report_data["transactions"][0]["reason"] = "Initial broad US market exposure"
    valid_report_data["transactions"][0]["reason_he"] = "פתיחת חשיפה רחבה לשוק האמריקאי"
    valid_report_data["thesis_check"]["notes"] = ["No thesis break identified."]
    valid_report_data["thesis_check"]["notes_he"] = ["לא זוהתה שבירת תזה."]
    valid_report_data["recommendation"]["action_he"] = "החזק"
    valid_report_data["recommendation"]["reason"] = (
        "Current drawdown is within normal volatility and no thesis break was identified."
    )
    valid_report_data["recommendation"]["reason_he"] = (
        "הירידה הנוכחית עדיין נמצאת בטווח תנודתיות סביר, ולא זוהתה שבירת תזה."
    )
    valid_report_data["operational_status"]["notes"] = "English operational note"
    valid_report_data["operational_status"]["notes_he"] = "הערה תפעולית בעברית"
    report = validate_report(valid_report_data)
    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(
            dashboard_access_token=None,
            google_doc_id="doc",
            google_application_credentials=None,
            cache_ttl_seconds=300,
        ),
    )
    monkeypatch.setattr(main, "load_report", lambda force=False: report)
    main.cache.clear()
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "דשבורד תיק מודל" in response.text
    assert "תיק מודל וירטואלי" in response.text
    assert "הערת שוק בעברית" in response.text
    assert "תיאור דשבורד בעברית" in response.text
    assert "הבהרה בעברית" in response.text
    assert "קרן סל שוק רחב" in response.text
    assert "המחיר נלקח ממקור חיצוני כמחיר אחרון זמין." in response.text
    assert "לא זוהתה שבירת תזה." in response.text
    assert "הירידה הנוכחית עדיין נמצאת בטווח תנודתיות סביר" in response.text
    assert "פתיחת חשיפה רחבה לשוק האמריקאי" in response.text
    assert "הערה תפעולית בעברית" in response.text
    assert "Current drawdown is within normal volatility" not in response.text
    assert "Price obtained from external source" not in response.text
    assert "Initial broad US market exposure" not in response.text
    assert "English dashboard description" not in response.text
    assert "English disclaimer" not in response.text
    assert "English operational note" not in response.text


def test_dashboard_supports_provider_schema_1_1_display_fields(monkeypatch, valid_report_data):
    valid_report_data["schema_version"] = "1.1"
    valid_report_data["display"] = {
        "title_he": "דוח תיק מודל וירטואלי",
        "subtitle_he": "עדכון תיק מודל - 29.04.2026 בשעה 14:10 שעון ישראל",
        "dashboard_title_he": "דשבורד תיק מודל",
        "eyebrow_he": "תיק מודל וירטואלי",
        "disclaimer_he": "תיק מודל וירטואלי לצורכי לימוד ומעקב בלבד - לא ייעוץ השקעות.",
        "summary_title_he": "סיכום תיק",
        "holdings_title_he": "טבלת אחזקות",
        "transactions_title_he": "יומן פעולות היסטורי",
        "thesis_title_he": "בדיקת תזה",
        "recommendation_title_he": "המלצת היום",
        "actions_today_title_he": "פעולות היום",
        "market_data_title_he": "סטטוס מקור מחירים",
    }
    valid_report_data["market_data"]["price_mode_he"] = (
        "מחיר אחרון זמין או מחיר סגירה אחרון זמין"
    )
    valid_report_data["market_data"]["source_he"] = (
        "מקורות פיננסיים חיצוניים זמינים בזמן הפקת הדוח"
    )
    valid_report_data["market_data"]["notes_he"] = (
        "הדוח הופק לפני פתיחת המסחר הרגיל בארה\"ב."
    )
    valid_report_data["summary"]["starting_value_label_he"] = "שווי פתיחה"
    valid_report_data["summary"]["current_value_label_he"] = "שווי כולל נוכחי"
    valid_report_data["summary"]["cash_label_he"] = "מזומן פנוי"
    valid_report_data["summary"]["securities_value_label_he"] = "שווי ניירות ערך"
    valid_report_data["summary"]["total_pl_label_he"] = "רווח/הפסד כולל"
    valid_report_data["summary"]["total_pl_pct_label_he"] = "שינוי כולל"
    valid_report_data["summary"]["recommendation_he"] = "להחזיק - אין שינוי בתיק"
    valid_report_data["holdings"][0]["display_name_he"] = "SPY - קרן סל על מדד S&P 500"
    valid_report_data["holdings"][0]["role_he"] = "חשיפה רחבה לשוק המניות האמריקאי"
    valid_report_data["holdings"][0]["note_he"] = (
        "המחיר נלקח ממקור חיצוני כמחיר אחרון זמין."
    )
    valid_report_data["holdings"][0]["status_he"] = "החזק"
    valid_report_data["holdings"][0]["price_confidence_he"] = "מחיר אחרון זמין"
    valid_report_data["actions_today"] = []
    valid_report_data["actions_today_he"] = ["לא בוצעה פעולה וירטואלית חדשה."]
    valid_report_data["thesis_check"]["status_he"] = "אין שבירת תזה"
    valid_report_data["thesis_check"]["notes_he"] = [
        "לא זוהתה שבירת תזה באף אחת מהאחזקות."
    ]
    valid_report_data["recommendation"]["action_he"] = "החזק"
    valid_report_data["recommendation"]["reason_he"] = (
        "הירידה הנוכחית עדיין נמצאת בטווח תנודתיות סביר."
    )
    report = validate_report(valid_report_data)
    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(
            dashboard_access_token=None,
            google_doc_id="doc",
            google_application_credentials=None,
            cache_ttl_seconds=300,
        ),
    )
    monkeypatch.setattr(main, "load_report", lambda force=False: report)
    main.cache.clear()
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "דשבורד תיק מודל" in response.text
    assert "עדכון תיק מודל - 29.04.2026 בשעה 14:10 שעון ישראל" in response.text
    assert "סטטוס מקור מחירים" in response.text
    assert "מקורות פיננסיים חיצוניים זמינים בזמן הפקת הדוח" in response.text
    assert "שווי כולל נוכחי" in response.text
    assert "SPY - קרן סל על מדד S&amp;P 500" in response.text
    assert "חשיפה רחבה לשוק המניות האמריקאי" in response.text
    assert "לא בוצעה פעולה וירטואלית חדשה." in response.text
    assert "אין שבירת תזה" in response.text
