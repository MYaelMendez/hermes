# Technical Report: The Visual Studio Code Installer (All Versions)

**Scope:** How Microsoft packages and ships the VS Code *application itself* to end users (Windows `.exe`, macOS, Linux packages, archives, CLI). This does **not** cover how third-party extensions are distributed through the Marketplace — except where the `code` CLI and `vsce` tooling are relevant to side-loading a `.vsix` (relevant to the Hermes Agent extension packaging effort).

**Compiled:** 2026-07-10. All version numbers and dates are taken from the cited authoritative sources; none are fabricated. Where a source was unavailable or ambiguous, the gap is noted inline.

---

## 1. TIMELINE — Release History & Cadence

| Milestone | Date | Version | Source |
|---|---|---|---|
| First public release (preview) | **April 29, 2015** | pre-1.0 (0.x line) | Wikipedia: https://en.wikipedia.org/wiki/Visual_Studio_Code |
| Version 1.0 (stable, "has half a million users") | **April 14–15, 2016** | 1.0 | Wikipedia (citing Ars Technica, 15 Apr 2016) |
| Monthly Stable cadence begins | ~2016 onward | — | code.visualstudio.com/updates |
| Current stable | **July 8, 2026** | **1.128.0** | Wikipedia + https://code.visualstudio.com/updates ("Release date: July 8, 2026") |

