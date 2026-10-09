# High-Level Architecture

## System Design Overview
Leaves is a local-first desktop agent. macOS is the first target, with Windows and Linux kept possible. It collects user-approved context, keeps its database and credentials on-device, and can send task-relevant context to the model provider selected by the user for reasoning. The requested user experience is a dashboard and search view; chat is out of scope.

### Recommended Component Flow
`Dashboard + Search UI` <--> `Tauri shell (Rust)` <--> `FastAPI local backend` <--> `SQLite + FTS5`
                                                                  ^
                                                                  |
                                                    `Source integrations`
                                          (Markdown, Gmail, Google Calendar)
                                                                  |
                                                                  v
                                                   `Model provider adapters`
                                          (user key: OpenAI, Anthropic, Gemini, etc.)

## Components

### Desktop Shell and UI
- **Tauri 2** owns desktop lifecycle. Development uses `scripts/dev.sh`; installed builds bundle the Python API as a PyInstaller sidecar, launch it on loopback, and stop it when Leaves exits. The app's application-data directory contains the SQLite database.
- **React/TypeScript** is the frontend stack in the current scaffold. The owner prefers a professional, minimal UI with manga-inspired details and light and dark modes. The main screen combines search with a daily dashboard.
- Leaves should stay available in the macOS menu bar after the user opens it; it does not need to launch at sign-in. It should notify the user about schedule updates.
- No Leaves account/login is planned. The user authenticates to connected providers and supplies their own model API key.

### Local Backend and Storage
- **FastAPI** handles source ingestion, indexing, search, and urgency-aware scheduling logic in a local Python process. It binds only to `127.0.0.1:8000`.
- **SQLite with FTS5** is the recommended first-release store for source metadata and indexed text. FTS5 is SQLite's built-in full-text search module. Start without a vector extension; add local vector search only if prioritized. [SQLite FTS5 documentation](https://www.sqlite.org/fts5.html)
- The API contract and current endpoints are documented in `SPEC/API_CONTRACT.md`. It is a same-user loopback service; it must never bind to a public interface.

### Integrations and Scheduling
- Prioritized sources are local Markdown, Gmail, and Google Calendar. Schedule providers implement `ScheduleConnector`; Google Calendar is live when connected and falls back to labeled local sample data otherwise. Google OAuth uses PKCE and OS credential storage.
- The app should run in the background, extract schedule-relevant details, assess task urgency, and arrange tasks. Automatic event additions and moves in Google Calendar are authorized, but deleting calendar events always requires user approval. Scheduling respects configurable working hours, breaks, time-away blocks, task duration, and existing commitments.
- Gmail should be scanned in full by default, with a user option to restrict collection by label.
- Leaves-held database, indexes, settings, and credentials remain on-device. Model requests send only task-relevant Markdown and email excerpts to the configured provider; calendar event text stays local and only event times constrain scheduling. For Gmail, requests include only emails identified as relevant to a task, not the entire inbox. When data is deleted from Leaves, only Leaves' local copy and index are removed, leaving original emails, files, and calendar events untouched.
- Use the operating system's secure credential store for provider keys and integration tokens where supported. The backend uses Python `keyring` and fails closed if no secure backend is available. Never log secrets or place them in SQLite. Integration scopes and lifecycle are specified in `SPEC/INTEGRATIONS.md`.

### Agent and Model Providers
- Leaves is an agentic application: for the first release, it focuses strictly on understanding tasks and scheduling them (broader actions across connected apps are deferred). The UI remains dashboard/search without chat.
- Provide a provider adapter boundary for user-supplied API keys (initial candidates: OpenAI, Anthropic Claude, and Google Gemini). The user selects one active provider/model at a time in settings; do not route automatically across providers.
- Keep scheduling policy and permissions in Leaves, not in the model. Treat model output as proposed structured actions, validate availability and constraints locally, and record action/source provenance before writing calendar changes (automatic additions and moves are authorized, but deleting calendar events always requires user approval).
- Ollama is a possible later local-model provider. It is not required for the first cloud-provider workflow.

## Deployment
- **Desktop product**: Tauri shell, platform-built Python sidecar, and on-device storage. macOS first; the sidecar must be built on the target OS/architecture.
- **Evaluation demo**: deferred and not an MVP release gate. See `SPEC/RELEASE_ACCEPTANCE.md`.
