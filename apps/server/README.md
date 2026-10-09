# Local Backend

The FastAPI service handles local Markdown indexing and search, task extraction,
calendar scheduling, and Google account integrations. Start it for development
with:

```sh
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Gmail and Google Calendar support live account connections with sample data
available for preview. Configure `GOOGLE_OAUTH_CLIENT_ID` before account
authorization.
