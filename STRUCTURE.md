# Repository Structure

This is the current repository layout. Some integrations and schedule behavior remain documentation-only; the dashboard/search UI and local Markdown indexing foundation have been started.

```text
leaves/
├── apps/
│   ├── desktop/
│   │   ├── README.md               # Dashboard/search frontend direction
│   │   ├── package.json            # React, Vite, Tauri, and dialog plugin
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── main.tsx
│   │   │   ├── App.tsx              # Dashboard, search, and source management
│   │   │   ├── api.ts               # Local FastAPI client
│   │   │   ├── styles.css           # Light/dark UI styles
│   │   │   └── vite-env.d.ts
│   │   ├── pnpm-lock.yaml
│   │   └── src-tauri/
│   │       ├── README.md           # Tauri shell notes
│   │       ├── Cargo.toml
│   │       ├── tauri.conf.json
│   │       └── src/
│   │           ├── lib.rs           # Menu-bar tray and window lifecycle
│   │           └── main.rs
│   └── server/
│       ├── README.md               # Local backend scope
│       ├── pyproject.toml
│       └── app/
│           ├── README.md
│           ├── main.py              # Local FastAPI endpoints
│           ├── core/
│           │   ├── config.py
│           │   └── database.py
│           ├── services/
│           │   ├── indexing.py
│           │   └── search.py
│           ├── api/README.md        # Future route modules
│           ├── models/README.md     # Future persistence models
│           ├── adapters/README.md   # BYOK model adapters; Ollama later
│           └── integrations/
│               ├── README.md
│               ├── markdown/README.md
│               ├── gmail/README.md
│               └── google_calendar/README.md
├── data/README.md                  # Local runtime data; ignored by Git
├── scripts/README.md               # Project automation scripts
├── scripts/dev.sh                  # Starts API and Tauri development app
├── README.md
├── SPEC/                           # Technical specifications
├── GUIDES/                         # Development and deployment guides
├── ARCHITECTURE.md
├── DOCS.md
├── PRODUCT.md
├── ROADMAP.md
├── SETUP.md                        # Codex/Antigravity workflow
├── STRUCTURE.md
├── TODO.md
└── .gitignore
```

## Current Decisions
- macOS is the first target; keep Windows and Linux possible.
- Prioritized sources are user-selected local Markdown, Gmail, and Google Calendar.
- Recommended first-release persistence is SQLite with FTS5 for indexed text and search.
- Recommended desktop/backend boundary is a Tauri-managed FastAPI process with a local REST API.
- The frontend dashboard/search and macOS tray shell are started.
- Recursive Markdown indexing is on by default, with a UI toggle to scan only the chosen folder's top level.
- The user authorized automatic calendar additions and moves, subject to availability; deleting calendar events always requires user approval. Schedule rules (working hours, breaks, default durations) will be configurable and decided later.
- Leaves-held database, indexes, and credentials stay local; user-keyed model requests send only task-relevant excerpts (for Gmail, only emails identified as relevant to a task, not the entire inbox).
- The user selects one active provider/model at a time in settings; do not route automatically across providers.
- First release focuses strictly on understanding tasks and scheduling them; broader actions across connected apps are deferred.
- Deleting something from Leaves removes only Leaves' local copy and index, leaving the original email, file, or calendar event untouched.

## Not Yet Implemented
Gmail and Google Calendar support live OAuth/API integrations, with local samples available before account connection. The current model-provider adapters, task extraction, scheduling, notifications, export, and packaged Python sidecar are in place. No runtime data or credentials should be committed.
