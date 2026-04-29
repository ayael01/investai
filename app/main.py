import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.core.config import Settings
from app.services.cache import ReportCache
from app.services.formatters import (
    calculate_allocation,
    display_list,
    display_text,
    format_date_il,
    format_datetime_il,
    format_ils,
    format_number,
    format_percent,
    format_price,
    format_usd,
    signed_class,
    status_class,
)
from app.services.google_docs import GoogleDocsReadError, fetch_google_doc_text
from app.services.report_extractor import (
    InvalidJsonError,
    MissingJsonBlockError,
    extract_machine_readable_json,
)
from app.services.report_validator import PortfolioReport, validate_report


logger = logging.getLogger(__name__)

settings = Settings()
cache = ReportCache(ttl_seconds=settings.cache_ttl_seconds)

app = FastAPI(title="Hebrew Portfolio Dashboard")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["ils"] = format_ils
templates.env.filters["usd"] = format_usd
templates.env.filters["number"] = format_number
templates.env.filters["percent"] = format_percent
templates.env.filters["price"] = format_price
templates.env.filters["datetime_il"] = format_datetime_il
templates.env.filters["date_il"] = format_date_il
templates.env.filters["display_text"] = display_text
templates.env.filters["signed_class"] = signed_class
templates.env.filters["status_class"] = status_class
templates.env.globals["display_list"] = display_list


def require_access_token(request: Request) -> None:
    if not settings.dashboard_access_token:
        return
    if request.query_params.get("token") != settings.dashboard_access_token:
        raise HTTPException(status_code=403, detail="Forbidden")


def build_allocations(report: PortfolioReport) -> list[dict[str, Any]]:
    total = report.summary.current_value_ils
    return [
        {
            "ticker": holding.ticker,
            "name": display_text(holding, "display_name")
            or display_text(holding, "name")
            or holding.ticker,
            "value_ils": holding.current_value_ils,
            "percent": calculate_allocation(holding.current_value_ils, total),
            "status": holding.status,
        }
        for holding in report.holdings
    ]


def build_ui_text(report: PortfolioReport) -> dict[str, Any]:
    display = getattr(report, "display", None)
    summary = report.summary
    thesis_check = report.thesis_check
    recommendation = report.recommendation
    market_data = report.market_data

    actions_today = display_list(report, "actions_today")

    return {
        "title": display_text(display, "title")
        or display_text(report, "title", "דוח תיק מודל וירטואלי"),
        "dashboard_title": display_text(display, "dashboard_title")
        or display_text(report, "title", "דשבורד תיק מודל"),
        "subtitle": display_text(display, "subtitle")
        or display_text(report, "subtitle", "תיק מודל וירטואלי"),
        "eyebrow": display_text(display, "eyebrow")
        or display_text(report, "subtitle", "תיק מודל וירטואלי"),
        "description": display_text(display, "description")
        or display_text(
            report,
            "description",
            "תצוגת דשבורד לתיק המודל: שווי כולל, רווח/הפסד, איכות נתוני שוק, חלוקת אחזקות, בדיקת תזה ויומן פעולות.",
        ),
        "disclaimer": display_text(display, "disclaimer")
        or display_text(
            report,
            "disclaimer",
            "זהו תיק מודל וירטואלי לצורכי לימוד ומעקב בלבד. אין לראות בדוח זה ייעוץ השקעות או הוראת קנייה/מכירה.",
        ),
        "summary_title": display_text(display, "summary_title", "סיכום תיק"),
        "holdings_title": display_text(display, "holdings_title", "טבלת אחזקות"),
        "transactions_title": display_text(
            display, "transactions_title", "יומן פעולות היסטורי"
        ),
        "thesis_title": display_text(display, "thesis_title", "בדיקת תזה"),
        "recommendation_title": display_text(
            display, "recommendation_title", "המלצת היום"
        ),
        "actions_today_title": display_text(
            display, "actions_today_title", "פעולות היום"
        ),
        "market_data_title": display_text(
            display, "market_data_title", "סטטוס מקור מחירים"
        ),
        "starting_value_label": display_text(
            summary, "starting_value_label", "שווי פתיחה"
        ),
        "current_value_label": display_text(
            summary, "current_value_label", "שווי כולל נוכחי"
        ),
        "cash_label": display_text(summary, "cash_label", "מזומן פנוי"),
        "securities_value_label": display_text(
            summary, "securities_value_label", "שווי ניירות ערך"
        ),
        "total_pl_label": display_text(summary, "total_pl_label", "רווח/הפסד כולל"),
        "total_pl_pct_label": display_text(summary, "total_pl_pct_label", "שינוי כולל"),
        "summary_recommendation": display_text(summary, "recommendation")
        or display_text(recommendation, "recommendation")
        or display_text(recommendation, "action"),
        "recommendation_action": display_text(recommendation, "recommendation")
        or display_text(recommendation, "action"),
        "recommendation_reason": display_text(recommendation, "reason"),
        "market_price_mode": display_text(market_data, "price_mode"),
        "market_source": display_text(market_data, "source"),
        "market_notes": display_text(market_data, "notes"),
        "thesis_status": display_text(thesis_check, "status")
        or ("תזה נשברה" if thesis_check.broken_thesis else "אין שבירת תזה"),
        "thesis_notes": display_list(thesis_check, "notes"),
        "actions_today": actions_today,
    }


