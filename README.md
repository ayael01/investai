# Hebrew Portfolio Dashboard

Small FastAPI application that reads a Google Doc, extracts only the machine-readable JSON block, validates it with Pydantic, and renders a Hebrew RTL broker-style portfolio dashboard.

The app never parses the free-text Hebrew report. The JSON block between these markers is the only source of truth:

```text
--- MACHINE_READABLE_JSON_START ---
{ ... }
--- MACHINE_READABLE_JSON_END ---
```

## Display Text Contract

The JSON schema can keep technical fields in English, but user-facing dashboard text should be supplied by Hebrew display fields ending in `_he`.

Examples:

```json
{
  "title": "Portfolio Model Dashboard",
  "title_he": "דשבורד תיק מודל",
  "recommendation": {
    "action": "HOLD",
    "action_he": "החזק",
    "reason": "Current drawdown is within normal volatility.",
    "reason_he": "הירידה הנוכחית עדיין נמצאת בטווח תנודתיות סביר."
  }
}
```

The HTML renderer prefers Hebrew fields such as `title_he`, `subtitle_he`, `display_name_he`, `status_he`, `note_he`, `reason_he`, `action_he`, `recommendation_he`, `thesis_check.notes_he`, `market_data.notes_he`, and `operational_status.notes_he`. If a Hebrew field is missing, it falls back to the technical field.

## Setup

1. Create a Google Cloud project.
2. Enable Google Docs API.
3. Create a service account.
4. Download the service-account JSON file.
5. Share the Google Doc with the service-account email as Viewer.
6. Create `.env` from `.env.example`.
7. Install dependencies:

```bash
pip install -r requirements.txt
```

8. Run locally:

```bash
uvicorn app.main:app --reload
```

9. Open:

```text
http://localhost:8000/?token=...
```

10. Refresh:

```text
http://localhost:8000/refresh?token=...
```

11. API:

```text
http://localhost:8000/api/report?token=...
```

If `DASHBOARD_ACCESS_TOKEN` is unset, `/`, `/api/report`, and `/refresh` are public. `/healthz` is always public.

## Tests

```bash
pytest
```

## Security Notes

Do not commit Google service-account credentials. Keep `GOOGLE_APPLICATION_CREDENTIALS` pointed at a local JSON file or a secret-managed runtime path.

## Render Deployment

Use Render when you want a public URL that works while your laptop is closed.

1. Push the project to GitHub.
2. In Render, create a new Web Service from the GitHub repository.
3. Use Python as the runtime.
4. Build command:

```bash
pip install -r requirements.txt
```

5. Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Add environment variables:

```env
GOOGLE_DOC_ID=1evbfnd7Pe_9MWXA6px54LdAXceJGawCswGyXqaPxvxE
GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64=<base64 encoded service-account JSON>
DASHBOARD_ACCESS_TOKEN=<choose a long random token>
CACHE_TTL_SECONDS=300
```

To create the base64 value locally:

```bash
base64 -i /path/to/service-account.json
```

Copy the single output string into Render as `GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64`. Do not commit the JSON file or the base64 value.
