<p align="center">
  <img src="assets/leaves-logo.svg" alt="Leaves leaf logo" width="76" height="76">
</p>

<h1 align="center">Leaves</h1>

<p align="center">
  Turn the things competing for your attention into a clear, workable plan.
</p>

<p align="center">
  A free desktop planner that brings tasks, important messages, and calendar commitments together—while keeping your Leaves data on your device.
</p>

## Why Leaves

Work and personal commitments arrive in different places. Leaves helps you see what needs attention, understand why it matters, and find time to do it. Your notes, task list, schedule, and connected account data are kept locally on your computer.

## What you can do

- **Capture and find context.** Add local folders as sources, index their documents, and search across the material you want to keep at hand.
- **Turn context into tasks.** Extract actionable tasks from your sources and connected Gmail, with a 1–10 urgency score and an explanation for each score.
- **Plan around your day.** Set working hours, breaks, and time-away blocks. Leaves finds available time around existing calendar events and helps resolve scheduling conflicts.
- **Keep your calendar in view.** Connect Google Calendar to see your events and schedule Leaves tasks. Deleting a calendar event always asks for confirmation.
- **Stay on top of urgent email.** Connect Gmail to sync messages with read-only access. Leaves checks for new messages while it is open and can automatically schedule high-urgency tasks when a calendar is connected.
- **Keep control of your data.** Leaves stores its working data locally, saves Google credentials and tokens in the operating system's secure credential store, and lets you export your Leaves data as JSON.

## Install on macOS

Leaves is free to install. The simplest option is to run this command in Terminal:

```sh
curl -fsSL https://raw.githubusercontent.com/singh-vidyush/Leaves/main/scripts/install.sh | bash
```

The installer downloads the latest release, checks its SHA-256 checksum, and installs Leaves in Applications. It does not need Python, Node.js, Rust, Homebrew, or `sudo` for a normal installation.

After installation, open **Leaves** from Finder → **Applications**. You can also use the [latest release page](https://github.com/singh-vidyush/Leaves/releases/latest) to download the disk image directly.

Leaves is currently unsigned, so macOS may ask you to confirm the first launch:

1. Try to open Leaves from Applications.
2. Open **System Settings → Privacy & Security**.
3. Select **Open Anyway** for Leaves if that option appears.
4. Confirm that you want to open it.

To update or reinstall, run the same installer command again. It verifies the new download before replacing the app; your local data remains in place.

## Get started

1. Open Leaves and explore **Overview**, **Tasks & Urgency**, **Calendar**, **Search**, **Sources**, and **Settings**.
2. In **Sources**, add a local folder containing notes or documents you want Leaves to search and use for task extraction.
3. In **Settings**, choose your working hours and breaks. Add time-away blocks so scheduling leaves room for appointments and time off.
4. To connect Google, enter the Client ID and Client Secret from a Google OAuth Desktop client in **Settings**, then connect Gmail and/or Calendar and complete Google's sign-in flow. Leaves stores these credentials in your macOS Keychain.
5. Review extracted tasks and their urgency explanations. Schedule a task when you are ready; connected calendar events and your availability are considered.

Google connections are optional. Google OAuth credentials are not included with the app: you provide your own client credentials. Gmail access is read-only; Calendar access is limited to events owned by the connected account. Gmail needs the Gmail API enabled in the Google Cloud project that owns the OAuth client. If Google's consent screen is in testing mode, the account must be listed as a test user.

## Common problems

### macOS says Leaves is damaged or cannot be opened

Leaves is currently unsigned. Try opening it once, then use **System Settings → Privacy & Security → Open Anyway** and confirm. Download only from the installer command above or the [official GitHub Releases page](https://github.com/singh-vidyush/Leaves/releases/latest). The installer verifies the published checksum and stops if it cannot.

### A Keychain password prompt appears

This prompt allows the Leaves backend to read saved Google credentials from your macOS login Keychain. Enter your Mac login password and choose **Always Allow** to remember the permission. If the prompt keeps returning after that, close Leaves and contact the project with your macOS version and the exact prompt text; do not share your password or OAuth secret.

### Google sign-in is blocked

Check that the Client ID and Client Secret in Leaves Settings belong to the same Google OAuth Desktop client. In Google Cloud Console, enable the Gmail API if you are connecting Gmail. If the consent screen is still in testing mode, add your Google account under **Test users**. Then reconnect the service in Leaves.

### Gmail cannot sync

Confirm Gmail shows as connected in Leaves and that the Gmail API is enabled for the OAuth project. Google may temporarily rate-limit requests; wait a few minutes and try syncing again. If your OAuth access was revoked, disconnect and reconnect Gmail.

### The installer cannot download or verify a release

Check your internet connection and try again. The installer will stop if a release file or its checksum is unavailable or does not match. You can check the [latest release page](https://github.com/singh-vidyush/Leaves/releases/latest) for the current installer status.

## Future plans

macOS is the currently supported desktop platform. Windows and Linux desktop apps are part of the future scope. Help us grow Leaves by testing it, reporting issues, improving the documentation, or contributing code. See the [contribution guide](contribution.md) to get started.

## Contributing

We welcome thoughtful bug reports, feature ideas, documentation improvements, and code contributions. Please read [contribution.md](contribution.md) before opening a pull request.

## Build from source

Building the app is for contributors and developers. It requires Python 3.11+, Node.js 20.19+ or 22.12+, pnpm, Rust, and the Xcode Command Line Tools.

```sh
git clone https://github.com/singh-vidyush/Leaves.git
cd Leaves
python3 -m venv apps/server/.venv
apps/server/.venv/bin/python -m pip install -e "apps/server[bundle,test]"
cd apps/desktop
pnpm install --frozen-lockfile
cd ../..
./scripts/dev.sh
```

To build the macOS app and disk image, run `./scripts/build_macos.sh` from the repository root. For detailed contributor guidance, see [contribution.md](contribution.md).

---

<p align="center">Made with care. Keep your attention on what matters.</p>