def load_report(force: bool = False) -> PortfolioReport:
    if not force:
        cached_report = cache.get_report()
        if cached_report is not None:
            return cached_report

    text = fetch_google_doc_text(
        settings.google_doc_id,
        settings.google_application_credentials,
        settings.google_application_credentials_json_base64,
    )
    data = extract_machine_readable_json(text)
    report = validate_report(data)
    cache.set(report=report, html=None)
    return report


def render_dashboard(request: Request, report: PortfolioReport) -> str:
    response = templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "report": report,
            "allocations": build_allocations(report),
            "ui": build_ui_text(report),
        },
    )
    return response.body.decode("utf-8")


def render_error(
    request: Request,
    title: str,
    message: str,
    details: list[str] | None = None,
    status_code: int = 500,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "title": title,
            "message": message,
            "details": details or [],
        },
        status_code=status_code,
    )


def google_docs_error_details(exc: GoogleDocsReadError) -> list[str]:
    message = str(exc)
    if "credentials are not configured" in message:
        return [
            "לא הוגדרו פרטי התחברות לחשבון השירות של Google.",
            "בסביבה מקומית יש להגדיר GOOGLE_APPLICATION_CREDENTIALS לקובץ JSON.",
            "בסביבת Render יש להגדיר GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64.",
        ]
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64" in message:
        return [
            "משתנה GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64 אינו תקין.",
            "יש לוודא שהוא מכיל קובץ service account JSON לאחר קידוד base64.",
        ]
    if "GOOGLE_APPLICATION_CREDENTIALS" in message:
        if "file does not exist" in message:
            return [
                "הנתיב שמוגדר ב-GOOGLE_APPLICATION_CREDENTIALS אינו מצביע לקובץ קיים.",
                "יש להחליף את /absolute/path/to/service-account.json בנתיב המלא לקובץ ה-JSON האמיתי של חשבון השירות.",
                "יש לשתף את Google Doc עם כתובת האימייל של חשבון השירות בהרשאת צפייה.",
            ]
        return [
            "משתנה הסביבה GOOGLE_APPLICATION_CREDENTIALS לא מוגדר.",
            "יש ליצור קובץ .env ולהפנות אותו לקובץ ה-JSON של חשבון השירות.",
            "יש לשתף את Google Doc עם כתובת האימייל של חשבון השירות בהרשאת צפייה.",
        ]
    return []


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    require_access_token(request)

    cached_html = cache.get_html()
    if cached_html is not None:
        return HTMLResponse(cached_html)

    try:
        report = load_report()
        html = render_dashboard(request, report)
        cache.set_html(html)
        return HTMLResponse(html)
    except GoogleDocsReadError as exc:
        logger.exception("Failed to read Google Doc.")
        return render_error(
            request,
            "שגיאת קריאה",
            "לא ניתן לקרוא את Google Doc כרגע.",
            google_docs_error_details(exc),
        )
    except MissingJsonBlockError:
        return render_error(
            request,
            "בלוק JSON חסר",
            "לא נמצא בלוק JSON מובנה במסמך.",
        )
    except InvalidJsonError:
        return render_error(
            request,
            "JSON לא תקין",
            "בלוק ה-JSON אינו תקין.",
        )
    except ValidationError as exc:
        return render_error(
            request,
            "מבנה נתונים לא תקין",
            "מבנה ה-JSON אינו תואם לסכמה הנדרשת.",
            [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()],
        )


@app.get("/api/report")
def api_report(request: Request) -> dict[str, Any]:
    require_access_token(request)
    report = load_report()
    return report.model_dump(mode="json")


@app.get("/refresh", response_class=HTMLResponse)
def refresh(request: Request) -> HTMLResponse:
    require_access_token(request)
    cache.clear()
    try:
        report = load_report(force=True)
        html = render_dashboard(request, report)
        cache.set(report=report, html=html)
        return HTMLResponse(html)
    except GoogleDocsReadError as exc:
        logger.exception("Failed to read Google Doc.")
        return render_error(
            request,
            "שגיאת קריאה",
            "לא ניתן לקרוא את Google Doc כרגע.",
            google_docs_error_details(exc),
        )
    except MissingJsonBlockError:
        return render_error(
            request,
            "בלוק JSON חסר",
            "לא נמצא בלוק JSON מובנה במסמך.",
        )
    except InvalidJsonError:
        return render_error(
            request,
            "JSON לא תקין",
            "בלוק ה-JSON אינו תקין.",
        )
    except ValidationError as exc:
        return render_error(
            request,
            "מבנה נתונים לא תקין",
            "מבנה ה-JSON אינו תואם לסכמה הנדרשת.",
            [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()],
        )
