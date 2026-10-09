# Local API Contract

## Process and trust boundary

The FastAPI service listens only on loopback. In development, `scripts/dev.sh`
supervises it on `127.0.0.1:8000`. Installed Tauri builds reserve an available
loopback port, launch the bundled `leaves-api` sidecar there, and provide the
port to the frontend through a Tauri command. The sidecar is terminated when
the app exits. Closing the window hides Leaves in the menu bar and intentionally
leaves the API running.

The API is a same-user local process and currently has no authentication token.
It must remain loopback-only; do not bind to `0.0.0.0`. The frontend allows only
the configured Vite and Tauri origins. App data is stored in Tauri's
application-data directory in packaged builds and `data/` in development, unless
`LEAVES_DATA_DIR` overrides it.

## Response and error conventions

JSON is used for requests and responses. Successful operations return the
resource or a small result object. Invalid input returns `400`, unknown local
IDs return `404`, no safe schedule slot returns `409`, and an unavailable OS
credential store returns `503`. Provider
authentication, permission, rate-limit, and transport errors should be surfaced
with a safe message and never include a credential value.

## Current operations

| Area | Operation | Contract |
| --- | --- | --- |
| Readiness | `GET /api/health` | `{status, service}` |
| Dashboard | `GET /api/dashboard` | Local counts, sources, recent documents, events, pending tasks, notifications |
| Markdown | `GET/POST /api/sources`, `POST /api/sources/{id}/refresh`, `DELETE /api/sources/{id}` | Selected local folder indexing; deletion removes only Leaves' copy |
| Search | `GET /api/search?q=&limit=` | FTS results with source references |
| Model settings | `GET/POST /api/settings/model`, `DELETE /api/settings/model/{provider}` | One active provider; keys live in OS credential manager |
| Availability | `GET/POST /api/settings/availability`, `/api/settings/time-away` | Working hours, break window, default duration, notification preference, and timezone-aware time-away blocks |
| Gmail | `POST /api/integrations/gmail/sync`, `GET /api/integrations/gmail/emails`, `DELETE /api/integrations/gmail/emails/{id}` | Read-only Google sync or explicit sample mode; deleting removes only the local copy |
| Google OAuth | `GET /api/auth/google/status`, `POST /api/auth/google/{gmail|calendar}/start`, `GET /api/auth/google/callback`, `DELETE /api/auth/google/{service}` | PKCE loopback flow; tokens stay in the OS credential store |
| Calendar | `GET /api/integrations/schedule-connectors`, `POST /api/integrations/calendar/sync`, event CRUD | Live Google sync/write when connected, otherwise sample mode; delete requires `confirmed=true` |
| Tasks | `POST /api/tasks/extract`, `GET /api/tasks`, `POST /api/tasks/{id}/schedule`, `PUT /api/tasks/{id}/status` | Local extraction, urgency rationale, schedule proposal and status |
| Conflict resolution | `POST /api/schedule/resolve-conflicts` | Moves only Leaves-created events; never deletes events |
| Notifications | `GET /api/notifications`, read operations | Local schedule update log |
| Export | `GET /api/export` | JSON export of Leaves-held records, including time-away blocks; excludes OS-stored credentials |

## Remaining provider API work

Google account sync requires a configured desktop OAuth client ID and the
scopes, PKCE flow, credential storage, and deletion controls in
[`INTEGRATIONS.md`](INTEGRATIONS.md). OAuth tokens must never be accepted in
ordinary API payloads or written to SQLite.
