# #opensourceware

Local Hermes Mandate

## I. Mandate

#opensourceware first: local machines, editable source, and open tooling—not cloud-only lock-in.

#250USA target: help 250 American entrepreneurs start businesses.

#æ^neuroplasticity: treat onboarding as critical-period cortical training—adaptive, intensive, time-sensitive rewiring of entrepreneurial behavior.

Run Hermes Agent **on this Windows machine**, not in a browser sandbox.
Use VS Code as the **local control plane** for edit, run, debug, and bridge.

Out of scope:
- Full desktop remote control via RDP/AnyDesk/TeamViewer
- Codex chat sandbox as runtime host
- Cloud-only development without local editable checkout

In scope:
- Editable local repo at `C:\æ\hermes-fork`
- CLI: `hermes chat`, `hermes setup`, `hermes mcp`, `hermes sessions`
- VS Code: Tasks, Debug, and `vscode_REMOTE_USE` extension
- Path to business automation via browser APIs without `cua-driver`

## II. System Requirements

- Windows 10/11
- Python 3.11+
- Node.js 18+ (for extension build only)
- VS Code 1.95+
- Git
- Administrator access during install

## III. Local Install Procedure

Run in VS Code PowerShell terminal:

```powershell
cd C:\æ\hermes-fork
python -m pip install -e ".[cli]"
hermes --help
```

If `python` is missing, use:

```powershell
py -3.11 -m pip install -e ".[cli]"
```

## IV. VS Code Bridge

### Tasks
`Ctrl+Shift+P` → **Tasks: Run Task**

- `Hermes: Setup`
- `Hermes: Chat`
- `Hermes: Quick One-Shot`
- `Hermes: MCP List`
- `Hermes: Sessions`
- `Hermes: Update` → `git pull; python -m pip install -e ".[cli]"`

### Debug
Open **Run and Debug** → select `Hermes: Chat` → `F5`

### Extension
Install `undefined_publisher.vscode-remote-use` from VSIX or folder.
Commands:
- `Remote Use: Capture Terminal Output`
- `Remote Use: Run Hermes Task`
- `Remote Use: Start Hermes Chat`

## V. Config Rules

Global Hermes config takes precedence over project defaults.

| Location | Purpose |
|---|---|
| `%LOCALAPPDATA%\\hermes\\config.yaml` | User-level settings |
| `%LOCALAPPDATA%\\hermes\\.env` | API keys |
| `C:\æ\hermes-fork\.env.example` | Local template |
| `C:\æ\hermes-fork\cli-config.yaml` | Project fallback |

Do not edit two configs in parallel. Use `hermes config` or `hermes setup`.

## VI. Guardrails

- Do not run `hermes` from the Codex chat sandbox.
- Never echo API keys.
- Validate JSON before committing `.vscode` artifacts.
- Use `hermes doctor` and `hermes status` before debugging.
- For browsers, prefer Hermes-native `computer-use` / `browser` tools over `cua-driver` when documentation allows.

## VII. Verification Checklist

```powershell
# CLI callable
hermes --help
# Extension installed
code --list-extensions | findstr remote-use
# Config present
ls $env:LOCALAPPDATA\hermes
# Tasks parse
python -m json.tool C:\æ\hermes-fork\.vscode\tasks.json
# Launch profile parse
python -m json.tool C:\æ\hermes-fork\.vscode\launch.json
# Extension compiles
cd C:\æ\hermes-fork\vscode-remote-use
npx tsc --noEmit
```

## VIII. Next Steps

1. Run `hermes setup`
2. Open `Ctrl+Shift+P` → `Remote Use: Start Hermes Chat`
3. Add MCP servers per business domain
4. Package and ship `vscode_REMOTE_USE` to teammates as a VSIX
