# Resk Remote

Resk-branded build of RustDesk, preconfigured for our self-hosted server
(`rustdesk.resk.ai`). AGPL-3.0, like upstream.

## What differs from upstream
- `libs/hbb_common` points at `preplink/resk-remote-hbb-common` (branch `resk`):
  app name `ReskRemote`, ID/relay server `rustdesk.resk.ai`, server public key.
  No spaces in the app name: Windows uninstall runs unquoted `sc stop {app_name}`.
- `resk/apply_branding.py`: Resk palette in the Flutter theme, display name
  "Resk Remote", Android package `ai.resk.remote`. Idempotent.
- `resk/gen_assets.py`: every icon, logo and installer bitmap from `resk/source`.
- `.github/workflows/flutter-build.yml`: `resk-only` input skips macOS/iOS/Sciter/
  packaging and builds the MSI as ReskRemote. `resk-build.yml` is the entry point.

## Build
Actions → "Resk Remote build" → Run workflow. It publishes a release
`v<version>-resk.<run>` with Windows (.exe, .msi) and Android (.apk) files.
Android signing key: repo secrets `ANDROID_*`, backed up in the team secret
manager. Never rotate it: installed apps only accept
updates signed with the same key.

## Pulling upstream
    git fetch upstream && git merge upstream/master
    python3 resk/apply_branding.py && python3 resk/gen_assets.py
Rebase `resk-remote-hbb-common` onto the hbb_common commit upstream now pins,
then bump the submodule here.
