import os
from typing import Any


class GoogleDocsReadError(RuntimeError):
    pass


def _extract_text_from_structural_elements(elements: list[dict[str, Any]]) -> list[str]:
    parts: list[str] = []
    for element in elements:
        paragraph = element.get("paragraph")
        if paragraph:
            paragraph_parts: list[str] = []
            for item in paragraph.get("elements", []):
                content = item.get("textRun", {}).get("content")
                if content:
                    paragraph_parts.append(content)
            if paragraph_parts:
                parts.append("".join(paragraph_parts))

        table = element.get("table")
        if table:
            for row in table.get("tableRows", []):
                for cell in row.get("tableCells", []):
                    parts.extend(_extract_text_from_structural_elements(cell.get("content", [])))

        section_break = element.get("sectionBreak")
        if section_break:
            parts.append("\n")
    return parts


def fetch_google_doc_text(document_id: str, credentials_path: str | None = None) -> str:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials_file = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_file:
            raise GoogleDocsReadError("GOOGLE_APPLICATION_CREDENTIALS is not configured.")
        if not os.path.isfile(credentials_file):
            raise GoogleDocsReadError(
                f"GOOGLE_APPLICATION_CREDENTIALS file does not exist: {credentials_file}"
            )

        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/documents.readonly"],
        )
    except Exception as exc:
        if isinstance(exc, GoogleDocsReadError):
            raise
        raise GoogleDocsReadError("Failed to initialize Google Docs client.") from exc

    try:
        service = build("docs", "v1", credentials=credentials, cache_discovery=False)
        document = service.documents().get(documentId=document_id).execute()
        content = document.get("body", {}).get("content", [])
        return "".join(_extract_text_from_structural_elements(content))
    except Exception as exc:
        raise GoogleDocsReadError("Failed to read Google Doc.") from exc
