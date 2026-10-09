# TODO

## Foundation
- [x] Create the Tauri menu-bar shell; closing the window hides Leaves.
- [x] Build the dashboard and search UI with light/dark themes.
- [x] Add the local FastAPI service and SQLite/FTS5 store.
- [x] Add selected-folder Markdown indexing, recursive scan toggle, search, refresh, and index removal.
- [x] Bundle the API as a platform-specific Tauri sidecar; select a free loopback port, start it for packaged builds, and stop it on app exit.
- [ ] Verify the packaged Tauri lifecycle on macOS before release.
- [x] Add macOS DMG build and GitHub Release automation.
- [ ] Configure Apple signing/notarization secrets and publish the first signed installer.
- [x] Export Leaves-held data without exporting credentials.
- [x] Store model-provider credentials in the OS credential manager and define fail-closed behavior.

## Prioritized Product Work
- [x] Implement local sample Gmail ingestion and FTS indexing. This is a prototype, not a live Gmail connection.
- [x] Implement a local calendar prototype and the reusable `ScheduleConnector` contract.
- [x] Implement PKCE-based Google OAuth, OS-keychain token storage, and Gmail read-only sync.
- [ ] Register a Google Desktop OAuth client, configure its consent screen and `GOOGLE_OAUTH_CLIENT_ID`, then run an account-level smoke test.
- [x] Implement live Google Calendar sync/add/move using the approved owned-events scope.
- [x] Add heuristic and model-provider task extraction with explainable urgency.
- [x] Keep calendar event text local; use event times only for schedule validation. Model extraction receives only relevant Markdown and email excerpts.
- [x] Add working hours and break settings; enforce workdays, breaks, and existing local events when finding a slot.
- [x] Add configurable time-away blocks and make the notification preference control schedule notifications.
- [x] Apply task scheduling and conflict moves to the connected Google Calendar; event deletion requires user confirmation.
- [x] Require explicit user confirmation before calendar-event deletion.
- [x] Add schedule notifications and a notification log.
- [x] Define and register schedule-bearing integrations through `ScheduleConnector`, with a local reference connector.

## Product Decisions
- [x] Specify minimum Google scopes: Gmail `gmail.readonly`; Calendar `calendar.events.owned`, with broader shared-calendar scope requiring a separate decision.
- [x] Specify credential storage: OS credential manager (Keychain, Credential Manager, or Secret Service); no plaintext fallback. Legacy prototype keys migrate on first access.
- [x] Define MVP acceptance criteria and MVP/Beta/v1.0 phases in `SPEC/RELEASE_ACCEPTANCE.md`.
- [x] Defer the containerized evaluation demo; it is not an MVP release gate.
- [x] Defer another live schedule provider until a provider and its scopes/sync policy are selected.
- [x] Define export contents and ensure exports exclude credentials.

<!-- Keep checked items tied to implemented behavior; provider registration and target-platform release checks may remain prerequisites. -->
