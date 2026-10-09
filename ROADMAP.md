# Roadmap

<!-- Proposed sequencing from the current discussion. No dates or commitments are
set. The scheduling rules and integration permissions still need definition. -->

## MVP — Recommended First Release
- macOS desktop app with a professional, minimal dashboard and search, manga-inspired details, and light/dark modes.
- Background operation from the macOS menu bar with schedule notifications.
- User-selected local Markdown, Gmail, and Google Calendar as the prioritized sources.
- BYOK model-provider adapter for task understanding (one active provider/model in settings: OpenAI, Claude, Gemini candidates), sending only task-relevant excerpts (only task-relevant emails, not entire inbox).
- Local indexing/search with source references and user controls for collected data (deleting from Leaves removes only local copy/index, leaving originals untouched).
- Urgency-aware scheduling with automatic Google Calendar additions/moves that respect user availability (deleting calendar events requires user approval; scope focused on task understanding and scheduling).
- SQLite with FTS5. No chat; defer Ollama as an optional local provider.

## Beta — Candidate Scope
<!-- Add other schedule-bearing app integrations after defining their permissions,
sync, local data handling, and schedule-writing behavior. -->

## v1.0 — Candidate Scope
<!-- Consider broader integration coverage and Windows/Linux support. Define scope
and dates with the owner. -->

<!-- Owner decisions established: first release focuses on understanding tasks and scheduling (broader actions deferred); single active provider; task-relevant excerpts only (task-relevant emails only); calendar deletions require approval; data removal leaves originals intact. Configurable working hours, breaks, and task duration defaults to be decided later. -->
