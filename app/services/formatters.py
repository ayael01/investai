from datetime import date, datetime
from zoneinfo import ZoneInfo


def _read_field(obj: object, field: str) -> object:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(field)
    return getattr(obj, field, None)


def display_text(obj: object, field: str, default: str = "") -> str:
    hebrew_value = _read_field(obj, f"{field}_he")
    if hebrew_value is not None:
        return str(hebrew_value)

    value = _read_field(obj, field)
    if value is not None:
        return str(value)

    return default


def display_list(obj: object, field: str) -> list[object]:
    hebrew_value = _read_field(obj, f"{field}_he")
    if isinstance(hebrew_value, list):
        return hebrew_value

    value = _read_field(obj, field)
    if isinstance(value, list):
        return value

    return []


def format_ils(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f'{value:,.0f} ש"ח'


def format_usd(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"${value:,.2f}"


def format_number(value: float | int | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.2f}"
    return f"{value:,.0f}"


def format_percent(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:+.2f}%"


def format_price(value: float | int | None, currency: str | None) -> str:
    if value is None:
        return "-"
    if currency == "USD":
        return format_usd(value)
    if currency == "ILS":
        return format_ils(value)
    return format_number(value)


def format_datetime_il(value: datetime | str | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    local_value = value.astimezone(ZoneInfo("Asia/Jerusalem"))
    return local_value.strftime("%d.%m.%Y | %H:%M")


def format_date_il(value: date | str | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value.strftime("%d.%m.%Y")


def signed_class(value: float | int | None) -> str:
    if value is None or value == 0:
        return "neutral"
    return "positive" if value > 0 else "negative"


def status_class(value: str | None) -> str:
    if value == "HOLD_WATCH":
        return "warning"
    if value == "AVAILABLE":
        return "cash"
    if value == "HOLD":
        return "positive"
    if value == "BUY":
        return "cash"
    return "neutral"


def calculate_allocation(value: float | int | None, total: float | int | None) -> float:
    if not value or not total or total <= 0:
        return 0.0
    return round((float(value) / float(total)) * 100, 2)
