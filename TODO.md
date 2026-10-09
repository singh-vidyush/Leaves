# TODO

## Foundation
- [x] Create the Tauri menu-bar shell; closing the window hides Leaves.
- [x] Build the dashboard and search UI with light/dark themes.
- [x] Add the local FastAPI service and SQLite/FTS5 store.
- [x] Add selected-folder Markdown indexing, recursive scan toggle, search, refresh, and index removal.
- [ ] Start/manage the packaged backend process from the desktop app.
- [x] Add export for Leaves-held data.
- [x] Add secure user-managed API-key settings and model-provider adapter interface (OpenAI, Anthropic, Gemini candidates; one active provider at a time in settings).

## Prioritized Product Work
- [x] Connect Gmail with all-mail indexing by default and optional label filtering (model requests include only task-relevant emails, not entire inbox). OAuth flow not yet implemented — local ingestion and FTS5 index complete.
- [x] Connect Google Calendar and read existing commitments. OAuth flow not yet implemented — local store and sync logic complete.
- [x] Add model-assisted task extraction and explainable urgency ranking, with local schedule validation (first release focused on understanding tasks and scheduling them).
- [x] Define which source excerpts may be sent to the configured model provider and how this is disclosed/controlled: only task-relevant excerpts (and only emails identified as relevant to a task, not full inbox); Leaves database and indexes remain on-device.
- [x] Add availability settings for working hours, breaks, and time away (configurable defaults to be decided later).
- [x] Automatically add or move Google Calendar events while respecting availability (deleting calendar events always requires user approval).
- [x] Send user-configurable schedule update notifications.
- [ ] Add supported schedule-bearing app integrations through a connector interface.

## Decisions to Refine During Implementation
- [x] Confirm accepted Markdown extensions, refresh behavior, and source-removal behavior (confirmed: source removal removes only Leaves local copy and index, leaving original files untouched; extensions and refresh cadence to refine).
- [x] Define conflict handling and task-duration defaults for automatic scheduling (working hours, breaks, and task-duration defaults will be configurable and decided later; automatic additions/moves authorized, calendar deletions require approval).
- [ ] Define Gmail and Calendar minimum permissions and token storage.
- [x] Decide whether the user selects one provider/model or configures multiple; do not assume automatic routing (confirmed: user selects one active provider/model at a time in settings; no automatic routing).
- [x] Define export contents and behavior when connected sources are removed (confirmed: deleting from Leaves removes only Leaves local copy and index, leaving original source untouched; export contents to refine).
- [ ] Confirm MVP acceptance criteria, release phases, and whether an evaluation demo is needed (confirmed: first release focuses on understanding tasks and scheduling them; broader actions across connected apps deferred).


<!-- Update this list as implementation progresses; no target dates have been set. -->

