import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    google_doc_id: str = os.getenv(
        "GOOGLE_DOC_ID",
        "1evbfnd7Pe_9MWXA6px54LdAXceJGawCswGyXqaPxvxE",
    )
    google_application_credentials: str | None = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )
    google_application_credentials_json_base64: str | None = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64"
    )
    dashboard_access_token: str | None = os.getenv("DASHBOARD_ACCESS_TOKEN") or None
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
