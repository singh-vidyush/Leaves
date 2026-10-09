# Integrations Specification

## Connector contract

Schedule-bearing providers implement `ScheduleConnector` in
`apps/server/app/integrations/connectors.py`. A connector has a stable `id` and
display name, and exposes `sync`, `list_events`, `add_event`, `move_event`, and
`delete_event`. New implementations are registered in `get_schedule_connectors`.
The API returns each connector's capabilities at
`GET /api/integrations/schedule-connectors`.

Connectors normalize event IDs, titles, descriptions, and ISO 8601 start/end
times into Leaves' calendar event model. `created_by` distinguishes external
commitments from Leaves-created events. Provider errors should retain whether
they were authentication, permission, throttling, or transient failures.

`LocalCalendarConnector` is the registered schedule connector. It reports
whether Google Calendar is connected and syncs live data when authorized;
without a connection, it loads deterministic sample commitments. Sync responses
include `mode: live` or `mode: sample`. Sample fixtures must never be reported
as a live sync.

## Google account permissions

Google OAuth uses an installed-app client with PKCE and a loopback redirect. The
client ID is configured as `GOOGLE_OAUTH_CLIENT_ID`; no client secret is
embedded in the desktop application.

- Gmail: request only `https://www.googleapis.com/auth/gmail.readonly`. This is
  enough to list and fetch messages and labels for local indexing. Leaves does
  not send mail, modify labels, or delete provider messages.
- Google Calendar: request only
  `https://www.googleapis.com/auth/calendar.events.owned` for the first release.
  This limits access to calendars the user owns while allowing read, create, and
  move operations there. If the user needs shared calendars, request the broader
  `calendar.events` scope only after explaining the tradeoff.
- Deleting an event requires an explicit in-app confirmation every time. OAuth
  scopes cannot distinguish deletion from edits, so this remains an application
  policy enforced by the API and UI. Deleting a record from Leaves removes only
  the local copy.

OAuth access and refresh tokens and model-provider API keys belong in the
operating-system credential manager (macOS Keychain, Windows Credential Manager,
or Linux Secret Service). The Python `keyring` adapter must fail closed when no
secure backend is available; do not fall back to plaintext files or SQLite.
Tokens are never included in exports, logs, or model prompts. The previous
prototype `.credentials.json` file is migrated into the OS store on first access
and removed only after the migration succeeds.

## Collection and model context

- Local Markdown collection is explicit: users select folders, choose recursive
  scanning, and can refresh or remove Leaves' index without touching source
  files.
- Gmail sync reads all mail by default, with an optional label filter. Email
  deletion in Leaves affects only the local copy. Before sending context to a
  model, identify task-relevant emails and send only their relevant excerpts.
- Calendar event titles and descriptions stay local and are not included in model
  prompts. Leaves uses time intervals locally to validate schedule proposals.
- A user chooses one active model provider. If no key is configured, local
  heuristic extraction remains available.
- The app must disclose which excerpt types are sent before enabling cloud
  extraction. Original email, calendar, and Markdown content stays on device.

## Sync and scheduling rules

- Sync is additive/update-by-provider-ID and safe to repeat. Record provider IDs
  locally so a second sync updates rather than duplicates entries.
- Adds and moves created by Leaves are permitted by the product policy. Do not
  delete external events automatically. Conflicts may move only a Leaves-created
  event; if no safe slot exists, surface the conflict instead of moving an
  external commitment.
- Use each provider's timezone-aware timestamps and preserve the source timezone.
- With no connected account the API explicitly reports sample mode. A connected
  account with a missing scope or provider failure returns an actionable error;
  it must not be reported as a successful live sync.
- Tests use deterministic fixtures and a fake credential store; live provider
  tests require an explicit developer-owned test account and are not part of the
  default suite.
