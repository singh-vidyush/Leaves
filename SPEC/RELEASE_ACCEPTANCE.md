# MVP Release Acceptance

MVP acceptance is met when each item below passes on a clean macOS machine with
no developer-only Python or database data present. The app has no chat surface.

## Installation and lifecycle

- A signed/notarized macOS build opens from a fresh install and creates its data
  directory on first launch.
- Leaves starts exactly one bundled API process on `127.0.0.1:8000`; the UI
  reports ready only after `/api/health` and dashboard requests succeed.
- Closing the window hides the app in the menu bar. Choosing **Quit Leaves**
  stops the backend and leaves no child process behind.
- Relaunching uses the same local database and OS credential entries.

## Sources and privacy

- A user can select a Markdown folder, scan recursively or top-level only,
  refresh it, search its indexed content, and remove only Leaves' local copy.
- Gmail can connect with the approved read-only scope, sync all mail or a
  selected label, and update records without creating duplicates. Removing an
  email in Leaves never deletes it from Gmail.
- Google Calendar can connect with the approved owned-events scope, read
  commitments, and keep provider IDs/time zones mapped locally.
- Cloud extraction sends only task-relevant Markdown and email excerpts to the
  one selected model provider. Calendar event text remains local. The UI discloses
  this behavior; API keys and OAuth tokens are
  stored in the OS credential manager and are absent from SQLite, logs, and
  exports.
- Export contains the documented Leaves-held data. Credential values are not
  present in the export.

## Understanding and scheduling

- Extraction produces actionable tasks with source references, urgency scores,
  reasons, duration estimates, and explicit deadlines when present. A local
  heuristic provider works without a cloud key.
- Scheduling respects configured work hours, breaks, weekdays, explicit
  time-away blocks, event conflicts, and task duration; no generated event
  overlaps an existing commitment.
- Leaves may add and move only its own events. Every event deletion requires a
  visible confirmation, and declining leaves the event unchanged.
- Schedule changes create notifications that can be read and dismissed.

## Release phases

- **MVP:** macOS desktop, local Markdown, live Gmail and Google Calendar,
  selected model provider, local search, explainable extraction, availability
  scheduling, notifications, and data export.
- **Beta:** additional providers implementing `ScheduleConnector`, improved
  sync/retry and time-zone handling, and broader usability feedback.
- **v1.0:** evaluate Windows/Linux packaging and any new integrations against
  their OS credential stores, permissions, and lifecycle behavior.

The containerized evaluation demo is deferred and is not an MVP release gate.
Revisit it only if a stakeholder requests a hosted demonstration; user data and
credentials must not be placed in a shared demo environment.
