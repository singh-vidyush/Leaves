# Contributing to Leaves

Thanks for helping Leaves grow. Bug reports, usability feedback, documentation updates, and focused code changes are all welcome.

## Before you start

- Search [existing issues](https://github.com/singh-vidyush/Leaves/issues) to avoid duplicates.
- For a large change or new feature, open an issue first so we can agree on the approach.
- Keep changes focused and preserve the local-first behavior and existing Gmail, calendar, and scheduling features.

## Development setup

Leaves currently ships as a macOS desktop app. Building it from source requires Python 3.11+, Node.js 20.19+ or 22.12+, pnpm, Rust, and the Xcode Command Line Tools. Follow the [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/) for macOS.

From the repository root:

```sh
python3 -m venv apps/server/.venv
apps/server/.venv/bin/python -m pip install -e "apps/server[bundle,test]"
cd apps/desktop
pnpm install --frozen-lockfile
cd ../..
./scripts/dev.sh
```

The development script starts the local API and desktop app. Google OAuth is optional. To test Google integrations, configure a Google OAuth Desktop client in the app's Settings; do not add credentials to the repository.

## Run checks

Run the backend test suite:

```sh
apps/server/.venv/bin/python -m pytest apps/server/tests -q
```

Build the desktop frontend:

```sh
cd apps/desktop
pnpm build
cd ../..
```

For installer changes, run the shell syntax and mocked installer checks available in `scripts/tests/`. If a change needs a macOS-only check that you cannot run, mention that clearly in the pull request.

## Make a contribution

1. Fork the repository and create a branch for your change.
2. Make the smallest change that solves the problem.
3. Run the relevant checks and review your diff for unrelated edits or secrets.
4. Open a pull request against `main` with a clear summary, the reason for the change, and the checks you ran. Include screenshots for visible UI changes when helpful.

## Security and privacy

- Never commit `.env` files, OAuth client secrets, access or refresh tokens, private user data, or generated app databases.
- Do not print credentials or tokens in logs, errors, screenshots, or test output.
- Keep Google OAuth scopes minimal and preserve explicit confirmation for destructive calendar actions.
- Do not weaken local API protections or introduce external data collection without discussing it in an issue first.
- Use fake credentials and synthetic data in tests.

## Roadmap

macOS is the current desktop platform. Windows and Linux support are future goals, and contributions that make the app more portable are welcome. Please open an issue before starting platform-specific work so we can coordinate it.
