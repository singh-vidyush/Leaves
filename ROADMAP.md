# Roadmap

No calendar dates are committed. Release gates are defined in
[`SPEC/RELEASE_ACCEPTANCE.md`](SPEC/RELEASE_ACCEPTANCE.md).

## MVP — macOS

- Tauri menu-bar desktop app with dashboard, search, light/dark themes, and
  supervised local backend.
- Explicitly selected local Markdown folders, refresh/removal controls, and
  local full-text search.
- Live read-only Gmail ingestion and Google Calendar read/create/move support,
  using the least-privilege scopes in `SPEC/INTEGRATIONS.md`.
- One user-selected model provider, local heuristic fallback, explainable task
  extraction, and task-relevant context disclosure.
- Configurable availability, conflict-aware scheduling, notifications, export,
  and explicit confirmation for every calendar deletion.

The current implementation supports PKCE Google OAuth, read-only Gmail, and
Google Calendar sync and writes. A configured OAuth client ID and provider
account verification remain release prerequisites.

## Beta

- Add another schedule-bearing provider through `ScheduleConnector` only after
  documenting its scopes, sync behavior, local data retention, and write rules.
- Improve synchronization retry, time-zone behavior, and user-facing connection
  recovery.
- Run focused usability and reliability feedback with opt-in test accounts.

## v1.0

- Evaluate Windows and Linux packaging, credential-manager support, and process
  supervision.
- Reassess additional integrations and local-model support.

The containerized evaluation demo is deferred and is not an MVP release gate.
