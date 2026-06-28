# Kodi-SH Distribution Fork Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create an independent personal Kodi distribution named **Kodi-SH** from the Kodi-SH codebase, with separate branding, install/update channels, release artifacts, and fixes for Yarin's workflow.

**Architecture:** Keep the Kodi addon/wizard architecture initially, but remove repository bloat by treating build zips/APKs/installers as release artifacts instead of git-tracked source. Rebrand the app/repository/wizard/page metadata first, then tackle functional fixes in small PRs.

**Tech Stack:** Kodi Python addons, GitHub Actions, GitHub Pages, Android APK rebranding/signing, NSIS Windows installer, XML addon metadata, static HTML.

---

## Naming Decisions

- Public/display name: `Kodi-SH`
- Repository name: `Kodi-SH`
- Android label: `Kodi-SH`
- Candidate Android package id: `org.xbmc.kdsh` — exactly 13 characters, matching `org.xbmc.kodi`, so it is compatible with the current same-length binary patching workflow.
- Project ownership: personal Yarin distribution; keep attribution/licensing intact until legal/licensing review is complete.

## Current Local State

A clean local seed repo exists at:

```bash
/home/yarin/Kodi-SH
```

It was created from upstream `yarinShapira/Kodi-SH` commit `baa4e16`, excluding large `dist/` artifacts and deleting copied `.zip/.apk/.exe/.enc` artifacts.

Initial verification already run:

```bash
cd /home/yarin/Kodi-SH
python3 -m compileall -q addons/service.subtitles.kodipovilai .github/scripts tools
python3 - <<'PY'
import yaml, pathlib
for p in sorted(pathlib.Path('.github/workflows').glob('*.yml')):
    yaml.safe_load(p.read_text())
    print('yaml ok', p)
PY
```

Expected/current result: core compile succeeds and all workflow YAML files parse.

---

## Task 1: Lock Down the Clean Repo Baseline

**Objective:** Ensure the new repo starts clean and cannot accidentally re-add huge artifacts.

**Files:**
- Modify: `.gitignore`
- Create: `docs/artifacts.md`

**Steps:**
1. Add ignores for generated build artifacts:
   - `dist/`
   - `*.apk`
   - `*.exe`
   - `*.zip` except source-managed test fixtures if explicitly needed later
   - `.secrets/`
2. Document that release artifacts live in GitHub Releases, not git.
3. Run:
   ```bash
   cd /home/yarin/Kodi-SH
   git status --short
   git ls-files | grep -E '\.(zip|apk|exe|enc)$' && exit 1 || true
   ```
4. Commit:
   ```bash
   git add .gitignore docs/artifacts.md
   git commit -m "chore: keep generated artifacts out of git"
   ```

## Task 2: Rebrand Top-Level Docs and Pages

**Objective:** Replace user-facing `Kodi-SH`/Moran URLs with `Kodi-SH` placeholders.

**Files:**
- Modify: `README.md`
- Modify: `ANDROID_TESTING.md`
- Modify: `APK_BUILD.md`
- Modify: `APK_RELEASE.md`
- Modify: `SECURITY.md`
- Modify: `index.html`
- Modify: `install.html`
- Modify: `downloads/**/*.html`

**Steps:**
1. Replace display copy with `Kodi-SH`.
2. Replace GitHub Pages URLs with placeholder `https://yarinShapira.github.io/Kodi-SH/` until the GitHub repo exists.
3. Fix known doc mismatch: package id must be `org.xbmc.kdsh` consistently, not `org.xbmc.kdsh`.
4. Run a text scan:
   ```bash
   search_files equivalent: Kodi-SH|Kodi-SH|yarinShapira|yarinShapira
   ```
5. Commit:
   ```bash
   git add README.md ANDROID_TESTING.md APK_BUILD.md APK_RELEASE.md SECURITY.md index.html install.html downloads
   git commit -m "docs: rebrand distribution as Kodi-SH"
   ```

## Task 3: Rebrand Android Build Workflow

**Objective:** Make APK builds generate side-by-side installable Kodi-SH packages.

**Files:**
- Modify: `.github/workflows/build-apk.yml`
- Modify: `.github/scripts/patch_apk_package_binary.py` only if needed
- Modify: `.github/scripts/verify_apk_package.py` only if needed

**Steps:**
1. Set:
   ```yaml
   PACKAGE_ID: 'org.xbmc.kdsh'
   APP_NAME: 'Kodi-SH'
   ```
2. Ensure `OLD_PACKAGE_ID` remains `org.xbmc.kodi`.
3. Keep same-length assertion.
4. Replace release filenames from `Kodi-SH-*` to `Kodi-SH-*`.
5. Run YAML parse and script compile.
6. Commit:
   ```bash
   git add .github/workflows/build-apk.yml .github/scripts
   git commit -m "ci: rebrand Android and Windows releases for Kodi-SH"
   ```

## Task 4: Rebrand Wizard Metadata

**Objective:** Make the wizard present Kodi-SH and pull from Kodi-SH URLs.

**Files:**
- Modify: `wizard/assets/build.txt`
- Modify: `wizard/source/plugin.program.kodipovilwizard/addon.xml`
- Modify: `wizard/source/plugin.program.kodipovilwizard/uservar.py`
- Modify: `wizard/source/plugin.program.kodipovilwizard/startup.py`
- Modify: `wizard/source/plugin.program.kodipovilwizard/resources/settings.xml`
- Modify: wizard language/copy files as found by search