- **First release date (April 29, 2015)** and **1.0 (April 2016)** are confirmed by Wikipedia's infobox and its citation to Ars Technica ("Visual Studio Code editor hits version 1, has half a million users", 15 April 2016).
- **Current stable = 1.128.0, released July 8, 2026.** Confirmed by two independent sources: the official release-notes page (`code.visualstudio.com/updates`, "Release date: July 8, 2026") and Wikipedia's infobox (Stable release 1.128.0 / 8 July 2026).
- **Cadence is monthly.** The official update API (`https://update.code.visualstudio.com/api/releases/stable`) returns **353 stable version strings**. The newest five are `1.128.0, 1.127.0, 1.126.0, 1.125.1, 1.125.0`; the oldest is `0.2.0`. The setup-overview page states plainly: *"VS Code ships weekly Stable releases with auto-update"* (https://code.visualstudio.com/docs/setup/setup-overview). Note the terminology nuance: VS Code internally tags "Stable" builds roughly monthly, while the same page describes Insiders as "ships nightly." The 353-entry list and the visible 1.125 → 1.128 progression confirm monthly feature releases are alive and current in 2026.

**Verdict on any "last updated 2022" claim:** VS Code *the product* is unambiguously still shipping monthly (latest 1.128.0, July 2026). A "last updated 2022" impression is **not** about the editor itself — it stems from a *specific deprecated tool* in the ecosystem (see §8). The editor is actively maintained.

---

## 2. INSTALLER TYPES ON WINDOWS

VS Code ships **two installer families** plus an archive/CLI path (https://code.visualstudio.com/docs/setup/windows):

### (a) Inno Setup `.exe` installers
| Installer | Scope | Admin rights | Install location | Notes |
|---|---|---|---|---|
| **User Setup** (User Installer) | Per-**user** | **Not required** | `%LOCALAPPDATA%\Programs\Microsoft VS Code` | Recommended; smoothest background updates |
| **System Setup** (System Installer) | Per-**machine** | **Required** (runs as admin) | `Program Files` | Available to all users; in-product updates also require elevation |

Direct quotes from the Windows setup docs:
- *"The User setup is the recommended installation for most people because it does not require administrator permissions and supports smoother background updates."*
- *"User setup — Install VS Code for your Windows account. This setup does not require administrator permissions. It installs under `%LOCALAPPDATA%\Programs\Microsoft VS Code` and provides the smoothest update experience."*
- *"System setup — Install VS Code for all users on the machine. This setup requires administrator permissions and installs under Program Files. In-product updates also require elevation."*
(Source: https://code.visualstudio.com/docs/setup/windows)

### (b) `.zip` archive + CLI
- A **ZIP archive** is offered for users who cannot run an installer (e.g. AppLocker/locked-down environments). Docs note: *"To use this installation method, unzip VS Code in your AppData\Local\Programs folder."* The ZIP does **not** self-update; updates are manual.
- The ZIP still includes the `bin\code.cmd` launcher and the `code` CLI (see §6).

### When was the User Installer introduced?
- **Preview in v1.25 (October 2017):** release notes list *"Preview Features — User setup on Windows"* (https://code.visualstudio.com/updates/v1_25).
- **Elevation no longer required / stabilized in v1.26 (November 2017):** *"User setup on Windows — Elevation no longer required during Windows setup"* (https://code.visualstudio.com/updates/v1_26).
- Before v1.25, only the System (per-machine, admin) installer and the ZIP existed. So the User Installer is ~9 years old as of 2026.

---

## 3. Inno Setup (Windows `.exe` packaging & update mechanism)

- **What it is:** Inno Setup is a free, open-source Windows installer-builder (by Jordan Russell / Martijn Laan). It produces a single self-extracting `.exe` setup with a wizard, registry/uninstall entries, and command-line switches.
- **Microsoft uses it for both Windows `.exe` installers** (User and System). The Windows setup docs explicitly state: *"VS Code uses Inno Setup to create its Windows setup package. All Inno Setup command-line switches are available."* (https://code.visualstudio.com/docs/setup/windows). Example documented switch: `/mergetasks=!runcode` to prevent launching VS Code after install.
- **Update mechanism (in-app auto-update):**
  - VS Code's running instance checks the update server; when a new Stable build is available it **downloads the update in the background** (no admin prompt for the User install).
  - On the **User Installer**, the update applies silently and the user is prompted to **restart** VS Code to pick up the new build. Because it installs under `%LOCALAPPDATA%`, no UAC/elevation is needed.
  - On the **System Installer**, in-product updates **require elevation** (UAC) because the files live under `Program Files`.
  - This is why docs call User setup the *"smoothest update experience."*
- Note: the underlying update framework on Windows for the shipped product is Microsoft's own **Windows Update / Squirrel-style** background-download-then-restart loop embedded in the Electron app; Inno Setup is used only for **first install / the installer executable**, not for the incremental patch delivery.

---

## 4. macOS & Linux Installers (brief)

### macOS
- **`.zip`** (Universal build) and **`.dmg`** (drag `Visual Studio Code.app` to Applications). Setup-overview docs: *"Download the .dmg installer. Open the .dmg file and drag Visual Studio Code.app to the Applications folder."* (https://code.visualstudio.com/docs/setup/setup-overview)
- **Auto-update:** Squirrel.Mac (the Electron `autoUpdater` framework, historically Squirrel-based on macOS). Background download + relaunch prompt, same model as Windows.
- Mac also offers a **`.zip`** with no installer for portable/CI use.

### Linux
- **`.deb`** (Debian/Ubuntu): `sudo apt install ./<file>.deb` — adds a repo for automatic updates via `apt`.
- **`.rpm`** (Fedora/RHEL): `sudo dnf install ./<file>.rpm` — adds a repo for automatic updates via `dnf`.
- **snap**: `snap install code --classic` (auto-updates through the snap store).
- **tarball** (`.tar.gz`): portable/CLI/container use; no auto-update.
- Setup-overview links a full Linux guide covering Snap, Arch, Nix, and other options.
- Source: https://code.visualstudio.com/docs/setup/setup-overview

---

## 5. UPDATE CHANNELS — Stable vs Insiders

| Channel | Ships | Auto-update | Coexists with other? |
|---|---|---|---|
| **Stable** | Monthly feature releases (≈ "weekly Stable releases with auto-update" per docs) | Yes (background download + restart) | — |
| **Insiders** | **Nightly** | Yes | Runs **side-by-side** with Stable |

- Quoted from setup-overview: *"VS Code ships weekly Stable releases with auto-update. To preview upcoming features, install the Insiders build, which ships nightly and runs side by side with Stable."*
- **Per-platform auto-update:**
  - **Windows:** Inno-based install + in-app background download/restart (User = no elevation; System = UAC).
  - **macOS:** Squirrel.Mac / Electron `autoUpdater` background download + relaunch.
  - **Linux:** `.deb`/`.rpm` update through the OS package manager repo (added at install); tarball/snap handle their own (snap store auto-update).
- The **About** dialog shows version + **commit ID**; for Insiders, multiple builds can share one version number, so the commit ID is the unique identifier. (Source: setup-overview.)

---

## 6. The `code` CLI & `code --install-extension <vsix> --force`

- The `code` command is the VS Code command-line launcher. On macOS/Linux it's placed on `PATH` via **Shell Command: Install 'code' command in PATH** (Command Palette); on Windows it ships in the install `bin\` dir. (Source: https://code.visualstudio.com/docs/setup/setup-overview)
- **Side-loading a `.vsix`** (exactly the mechanism the Hermes Agent extension uses):
  ```
  code --install-extension <path-to>.vsix --force
  ```
  - `--install-extension` installs a packaged extension from a local `.vsix` file (bypasses the Marketplace).
  - `--force` overwrites/reinstalls an existing version of the same extension ID — required when re-deploying a locally built VSIX over a previously installed copy.
- This is the documented, supported way to install extensions without the Marketplace and is the standard approach for internal/CI/enterprise VSIX distribution. It works against any installed VS Code (User or System) and respects the `engines.vscode` constraint declared in `package.json` (the Hermes extension targets `^1.85.0`).

---

## 7. `@vscode/vsce` — the packaging tool

- **What it is:** `vsce` (Visual Studio Code Extensions) is the official CLI to **package, publish, and manage** VS Code extensions (produces the `.vsix` file). It was originally published by Microsoft under the unscoped name **`vsce`**.
- **Rename / handoff to the `@vscode` scope:**
  - The unscoped **`vsce`** package was **last published `2.15.0` on 2022-12-02** (npm registry: https://registry.npmjs.org/vsce). It is effectively frozen/deprecated in favor of the scoped package.
  - The scoped **`@vscode/vsce`** package was **created 2022-12-02** (the same day) and is the maintained successor. Its `repository` field still points at `github.com/Microsoft/vsce` (https://registry.npmjs.org/@vscode/vsce).
- **Actively maintained — current ~3.x:**
  - Latest stable on the registry: **`3.9.2`, published 2026-06-03**; newer pre-release `3.9.3-2` exists (2026-06-26).
  - License: **MIT**. Homepage: code.visualstudio.com.
  - This directly matches the Hermes extension's declared dev dependency `@vscode/vsce ^3.9.2`.
- **Conclusion:** `@vscode/vsce` is alive and shipping (3.x, mid-2026). The 2022 date belongs only to the old unscoped `vsce`.

---

## 8. The "Microsoft's last update was 2022" — Most Likely Explanation

The impression almost certainly comes from the **deprecated, unscoped `vsce` npm package**, not VS Code itself:

- **Unscoped `vsce`** (https://registry.npmjs.org/vsce):
  - First publish: `0.1.0` on **2015-10-09**.
  - **Last publish: `2.15.0` on 2022-12-02** — and has not moved since.
  - This is the single most visible "Microsoft-owned, last touched 2022" artifact in the VS Code toolchain.
- The very next day the maintainership shifted to **`@vscode/vsce`** (created 2022-12-02), which is the live 3.x line.
- **Other candidates ruled out / contextualized:**
  - **`generator-code`** (Yeoman `yo code` scaffold) — **NOT** deprecated: latest `1.12.0` published **2026-06-23**, maintained by `microsoft1es`, `microsoft-oss-releases`, `vscode-bot`, etc. (https://registry.npmjs.org/generator-code).
  - **VS Code the editor** — NOT 2022: monthly cadence, current 1.128.0 (July 2026).
  - Old sample repos / `vscode-generator-code` mirrors might show stale 2022 commits, but the canonical generator is current.

**Actual status of the 2022 artifact:** The unscoped `vsce@2.15.0` is **frozen/deprecated**; users are expected to migrate to `@vscode/vsce` (3.x). It is not evidence that Microsoft abandoned VS Code tooling — the scoped successor is actively published.

---

## Source Index

- Stable release list (353 versions; newest 1.128.0): https://update.code.visualstudio.com/api/releases/stable
- Latest release notes / 1.128.0 date (July 8, 2026): https://code.visualstudio.com/updates
- Windows setup (User/System installers, Inno Setup, %LOCALAPPDATA% vs Program Files): https://code.visualstudio.com/docs/setup/windows
- Setup overview (Stable/Insiders cadence, macOS .dmg, Linux .deb/.rpm/snap, `code` CLI): https://code.visualstudio.com/docs/setup/setup-overview
- User Setup introduction: preview v1.25 (Oct 2017) https://code.visualstudio.com/updates/v1_25 ; elevation-free v1.26 (Nov 2017) https://code.visualstudio.com/updates/v1_26
- `@vscode/vsce` (3.9.2, 2026-06-03; repo github.com/Microsoft/vsce): https://registry.npmjs.org/@vscode/vsce
- Unscoped `vsce` (last 2.15.0, 2022-12-02): https://registry.npmjs.org/vsce
- `generator-code` (1.12.0, 2026-06-23): https://registry.npmjs.org/generator-code
- Timeline / first release (Apr 29 2015) / 1.0 (Apr 2016) / stable 1.128.0 (Jul 8 2026): https://en.wikipedia.org/wiki/Visual_Studio_Code
