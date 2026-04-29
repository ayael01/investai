from dataclasses import dataclass
from time import monotonic
from typing import Any


@dataclass
class CacheEntry:
    report: Any
    html: str | None
    expires_at: float


class ReportCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._entry: CacheEntry | None = None

    def get_report(self) -> Any | None:
        if not self._entry or self._entry.expires_at <= monotonic():
            return None
        return self._entry.report

    def get_html(self) -> str | None:
        if not self._entry or self._entry.expires_at <= monotonic():
            return None
        return self._entry.html

    def set(self, report: Any, html: str | None = None) -> None:
        self._entry = CacheEntry(
            report=report,
            html=html,
            expires_at=monotonic() + self.ttl_seconds,
        )

    def set_html(self, html: str) -> None:
        if self._entry and self._entry.expires_at > monotonic():
            self._entry.html = html

    def clear(self) -> None:
        self._entry = None

