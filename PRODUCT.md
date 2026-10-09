# Product Description: Leaves

> Go touch some grass

## Vision
Leaves is a local-first, agentic personal scheduling assistant. It collects user-approved context from connected sources, understands tasks with a user-provided API key for a supported model provider (such as OpenAI, Anthropic Claude, or Google Gemini), and helps arrange the user's schedule. It is intended to connect to Gmail, Google Calendar, local Markdown, and other supported schedule-bearing apps.

## Product Experience
The first interface is a professional, minimal dashboard and search experience with a manga-inspired visual style and light and dark modes. Leaves acts in the background as an agent; the requested interface has no chat surface.

The agreed main screen combines a prominent search field with a compact view of the user's day and useful context surfaced from connected sources.

## Data and Control
- The user chooses what Leaves collects.
- Leaves' database, indexes, settings, and credentials stay on the user's device.
- To use a configured cloud model, Leaves sends task-relevant context (relevant email, calendar, or Markdown excerpts) to the configured provider for analysis, while Leaves' database and indexes stay on-device. For Gmail, model requests include only emails identified as relevant to a task, rather than sending the entire inbox.
- Provider API keys are supplied by the user. Store them in the operating system's secure credential store where available; never write keys to project files, logs, or the ordinary app database.
- The user can export or delete Leaves-held data. Deleting something from Leaves removes only Leaves' local copy and index, leaving the original email, file, or calendar event untouched. Exact export contents remain to be defined.
- No Leaves account/login is planned. The user is okay authenticating to connected providers while keeping collected data on-device.

## Integrations and Background Operation
Leaves is intended to connect to Gmail, Google Calendar, and other schedule-bearing apps the user chooses, extract relevant details, understand task urgency, and arrange tasks accordingly. It may add or move calendar events automatically while respecting availability, but deleting calendar events always requires user approval. Schedule rules (working hours, breaks, and default task duration) will be configurable and decided later. Leaves notifies the user about schedule updates. On macOS, it stays in the menu bar after the user opens it; automatic launch at sign-in is not planned.

## Recommended First Release
Start with a macOS desktop app, a dashboard and search view, user-selected local Markdown plus Gmail and Google Calendar as prioritized sources, local indexing/search with source references, and controls to manage collected sources. Gmail scans all mail by default, with an option to limit by label. The first release focuses strictly on understanding tasks and scheduling them; broader actions across connected apps are deferred. Support user-provided keys with one active provider/model chosen in settings at a time (no automatic routing). Keep Windows and Linux possible. Ollama may remain a later local-model option; chat is out of scope.

## Later Candidates
Additional schedule-bearing app integrations, expanded agent actions across connected apps, semantic/vector search, Ollama, and broader platform support. Integration permissions, export format, and detailed schedule rules/conflict logic need definition before implementation.
