# Artifact Policy

Kodi-SH keeps source and release artifacts separate.

## Tracked in git

- Kodi add-on source code under `addons/`, `wizard/source/`, `repository/`, `tools/`
- GitHub Actions workflows and helper scripts
- Static HTML/docs and metadata files
- Small artwork/source assets required to build packages

## Not tracked in git

The following are generated artifacts and must be published as GitHub Release assets or produced by CI:

- `dist/`
- `*.zip`
- `*.apk`
- `*.exe`
- encrypted signing material such as `.secrets/*.enc`
- local keystores and build work directories

## Why

The upstream seed repository contained many gigabytes of build zips. Keeping those in git makes clones, CI, and Pages deployment slow and fragile. Kodi-SH should keep git lightweight and use release/download URLs in `wizard/assets/build.txt` to point at published artifacts.

## Verification

Before pushing, run:

```bash
git ls-files | grep -E '\.(zip|apk|exe|enc)$' && exit 1 || true
```

This should print nothing and exit successfully.
