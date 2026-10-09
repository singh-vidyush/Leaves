<div align="center">

<img src="assets/leaves-logo.svg" alt="Leaves Logo" width="90" />

# Leaves 🌿

### Less planning. More living.

**Your tasks, emails, and calendar — finally working together.**

Leaves is a free, local-first desktop assistant that turns scattered information into actionable tasks, prioritizes what matters, and helps you make time for it.

<br />

[![Platform](https://img.shields.io/badge/Platform-macOS-000000?style=flat-square&logo=apple&logoColor=white)](https://github.com/singh-vidyush/Leaves/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square)](LICENSE)
[![Release](https://img.shields.io/github/v/release/singh-vidyush/Leaves?style=flat-square&label=Release)](https://github.com/singh-vidyush/Leaves/releases/latest)
[![GitHub Stars](https://img.shields.io/github/stars/singh-vidyush/Leaves?style=flat-square)](https://github.com/singh-vidyush/Leaves/stargazers)

<br />

[**Download Leaves**](https://github.com/singh-vidyush/Leaves/releases/latest) ·
[**Installation Guide**](#installation) ·
[**Features**](#features) ·
[**Contribute**](#contributing)

<br />

*Your attention belongs to your life, not your inbox.*

</div>

---

## 🍃 Why Leaves?

Your responsibilities don't arrive in one place.

Some are buried in emails. Others are scattered across notes, documents, and calendar events. Keeping track of everything shouldn't become another full-time job.

**Leaves brings everything together and helps you decide what deserves your attention.**

It finds actionable tasks, understands their urgency, and helps organize your schedule around your existing commitments.

And unlike cloud-first productivity tools, **your Leaves data stays on your device.**

---

## ✨ Features

| Feature | What Leaves does |
|---------|-----------------|
| 📥 **Smart Task Extraction** | Identifies actionable tasks from documents, notes, and connected Gmail messages. |
| 🎯 **Intelligent Prioritization** | Assigns urgency scores from 1–10, with explanations for why each task matters. |
| 📅 **Calendar-Aware Scheduling** | Finds available time around meetings, working hours, breaks, and time away. |
| ✉️ **Gmail Integration** | Syncs emails with read-only access and identifies messages requiring attention. |
| 🔎 **Local Search** | Indexes selected folders so you can quickly find relevant information. |
| 🔐 **Privacy First** | Stores working data locally and protects Google credentials using the macOS Keychain. |
| ⚡ **Automatic Scheduling** | Can schedule high-priority tasks when Google Calendar is connected. |
| 📤 **Data Export** | Export your Leaves data as JSON whenever you want. |

### Built around your schedule

Leaves doesn't just create another to-do list.

It considers your existing calendar commitments, preferred working hours, breaks, and time-away blocks before finding room for new tasks.

**You stay in control:** deleting an existing calendar event requires your confirmation.

---

## 🚀 Installation

### macOS

Leaves is completely free to install.

**Option 1 — One-command installation (recommended)**

Open Terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/singh-vidyush/Leaves/main/scripts/install.sh | bash
```

That's it!

The installer will:

- Download the latest Leaves release.
- Verify the published SHA-256 checksum.
- Install `Leaves.app` into Applications.
- Clean up temporary installation files.

**No Python, Node.js, Rust, Homebrew, or other development tools required.**

**Option 2 — Manual download**

Prefer installing manually?

1. Visit the [**latest GitHub Release**](https://github.com/singh-vidyush/Leaves/releases/latest).
2. Download the macOS `.dmg` file.
3. Open the downloaded file.
4. Drag `Leaves.app` into **Applications**.
5. Launch Leaves from Finder or Launchpad.

### ⚠️ First launch on macOS

Leaves is currently unsigned because the project is independently developed and distributed for free.

macOS may display a security warning when opening it for the first time.

If that happens:

1. Try opening **Leaves** from Applications.
2. Open **System Settings → Privacy & Security**.
3. Find the security message about Leaves.
4. Click **Open Anyway**, if available.
5. Confirm that you want to open the application.

You should only need to approve the application once per installation.

> **Security:** Download Leaves only from this repository or its official GitHub Releases. The installer verifies the published checksum before installation.

### Updating Leaves

To install the latest version, simply run the same command again:

```bash
curl -fsSL https://raw.githubusercontent.com/singh-vidyush/Leaves/main/scripts/install.sh | bash
```

Your locally stored Leaves data remains intact.

---

## 🌱 Getting Started

Once Leaves is installed, you're ready to organize your day.

**1. Explore your workspace**

Open Leaves and navigate through:

`Overview` · `Tasks & Urgency` · `Calendar` · `Search` · `Sources` · `Settings`

**2. Connect your sources**

Open **Sources** and select local folders containing notes or documents.

Leaves indexes the selected material to make it searchable and identify actionable tasks.

**3. Personalize your schedule**

Open **Settings** and configure:

- Working hours
- Breaks
- Time-away blocks
- Scheduling preferences

**4. Connect Google (optional)**

Leaves supports Gmail and Google Calendar.

To connect:

1. Create a Google OAuth **Desktop** client in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the Gmail API for Gmail integration.
3. Copy your OAuth Client ID and Client Secret.
4. Enter both credentials in **Leaves → Settings**.
5. Connect Gmail or Calendar and complete Google's sign-in flow.

Your credentials are stored in the macOS Keychain.

> **Note:** Google integrations are optional. Leaves does not include shared Google OAuth credentials. If your Google OAuth consent screen is in testing mode, add your Google account as a test user.

**5. Let Leaves help you plan**

Review your extracted tasks, understand their urgency scores, and schedule them around your existing commitments.

When Gmail and Calendar are connected, Leaves can also automatically schedule high-urgency tasks.

---

## 🔒 Privacy & Data

**Your data. Your device. Your control.**

Leaves is designed around local-first storage and user-controlled integrations.

| Data | How Leaves handles it |
|------|-----------------------|
| Tasks and scheduling data | Stored locally |
| Indexed documents | Stored locally |
| Google OAuth credentials | Stored in macOS Keychain |
| Google access tokens | Stored in the OS secure credential store |
| Gmail | Read-only access |
| Calendar | Access limited to events owned by the connected account |
| Data export | Available in JSON format |

Google connections are optional.

Leaves does not require a Leaves account.

---

## 🛠 Troubleshooting

<details>
<summary><b>macOS says "Leaves is damaged" or cannot be opened</b></summary>

<br />

Leaves is currently unsigned, so macOS Gatekeeper may prevent it from opening.

Try launching Leaves once, then navigate to:

**System Settings → Privacy & Security → Open Anyway**

Confirm the launch if that option is available.

Always download Leaves from the [official Releases page](https://github.com/singh-vidyush/Leaves/releases/latest).

</details>

<details>
<summary><b>macOS Keychain keeps asking for permission</b></summary>

<br />

Leaves uses the macOS Keychain to securely store Google credentials.

If macOS requests access, verify that the prompt is associated with Leaves before approving it.

You may choose **Always Allow** if you trust the application and want macOS to remember your decision.

If prompts continue appearing, report the issue with your macOS version and the exact prompt text.

**Never share your password or OAuth credentials in an issue.**

</details>

<details>
<summary><b>Google sign-in is blocked</b></summary>

<br />

Verify that:

- Your OAuth Client ID and Client Secret belong to the same Google OAuth Desktop client.
- The required Google APIs are enabled.
- Your Google account is listed under **Test users** if your OAuth application is in testing mode.

Then reconnect the integration from Leaves Settings.

</details>

<details>
<summary><b>Gmail is connected but not syncing</b></summary>

<br />

Check that:

- Gmail is connected in Leaves.
- The Gmail API is enabled in Google Cloud Console.
- Your Google authorization hasn't been revoked.

Google may temporarily rate-limit requests. Wait a few minutes before retrying.

If necessary, disconnect and reconnect Gmail.

</details>

<details>
<summary><b>The installer cannot download or verify Leaves</b></summary>

<br />

Check your internet connection and confirm that a release is available on the [GitHub Releases page](https://github.com/singh-vidyush/Leaves/releases/latest).

The installer intentionally stops if the release or its checksum cannot be verified.

</details>

---

## 🧑‍💻 Build from Source

Want to contribute or run the development version?

### Prerequisites

- macOS
- Python 3.11+
- Node.js 20.19+ or 22.12+
- pnpm
- Rust
- Xcode Command Line Tools

### Development Setup

```bash
git clone https://github.com/singh-vidyush/Leaves.git
cd Leaves

# Set up the Python backend
python3 -m venv apps/server/.venv
apps/server/.venv/bin/python -m pip install -e "apps/server[bundle,test]"

# Install frontend dependencies
cd apps/desktop
pnpm install --frozen-lockfile
cd ../..

# Start Leaves
./scripts/dev.sh
```

### Build the macOS Application

```bash
./scripts/build_macos.sh
```

This generates the macOS application and disk image.

For additional development guidelines, see [contribution.md](contribution.md).

---

## 🗺 Roadmap

Leaves is actively evolving.

**Current focus**
- [x] macOS desktop application
- [x] Gmail integration
- [x] Google Calendar integration
- [x] Task extraction and urgency scoring
- [x] Calendar-aware task scheduling
- [x] Local data storage
- [x] One-command macOS installer

**Looking ahead**
- [ ] Windows support
- [ ] Linux support
- [ ] Additional productivity integrations
- [ ] Improved scheduling intelligence
- [ ] More personalization and automation

Have an idea? [Open a feature request](https://github.com/singh-vidyush/Leaves/issues).

---

## 🤝 Contributing

Leaves is an open-source project, and contributions are welcome.

Whether you're fixing a bug, improving documentation, suggesting an integration, or contributing code, your help makes Leaves better.

Read [**contribution.md**](contribution.md) to get started.

Found a bug? [Report an issue](https://github.com/singh-vidyush/Leaves/issues).

---

<div align="center">

### 🍃 Less screen time. More real life.

**Leaves handles the planning. You go touch some grass.**

<br />

Made with care, for people who have better things to do than manage another to-do list.

<br />

[⭐ Star Leaves](https://github.com/singh-vidyush/Leaves) · [🐛 Report a Bug](https://github.com/singh-vidyush/Leaves/issues) · [⬇️ Download](https://github.com/singh-vidyush/Leaves/releases/latest)

</div>