**Steps:**
1. Keep addon id `plugin.program.kodipovilwizard` for phase 1 unless changing it proves low-risk.
2. Change displayed wizard/build name to `Kodi-SH`.
3. Change `build.txt` URLs to Kodi-SH release/raw placeholders.
4. Run compile on the wizard source, expecting a known failure in vendored Python-2 `resources/libs/zipfile.py` until Task 7 fixes it.
5. Commit:
   ```bash
   git add wizard
   git commit -m "feat: rebrand wizard for Kodi-SH"
   ```

## Task 5: Rebrand Repository Addon Channel

**Objective:** Create a separate Kodi repo channel for Kodi-SH.

**Files:**
- Modify/rename later: `repository/repository.kodipovilai/addon.xml`
- Modify: `repo/addons.xml`
- Modify: `repo/index.html`

**Steps:**
1. Phase 1 safe path: keep addon ids unchanged but rebrand display names and URLs.
2. Phase 2 optional path: rename `repository.kodipovilai` to `repository.kodish` and update zips/build tooling.
3. Update repo URLs to `https://yarinShapira.github.io/Kodi-SH/repo/...`.
4. Commit:
   ```bash
   git add repository repo
   git commit -m "feat: add Kodi-SH repository channel metadata"
   ```

## Task 6: Decide MoranSubs Strategy

**Objective:** Avoid breaking subtitle settings while separating visible ownership.

**Files:**
- Inspect/modify: `addons/service.subtitles.kodipovilai/addon.xml`
- Inspect/modify: `addons/service.subtitles.kodipovilai/resources/settings.xml`
- Inspect/modify: `repo/addons.xml`

**Recommended phase 1:** Keep internal addon id `service.subtitles.kodipovilai`, keep display name `MoranSubs` or `Kodi-SH MoranSubs` with attribution. This reduces breakage because many patchers and RunScript references assume the old id.

**Optional later phase:** Rename to `service.subtitles.kodish` after a dedicated search/replace + migration test.

**Steps:**
1. Keep attribution/license text.
2. Add Kodi-SH-specific defaults only after the base rebrand works.
3. Commit only copy/metadata changes initially.

## Task 7: Fix Wizard Python 2 Vendored zipfile

**Objective:** Ensure the wizard is Python 3 compatible.

**Files:**
- Modify/delete: `wizard/source/plugin.program.kodipovilwizard/resources/libs/zipfile.py`
- Modify: files importing fallback zipfile if necessary:
  - `resources/libs/test.py`
  - `resources/libs/extract.py`
  - `resources/libs/db.py`
  - `resources/libs/restore.py`
  - `resources/libs/backup.py`
  - `resources/libs/save.py`

**Steps:**
1. Prefer stdlib `zipfile`; remove Python-2 vendored fallback if tests/usage allow.
2. Run:
   ```bash
   cd /home/yarin/Kodi-SH
   python3 -m compileall -q wizard/source/plugin.program.kodipovilwizard
   ```
3. Expected: compile succeeds.
4. Commit:
   ```bash
   git add wizard/source/plugin.program.kodipovilwizard/resources/libs
   git commit -m "fix: remove Python 2 zipfile fallback from wizard"
   ```

## Task 8: Add CI Guardrails

**Objective:** Prevent regressions and artifact bloat.

**Files:**
- Create: `.github/workflows/ci.yml`

**Checks:**
1. Python compile for addon/tools/wizard.
2. YAML parse for workflows.
3. Block tracked `.zip/.apk/.exe/.enc` artifacts.
4. Optional: scan remaining hardcoded old branding and report, but do not fail until migration is complete.

**Commit:**
```bash
git add .github/workflows/ci.yml
git commit -m "ci: add Kodi-SH repository guardrails"
```

## Task 9: Create GitHub Repo and Push

**Objective:** Publish the independent source repo after local migration is coherent.

**Needs Yarin decision:** public/private and GitHub owner/org.

**Steps:**
1. Create GitHub repo `Kodi-SH`.
2. Push local `main`.
3. Configure branch protection / PR-only workflow.
4. Enable Pages after deploy workflow is fixed.
5. Add required secrets only after reviewing workflows:
   - `KEYSTORE_PASSWORD`
   - any release/deploy values needed later

## Task 10: First Release Dry Run

**Objective:** Prove install/update flow works end-to-end.

**Steps:**
1. Generate/sign keystore via setup workflow.
2. Build APK/installer workflow manually with a test version.
3. Publish a test release.
4. Verify Pages repo/wizard URLs return 200.
5. Install on a test Android/Kodi device.
6. Smoke test:
   - app launches side-by-side with official Kodi
   - wizard loads Kodi-SH build entry
   - MoranSubs settings open
   - subtitle search does not crash
   - quick update metadata is readable

---

## Immediate Open Decisions

1. GitHub owner: personal `yarin` account or another org/user?
2. Repository visibility: public or private?
3. Keep `MoranSubs` name with attribution, or rebrand display to `Kodi-SH Subs` in phase 1?
4. Keep wizard addon id for compatibility, or rename fully and accept more migration work?
5. Do we want a custom icon/splash now, or use placeholders until functionality is stable?
