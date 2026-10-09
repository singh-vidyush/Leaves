# Leaves

> Go touch some grass

Leaves is a local-first, agentic desktop app that understands tasks from selected sources and organizes the user's schedule. It has no chat interface. Users can choose OpenAI, Anthropic, or Gemini for task understanding; only task-relevant context should be sent to that provider. Leaves-held data stays on-device, and credentials use the operating system's secure credential manager. The app includes a dashboard, local Markdown indexing/search, heuristic and model task extraction, Google OAuth for read-only Gmail and Google Calendar scheduling, and a macOS menu-bar shell. Local sample data remains available until Google accounts are connected.

## Development

See [GUIDES/SETUP.md](GUIDES/SETUP.md) for prerequisites. After installing dependencies, start the API and desktop app with:

```sh
./scripts/dev.sh
```

Project decisions and specifications are indexed in [DOCS.md](DOCS.md).

## Download Leaves

The signed macOS installer will be available on the [GitHub Releases page](https://github.com/singh-vidyush/Leaves/releases) after the release signing setup is complete. Then you can download and open it from Terminal with:

```sh
curl -fL "https://github.com/singh-vidyush/Leaves/releases/latest/download/Leaves-macos-$(uname -m).dmg" -o Leaves.dmg && open Leaves.dmg
```

See [the distribution guide](GUIDES/DISTRIBUTION.md) for release setup and installation details.
