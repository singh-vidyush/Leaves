# Leaves

> Go touch some grass

Leaves is a local-first, agentic desktop app that understands tasks from connected sources and organizes the user's schedule. It has no chat interface. User-provided keys for supported model providers (initial candidates: OpenAI, Anthropic Claude, and Google Gemini) power task understanding; task-relevant context may be sent to the configured provider. Leaves-held data and credentials stay on-device. The current build foundation includes a dashboard, local Markdown indexing/search, and a macOS menu-bar shell. Gmail, Google Calendar, model-provider calls, schedule planning, notifications, and packaged backend delivery are not implemented yet.

## Development

See [GUIDES/SETUP.md](GUIDES/SETUP.md) for prerequisites. After installing dependencies, start the API and desktop app with:

```sh
./scripts/dev.sh
```

Project decisions and specifications are indexed in [DOCS.md](DOCS.md).
