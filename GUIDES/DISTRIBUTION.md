# Downloading and distributing Leaves

The normal user install is a macOS disk image (`.dmg`), not a source checkout.
The GitHub Actions workflow builds separate native packages for Apple Silicon
and Intel Macs. Pushes to `main` or `work` upload unsigned test DMGs as
14-day workflow artifacts. A version tag builds release packages; GitHub Release
assets are published only when the app has been signed and notarized.

## One-line download

After the first signed release is published, download and open the DMG that
matches the Mac's processor:

```sh
curl -fL "https://github.com/singh-vidyush/Leaves/releases/latest/download/Leaves-macos-$(uname -m).dmg" -o Leaves.dmg && open Leaves.dmg
```

In the window that opens, drag Leaves to **Applications**. Open Leaves from
Applications or Spotlight. The DMG contains the app and bundled local API; users
do not install Python, Rust, Node.js, or pnpm.

## Configure release signing once

Publishing a Mac app without Gatekeeper warnings requires an Apple Developer
ID Application certificate and notarization credentials. In the GitHub
repository, add these under **Settings → Secrets and variables → Actions**:

- `APPLE_CERTIFICATE`: base64-encoded Developer ID Application `.p12`
- `APPLE_CERTIFICATE_PASSWORD`: password used to export the `.p12`
- `APPLE_SIGNING_IDENTITY`: full Developer ID Application identity
- `APPLE_ID`: Apple ID email used for notarization
- `APPLE_PASSWORD`: an Apple app-specific password
- `APPLE_TEAM_ID`: Apple Developer Team ID

Do not commit these values or send them in chat. Branch builds don't receive the
secrets and produce unsigned test artifacts only. A tag build with incomplete
secrets also produces a test artifact, but does not publish a GitHub Release.

## Publish a version

First merge the release workflow and app changes into `main`. Update the
matching version in `apps/desktop/package.json`,
`apps/desktop/src-tauri/Cargo.toml`, and
`apps/desktop/src-tauri/tauri.conf.json`. For version `0.1.0`, create and push
the tag:

```sh
git switch main
git pull
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions builds a DMG for Apple Silicon and Intel, signs and notarizes
each package, and attaches both to the GitHub Release. The release job verifies
that the tag matches the Cargo and Tauri versions.
