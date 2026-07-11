# vscode_REMOTE_USE

Hermes control plane through VS Code APIs. No `cua-driver`, no `computer_use`.

## Commands

- `Remote Use: Capture Terminal Output` — focus active Hermes terminal
- `Remote Use: Run Hermes Task` — run Setup/Chat/MCP/Sessions/Update
- `Remote Use: Start Hermes Chat` — launch `hermes chat` in repo cwd

## Install from Folder

1. Open VS Code
2. Extensions → `...` → **Install from VSIX...**
3. Select generated `.vsix`

## Build

```powershell
cd C:\æ\hermes-fork\vscode-remote-use
npm install
npx tsc
npx vsce package
```

## Structure

```
vscode-remote-use/
  package.json
  tsconfig.json
  src/extension.ts
  out/extension.js
```

## Blueprint

Part of `hermes-fork/blueprints/computer-use-for-business.md`.

## Status

Compiled. Untested in VS Code extension host. Use as template.
