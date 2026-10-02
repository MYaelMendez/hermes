"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
function escapeHtml(value) {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
function getHermesRepoPath() {
    const repo = vscode.workspace.getConfiguration('remoteUse').get('hermesRepoPath', '');
    if (typeof repo === 'string' && repo.trim()) {
        return repo.trim();
    }
    const folder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (typeof folder === 'string' && folder.trim()) {
        return folder;
    }
    return '';
}
function toPowerShellSingleQuoted(value) {
    return `'${value.replace(/'/g, "''")}'`;
}
function launchTerminalCommand(name, command) {
    const terminal = vscode.window.createTerminal(name);
    terminal.sendText(command);
    terminal.show();
}
function getVlcPath() {
    try {
        const configured = vscode.workspace.getConfiguration('remoteUse').get('vlcPath', '');
        if (typeof configured === 'string' && configured.trim() && require('fs').existsSync(configured.trim())) {
            return configured.trim();
        }
    }
    catch {
        // ignore config read errors
    }
    const candidates = [
        'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe',
        '/Applications/VLC.app/Contents/MacOS/VLC',
        '/usr/bin/vlc',
    ];
    return candidates.find((path) => require('fs').existsSync(path)) || '';
}
function openInVlc(inputPath) {
    const vlcPath = getVlcPath();
    if (!vlcPath) {
        vscode.window.showWarningMessage('Remote Use: VLC not found');
        return;
    }
    const command = [
        `$vlc = ${toPowerShellSingleQuoted(vlcPath)}`,
        `if (-not (Test-Path $vlc)) { Write-Error 'VLC not found at configured path'; exit 1 }`,
        `& $vlc ${toPowerShellSingleQuoted(inputPath)}`,
    ].join('; ');
    launchTerminalCommand('Hermes Media VLC', command);
}
function transcodeToMp3(inputPath, outputPath) {
    const command = [
        `ffmpeg -y -i ${toPowerShellSingleQuoted(inputPath)} ${toPowerShellSingleQuoted(outputPath)}`,
        `Write-Output ${toPowerShellSingleQuoted(`ffmpeg_output=${outputPath}`)}`,
    ].join('; ');
    launchTerminalCommand('Hermes Media FFmpeg', command);
}
function runHermesMediaAction(action, manifestPath) {
    const repo = getHermesRepoPath();
    const command = [
        `Set-Location ${toPowerShellSingleQuoted(repo)}`,
        `hermes media ${action} --manifest ${toPowerShellSingleQuoted(manifestPath)}`,
    ].join('; ');
    launchTerminalCommand(`Hermes Media ${action}`, command);
}
function runHermesMediaCoevolve(manifest, goal) {
    const inputPath = String(manifest.input_path || '');
    const outputPath = String(manifest.output_path || '');
    if (!inputPath || !outputPath) {
        vscode.window.showErrorMessage('Manifest requires input_path and output_path for coevolve.');
        return;
    }
    const memberToken = String(manifest.member_token || '+æ');
    const governance = String(manifest.governance || 'none');
    const surface = String(manifest.surface || 'ae://HERMES-AGENT^media');
    const repo = getHermesRepoPath();
    const command = [
        `Set-Location ${toPowerShellSingleQuoted(repo)}`,
        `hermes media coevolve --goal ${toPowerShellSingleQuoted(goal)} --input ${toPowerShellSingleQuoted(inputPath)} --output ${toPowerShellSingleQuoted(outputPath)} --codec h264_nvenc --surface ${toPowerShellSingleQuoted(surface)} --member-token ${toPowerShellSingleQuoted(memberToken)} --governance ${toPowerShellSingleQuoted(governance)}`,
    ].join('; ');
    launchTerminalCommand('Hermes Media Coevolve', command);
}
function inferMediaKind(filePath) {
    const ext = filePath.toLowerCase().split('.').pop() || '';
    const audioExt = new Set(['mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac']);
    const videoExt = new Set(['mp4', 'webm', 'mov', 'mkv', 'avi', 'm4v']);
    if (audioExt.has(ext)) {
        return 'audio';
    }
    if (videoExt.has(ext)) {
        return 'video';
    }
    return undefined;
}
function collectPreviewEntries(panel, manifest) {
    const fs = require('fs');
    const entries = [];
    const candidates = [
        { label: 'Input Preview', path: manifest.input_path },
        { label: 'Output Preview', path: manifest.output_path },
    ];
    for (const candidate of candidates) {
        const p = String(candidate.path || '').trim();
        if (!p || !fs.existsSync(p)) {
            continue;
        }
        const kind = inferMediaKind(p);
        if (!kind) {
            continue;
        }
        const webviewUri = panel.webview.asWebviewUri(vscode.Uri.file(p)).toString();
        entries.push({ label: candidate.label, kind, uri: webviewUri });
    }
    return entries;
}
function encodeUtf8Bytes(text) {
    const { Buffer } = require('buffer');
    return Uint8Array.from(Buffer.from(text, 'utf8'));
}
function decodeUtf8Bytes(raw) {
    const { Buffer } = require('buffer');
    return Buffer.from(raw).toString('utf8');
}
async function readManifest(uri) {
    const raw = await vscode.workspace.fs.readFile(uri);
    const text = decodeUtf8Bytes(raw);
    return JSON.parse(text);
}
async function openMediaWindowFromUri(uri) {
    const manifest = await readManifest(uri);
    await openMediaWindowFromManifest(manifest, uri.fsPath);
}
async function openMediaWindowFromManifest(manifest, manifestPath) {
    const fs = require('fs');
    const localRoots = [];
    const candidatePaths = [manifest.input_path, manifest.output_path, manifestPath];
    for (const candidate of candidatePaths) {
        const p = String(candidate || '').trim();
        if (!p) {
            continue;
        }
        const dir = fs.existsSync(p) && fs.statSync(p).isDirectory() ? p : require('path').dirname(p);
        if (!dir) {
            continue;
        }
        localRoots.push(vscode.Uri.file(dir));
    }
    const panel = vscode.window.createWebviewPanel('remoteUseMediaWindow', 'Remote Use: Media Window', vscode.ViewColumn.Beside, {
        enableScripts: true,
        localResourceRoots: localRoots,
    });
    const previews = collectPreviewEntries(panel, manifest);
    panel.webview.html = renderMediaViewportHtml(manifest, manifestPath, previews);
    panel.webview.onDidReceiveMessage((message) => {
        const effectiveManifestPath = message?.manifestPath || manifestPath;
        if (message?.type === 'openVlc') {
            const inputPath = String(manifest?.input_path || '');
            if (!inputPath) {
                vscode.window.showErrorMessage('Manifest has no input_path for VLC playback.');
                return;
            }
            openInVlc(inputPath);
            return;
        }
        if (message?.type === 'runManifest') {
            runHermesMediaAction('run', effectiveManifestPath);
            return;
        }
        if (message?.type === 'transcodeMp3') {
            const inputPath = String(manifest?.input_path || '');
            if (!inputPath) {
                vscode.window.showErrorMessage('Manifest has no input_path for FFmpeg transcode.');
                return;
            }
            const outputPath = String(manifest?.output_path || `${inputPath}.transcoded.mp3`);
            transcodeToMp3(inputPath, outputPath);
            return;
        }
        if (message?.type === 'coevolve') {
            const goal = String(message?.goal || 'optimize for mobile shortform');
            runHermesMediaCoevolve(manifest, goal);
            return;
        }
        if (message?.type === 'auditManifest') {
            runHermesMediaAction('audit', effectiveManifestPath);
            return;
        }
        if (message?.type === 'refreshManifest') {
            void openMediaWindowFromUri(vscode.Uri.file(effectiveManifestPath));
        }
    });
}
async function findDefaultManifestUri() {
    const env = globalThis?.process?.env;
    const localAppData = typeof env?.LOCALAPPDATA === 'string' ? env.LOCALAPPDATA : '';
    if (!localAppData) {
        return undefined;
    }
    const candidates = [
        `${localAppData}\\hermes\\media\\manifests\\private-client-glocal-smoke.json`,
        `${localAppData}\\hermes\\media\\manifests\\mp3-window-test.json`,
        `${localAppData}\\hermes\\media\\manifests\\media-window-sample.json`,
        `${localAppData}\\hermes\\media\\manifests\\smoke-media.json`,
    ];
    for (const filePath of candidates) {
        const uri = vscode.Uri.file(filePath);
        try {
            await vscode.workspace.fs.stat(uri);
            return uri;
        }
        catch {
            // Skip missing files and continue checking defaults.
        }
    }
    return undefined;
}
async function launchDefaultMediaWindow() {
    const defaultUri = await findDefaultManifestUri();
    if (!defaultUri) {
        return false;
    }
    try {
        await openMediaWindowFromUri(defaultUri);
        return true;
    }
    catch {
        return false;
    }
}
function buildPlayerManifestFromInput(inputPath, localAppData) {
    const now = new Date();
    const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
    const manifestPath = `${localAppData}\\hermes\\media\\manifests\\vscode-player-${stamp}.json`;
    const outputPath = `${localAppData}\\hermes\\media\\outputs\\vscode-player-${stamp}.mp3`;
    const payload = {
        action: 'vscode-vlc-ffmpeg-player',
        engine: 'ffmpeg',
        surface: 'æ://private client^glocal',
        runtime: 'ae://local^ollama',
        local_only: true,
        cloud: false,
        input_path: inputPath,
        output_path: outputPath,
        command: ['ffmpeg', '-y', '-i', inputPath, outputPath],
    };
    return { path: manifestPath, payload };
}
function renderMediaViewportHtml(manifest, manifestPath, previews = []) {
    const rawManifest = JSON.stringify(manifest, null, 2);
    const embeddedPreviewHtml = previews.length > 0
        ? previews.map((entry) => {
            const tag = entry.kind === 'audio'
                ? `<audio controls style="width:100%;"><source src="${escapeHtml(entry.uri)}" /></audio>`
                : `<video controls style="width:100%;max-height:360px;background:#000;"><source src="${escapeHtml(entry.uri)}" /></video>`;
            return `
          <div class="row" style="margin-top: 10px;">
            <div class="k">${escapeHtml(entry.label)}</div>
            ${tag}
          </div>
        `;
        }).join('')
        : '<div class="row"><span class="k">No local previewable media found for this manifest.</span></div>';
    const title = String(manifest?.action || 'Media Manifest');
    const engine = String(manifest?.engine || 'unknown');
    const memberToken = String(manifest?.member_token || '');
    const governance = String(manifest?.governance || 'none');
    const command = Array.isArray(manifest?.command) ? manifest.command.join(' ') : '';
    const manifestHash = String(manifest?.manifest_sha256 || '');
    const inputSha = String(manifest?.input_sha256 || '');
    return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Hermes Media Viewport</title>
    <style>
      :root { --bg:#050505; --panel:#111; --text:#D4AF37; --muted:#8b8b8b; }
      body { font-family: "Orbitron", "JetBrains Mono", monospace; margin: 0; padding: 16px; background: var(--bg); color: var(--text); }
      .card { background: var(--panel); border: 1px solid #222; border-radius: 6px; padding: 14px; margin-bottom: 12px; }
      h1 { margin: 0 0 10px; font-size: 18px; }
      h2 { margin: 0 0 8px; font-size: 14px; color: var(--muted); }
      .row { margin: 5px 0; }
      .k { color: var(--muted); }
      .v { color: var(--text); word-break: break-all; }
      pre { white-space: pre-wrap; word-break: break-word; margin: 0; color: #f0f0f0; }
      button { background: transparent; color: var(--text); border: 1px solid var(--text); border-radius: 6px; padding: 8px 10px; cursor: pointer; }
      button:hover { background: rgba(212,175,55,0.1); }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Hermes Media Viewport</h1>
      <div class="row"><span class="k">Action:</span> <span class="v">${escapeHtml(title)}</span></div>
      <div class="row"><span class="k">Engine:</span> <span class="v">${escapeHtml(engine)}</span></div>
      <div class="row"><span class="k">Member Token:</span> <span class="v">${escapeHtml(memberToken)}</span></div>
      <div class="row"><span class="k">Governance:</span> <span class="v">${escapeHtml(governance)}</span></div>
    </div>

    <div class="card">
      <h2>Execution</h2>
      <pre>${escapeHtml(command)}</pre>
    </div>

    <div class="card">
      <h2>Manifest</h2>
      <pre>${escapeHtml(rawManifest)}</pre>
    </div>

    <div class="card">
      <h2>Integrity</h2>
      <div class="row"><span class="k">Manifest SHA256:</span> <span class="v">${escapeHtml(manifestHash)}</span></div>
      <div class="row"><span class="k">Input SHA256:</span> <span class="v">${escapeHtml(inputSha)}</span></div>
    </div>
  </body>
</html>`;
}
function renderGoldShell(title, bodyHtml, opts) {
    const script = opts?.script ? `<script>${opts.script}</script>` : '';
    return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(title)}</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet" />
    <style>
      :root { --void:#050505; --panel:#0b0b0b; --gold:#D4AF37; --gold-glow:rgba(212,175,55,.32); --neon:#00ffa3; --ink:#e6e6e6; --muted:#8b8b8b; --border:rgba(212,175,55,.22); --border-hot:rgba(212,175,55,.5); }
      * { box-sizing: border-box; }
      body { font-family: 'JetBrains Mono', monospace; margin:0; padding:18px; background:var(--void); color:var(--ink); line-height:1.5; }
      body::before { content:''; position:fixed; inset:0; pointer-events:none; background:repeating-linear-gradient(transparent 0 2px, rgba(212,175,55,.018) 2px 4px); z-index:999; }
      .shell { max-width:880px; margin:0 auto; }
      h1 { font-family:'Orbitron'; font-weight:900; color:var(--gold); text-shadow:0 0 24px var(--gold-glow); font-size:20px; margin:0 0 4px; letter-spacing:1px; }
      h2 { font-family:'Orbitron'; font-weight:700; color:var(--gold); font-size:13px; letter-spacing:1.5px; text-transform:uppercase; margin:18px 0 8px; }
      .sub { color:var(--muted); font-size:11px; letter-spacing:1px; margin-bottom:14px; }
      .card { background:var(--panel); border:1px solid var(--border); border-radius:6px; padding:14px; margin-bottom:12px; box-shadow:0 0 32px rgba(212,175,55,.05); }
      .card.hot { border-color:var(--border-hot); }
      .row { margin:6px 0; display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }
      .k { color:var(--muted); font-size:12px; min-width:120px; }
      .v { color:var(--ink); word-break:break-all; }
      .v.gold { color:var(--gold); } .v.neon { color:var(--neon); }
      pre { white-space:pre-wrap; word-break:break-word; margin:0; color:#f0f0f0; font-size:12px; line-height:1.45; }
      a { color:var(--neon); text-decoration:none; border-bottom:1px dotted var(--neon); }
      a:hover { color:#fff; }
      button { font-family:'JetBrains Mono'; background:transparent; color:var(--gold); border:1px solid var(--gold); border-radius:6px; padding:9px 13px; cursor:pointer; font-size:12px; transition:.15s; letter-spacing:.5px; }
      button:hover { background:rgba(212,175,55,.12); box-shadow:0 0 16px var(--gold-glow); }
      .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:10px; }
      .pill { border:1px solid var(--border); border-radius:999px; padding:5px 12px; font-size:10px; color:var(--muted); letter-spacing:1px; text-transform:uppercase; }
      .pill.hot { border-color:var(--border-hot); color:var(--gold); }
      .pill.neon { border-color:rgba(0,255,163,.4); color:var(--neon); }
      .hash { text-align:center; font-family:'Orbitron'; font-weight:700; font-size:12px; margin-top:18px; background:linear-gradient(90deg,var(--gold),var(--neon),var(--gold)); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:2px; }
    </style>
  </head>
  <body>
    <div class="shell">
      <h1>${escapeHtml(title)}</h1>
      ${bodyHtml}
    </div>
    ${script}
  </body>
</html>`;
}
function renderReachyPanelHtml(repo) {
    const body = `
    <div class="sub">SOVEREIGN ROBOTIC CLERK · +æ://reachy</div>
    <div class="card hot">
      <div class="row"><span class="k">Repo</span><span class="v gold">${escapeHtml(repo)}</span></div>
      <div class="row"><span class="k">Primitive</span><span class="v neon">reachy</span></div>
      <div class="row"><span class="k">Status</span><span class="v neon">onboarded</span></div>
    </div>
    <div class="card">
      <h2>Actions</h2>
      <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <button id="requestProbe">Reachy Probe</button>
        <button id="requestMediaWindow">Open Media Window</button>
      </div>
    </div>
    <div class="hash">#hermiphicationisinevitable</div>`;
    const script = `const vscode=acquireVsCodeApi();
    document.getElementById('requestProbe')?.addEventListener('click',()=>vscode.postMessage({type:'requestProbe'}));
    document.getElementById('requestMediaWindow')?.addEventListener('click',()=>vscode.postMessage({type:'requestMediaWindow'}));`;
    return renderGoldShell('Remote Use: Reachy Primitive', body, { script });
}
function renderAgenticHtmlViewportHtml(templatePath) {
    try {
        return require('fs').readFileSync(templatePath, 'utf8');
    }
    catch {
        return renderGoldShell('Remote Use: Agentic HTML Viewport', `
      <div class="card hot">
        <p>Template not found at: <span class="v gold">${escapeHtml(templatePath)}</span></p>
      </div>
      <div class="hash">#hermiphicationisinevitable</div>`);
    }
}
function renderDaoBlueprintHtml(repo) {
    const path = require('path');
    const blueprintPath = path.join(repo, 'blueprints', 'laptop-as-dao.md');
    let markdown = '';
    try {
        markdown = require('fs').readFileSync(blueprintPath, 'utf8');
    }
    catch {
        markdown = `# DAO Blueprint Not Found\n\nExpected path: ${blueprintPath}`;
    }
    return renderGoldShell('Remote Use: DAO Blueprint', `
    <div class="sub">BLUEPRINT AS OPERATING AGREEMENT · +æ://blueprint</div>
    <div class="card">
      <div class="row"><span class="k">Source</span><span class="v gold">${escapeHtml(blueprintPath)}</span></div>
    </div>
    <div class="card hot">
      <pre>${escapeHtml(markdown)}</pre>
    </div>
    <div class="hash">#hermiphicationisinevitable</div>`);
}
function renderDaoSurfaceHtml() {
    let daoPath = 'C:\\æ\\agentic-entrepreneurship\\dao\\index.html';
    try {
        const configured = vscode.workspace.getConfiguration('remoteUse').get('daoSurfacePath', '');
        if (typeof configured === 'string' && configured.trim()) {
            daoPath = configured.trim();
        }
    }
    catch {
        // ignore config read errors and use default
    }
    let html = '';
    try {
        html = require('fs').readFileSync(daoPath, 'utf8');
    }
    catch {
        html = renderGoldShell('Remote Use: DAO Surface', `
      <div class="card hot">
        <p>Could not load DAO surface at: <span class="v gold">${escapeHtml(daoPath)}</span></p>
      </div>
      <div class="hash">#hermiphicationisinevitable</div>`);
    }
    return html;
}
function renderFactoryHtml(repo) {
    const local = findLocalTemplate(repo, [`${repo}/templates/factory.html`]);
    if (local)
        return local;
    try {
        const fs = require('fs');
        const p = require('path').join(__dirname, '..', 'templates', 'factory.html');
        if (fs.existsSync(p))
            return fs.readFileSync(p, 'utf8');
    }
    catch (e) { /* fall through */ }
    return `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Hermes Native · Factory</title></head><body>Sovereign factory surface unavailable.</body></html>`;
}
function renderComputerUseHtml() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Hermes Native · Computer Use</title>
<style>
  :root { --bg:#050505; --panel:#0a0a0f; --gold:#D4AF37; --text:#e6e6e6; --muted:#9a9a9a; --border:#1f1f1f; --neon:#00ffa3; --error:#ff7b72; }
  * { box-sizing: border-box; }
  body { margin:0; padding:18px; background:var(--bg); color:var(--text); font-family:'JetBrains Mono',ui-monospace,monospace; height:100vh; display:grid; grid-template-rows:auto 1fr auto; gap:12px; }
  .header { font-size:18px; font-weight:700; color:var(--gold); border-bottom:1px solid var(--border); padding-bottom:12px; }
  .sub { color:var(--muted); font-size:12px; }
  .shot { flex:1; border:1px solid var(--border); border-radius:10px; background:#000; min-height:0; }
  .log { background:#050508; border:1px solid var(--border); border-radius:10px; padding:10px; min-height:80px; font-size:11px; color:var(--muted); white-space:pre-wrap; max-height:160px; overflow:auto; }
  .row { display:flex; gap:10px; }
  button.primary { background:linear-gradient(135deg, rgba(212,175,55,0.15), rgba(0,255,163,0.08)); border:1px solid rgba(212,175,55,0.65); color:var(--gold); padding:10px 12px; border-radius:10px; font:inherit; font-size:12px; cursor:pointer; }
  .err { color:var(--error); }
</style>
</head>
<body>
<div class="header">Hermes Native · Computer Use <span class="sub">— bounded local desktop control</span></div>
<img class="shot" id="shot" alt="desktop capture"/>
<div class="log" id="log">Ready. Use capture / click / type from the mesh.</div>
<script>
const logEl = document.getElementById('log');
const shot = document.getElementById('shot');
const log = (t, err=false) => { const d = document.createElement('div'); d.className = err ? 'err' : ''; d.textContent = new Date().toLocaleTimeString() + ' ' + t; logEl.appendChild(d); logEl.scrollTop = logEl.scrollHeight; };
const vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
if (vscode) {
  window.addEventListener('message', (event) => {
    const m = event && event.data;
    if (!m || !m.command) return;
    if (m.command === 'remoteUse.computerUse.capture' && m.dataUrl) { shot.src = m.dataUrl; log('Captured desktop frame.'); }
    if (m.command === 'remoteUse.computerUse.log') { log(m.text || '', !!m.error); }
  });
  vscode.postMessage({ command: 'remoteUse.computerUse.ready' });
  log('Computer Use surface active.');
}
window.addEventListener('unhandledrejection', (e) => { log('Unhandled rejection: ' + (e.reason && e.reason.message ? e.reason.message : String(e.reason)), true); });
</script>
</body>
</html>`;
}
function renderHomeOS() {
    const repo = getHermesRepoPath();
    const fallbackHome = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"/>
<title>home://</title>
<style>
:root { --bg:#050505; --bg-panel:#0a0a0a; --gold:#D4AF37; --gold-60:rgba(212,175,55,0.6); --text:#e6e6e6; --muted:#8a8a8a; --border:#1a1a1a; --ff:'Orbitron','JetBrains Mono','Segoe UI',monospace; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; height: 100%; background: var(--bg); color: var(--text); font-family: var(--ff); }
body { padding: 24px; }
.header { display: flex; align-items: baseline; gap: 16px; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
.title { font-size: 18px; font-weight: 700; color: var(--gold); }
.subtitle { font-size: 12px; color: var(--muted); text-transform: lowercase; letter-spacing: 0.08em; }
.surfaces { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
button { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px; text-align: left; cursor: pointer; display: flex; flex-direction: column; gap: 6px; transition: border-color 0.2s; color: var(--text); font-family: var(--ff); font-size: 12px; }
button:hover { border-color: var(--gold-60); }
</style>
</head>
<body>
<div class="header"><div class="title">home://</div><div class="subtitle">agentic OS surface</div></div>
<div class="surfaces">
<button data-command="remoteUse.commandPrompt">terminal · Hermes terminal profile</button>
<button data-command="remoteUse.editor">editor · VS Code editor control</button>
<button data-command="remoteUse.files">files · Bounded filesystem primitive</button>
<button data-command="remoteUse.victus">victus · Victus machine vitals</button>
<button data-command="remoteUse.nvidia">nvidia · NVIDIA GPU C2</button>
<button data-command="remoteUse.vlc">vlc · VLC fleet command</button>
<button data-command="remoteUse.ffmpeg">ffmpeg · FFmpeg media pipeline</button>
<button data-command="remoteUse.qr">qr · QR-tagged HTML execution</button>
<button data-command="remoteUse.mesh">mesh · Bounded sovereign mesh</button>
<button data-command="remoteUse.agenticHtmlViewport">shell · agentic.html viewport</button>
<button data-command="remoteUse.htmlSurface">bundle · local HTML surfaces</button>
<button data-command="remoteUse.hermesNative">inference · Hermes Native · WebLLM WebGPU</button>
</div>
<script>
const vscode = acquireVsCodeApi();
document.querySelectorAll('button').forEach((btn) => {
  btn.addEventListener('click', () => vscode.postMessage({ command: btn.getAttribute('data-command') }));
});
</script>
</body>
</html>`;
    const defaultSuffix = 'templates/agentic.html';
    const fallbackSuffix = 'vscode-remote-use/templates/agentic-fallback.html';
    const candidateTails = repo ? [
        'templates/agentic.html',
        defaultSuffix,
        fallbackSuffix,
        'templates/omniverse.html',
        'templates/hermes-superagent.html',
    ] : [];
    let html = fallbackHome;
    if (repo) {
        for (const tail of candidateTails) {
            const candidate = `${repo.replace(/\/$/, '')}/${tail}`;
            try {
                if (require('fs').existsSync(candidate)) {
                    html = require('fs').readFileSync(candidate, 'utf8');
                    break;
                }
            }
            catch {
                // continue to next fallback
            }
        }
    }
    return html;
}
function renderWebLLM() {
    const repo = getHermesRepoPath();
    const fallbackTemplate = 'vscode-remote-use/templates/web-llm.html';
    const cleanRepo = (repo || '').replace(/[\\/]+$/, '');
    const templateCandidates = cleanRepo
        ? [
            cleanRepo + '/templates/web-llm.html',
            cleanRepo + '/vscode-remote-use/templates/web-llm.html',
            'C:/æ/hermes-fork/templates/web-llm.html',
            'C:/æ/hermes-fork/vscode-remote-use/templates/web-llm.html',
        ]
        : [fallbackTemplate];
    for (const candidate of templateCandidates) {
        try {
            if (require('fs').existsSync(candidate)) {
                return require('fs').readFileSync(candidate, 'utf8');
            }
        }
        catch {
            // continue to next fallback
        }
    }
    return fallbackHermesNativeHtml();
}
function findLocalTemplate(repo, candidates) {
    const cleanRepo = (repo || '').replace(/[\\/]+$/, '');
    const htmlCandidates = cleanRepo
        ? [
            cleanRepo + '/templates/web-llm.html',
            cleanRepo + '/vscode-remote-use/templates/web-llm.html',
            'C:/æ/hermes-fork/templates/web-llm.html',
            'C:/æ/hermes-fork/vscode-remote-use/templates/web-llm.html',
            ...candidates,
        ]
        : candidates;
    for (const candidate of htmlCandidates) {
        try {
            if (require('fs').existsSync(candidate)) {
                return require('fs').readFileSync(candidate, 'utf8');
            }
        }
        catch {
            // continue to next fallback
        }
    }
    return undefined;
}
function renderHermesNativeHtml(repo) {
    const local = findLocalTemplate(repo, []);
    if (local)
        return local;
    return fallbackHermesNativeHtml();
}
function renderWebLLMHtml(repo) {
    // Hermes Native · WebLLM WebGPU surface, framed as the æ:// agentic-language-chassis
    // local runtime. Distinct from the generic Hermes Native surface so the chassis
    // (and its dialects) is legible inside VS Code.
    const local = findLocalTemplate(repo, [`${repo}/templates/surfaces/webllm.html`]);
    if (local)
        return local;
    return fallbackWebLLMHtml();
}
function fallbackWebLLMHtml() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"/>
<meta name="theme-color" content="#050505"/>
<title>æ:// · Hermes Native WebLLM WebGPU</title>
<style>
  :root { --bg:#050505; --panel:#0a0a0f; --gold:#D4AF37; --gold-60:rgba(212,175,55,0.65); --text:#e6e6e6; --muted:#9a9a9a; --border:#1f1f1f; --neon:#00ffa3; --error:#ff7b72; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; min-height: 100%; background: var(--bg); color: var(--text); font-family: 'JetBrains Mono','Cascadia Mono',ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace; }
  body { padding: 18px; }
  .header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 8px; border-bottom: 1px solid var(--border); padding-bottom: 12px; }
  .title { font-size: 18px; font-weight: 700; color: var(--gold); letter-spacing: 0.06em; }
  .subtitle { font-size: 12px; color: var(--muted); letter-spacing: 0.12em; }
  .chassis { margin: 14px 0; padding: 12px 14px; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }
  .chassis .k { color: var(--gold); font-weight: 700; letter-spacing: 0.08em; font-size: 12px; }
  .chassis .d { color: var(--muted); font-size: 11px; margin-top: 4px; }
  .dialects { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-top: 12px; }
  .dialect { background: #060609; border: 1px solid var(--border); border-radius: 10px; padding: 10px; }
  .dialect .name { color: var(--gold); font-size: 12px; font-weight: 700; }
  .dialect .meta { color: var(--muted); font-size: 11px; margin-top: 4px; }
  .status { font-size: 11px; color: var(--neon); display: flex; align-items: center; gap: 6px; margin-top: 14px; }
  .status::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: var(--neon); box-shadow: 0 0 8px var(--neon); }
  .prompt { width: 100%; min-height: 96px; background: #060609; color: var(--text); border: 1px solid var(--border); border-radius: 10px; padding: 10px; font: inherit; font-size: 12px; margin-top: 14px; }
  .row { display: flex; gap: 10px; margin-top: 12px; }
  button.primary { background: linear-gradient(135deg, rgba(212,175,55,0.15), rgba(0,255,163,0.08)); border: 1px solid var(--gold-60); color: var(--gold); padding: 10px 12px; border-radius: 10px; font: inherit; font-size: 12px; cursor: pointer; }
  .log { margin-top: 14px; background: #050508; border: 1px solid var(--border); border-radius: 10px; padding: 10px; min-height: 64px; font-size: 11px; color: var(--muted); white-space: pre-wrap; }
  .err { color: var(--error); }
</style>
</head>
<body>
<div class="header"><div class="title">æ:// · Hermes Native</div><div class="subtitle">Agentic Language Chassis · WebLLM WebGPU</div></div>
<div class="chassis">
  <div class="k">æ:// — AGENTIC-LANGUAGE-CHASSIS</div>
  <div class="d">Sovereign namespace/runtime for agentic languages. Bare æ:// is the context router (aectx).</div>
  <div class="dialects">
    <div class="dialect"><div class="name">æ://basic</div><div class="meta">+bæsic:// · qc64 BASIC chassis (verified runtime)</div></div>
    <div class="dialect"><div class="name">æ://mech</div><div class="meta">mech-lang · reactive dataflow (spec grammar)</div></div>
    <div class="dialect"><div class="name">æ://glocal-agent</div><div class="meta">sovereign local agent · GPU-MCP</div></div>
    <div class="dialect"><div class="name">+æ://cc</div><div class="meta">command &amp; control surface</div></div>
  </div>
</div>
<div class="status" id="status">INITIALIZING WEBGPU</div>
<textarea class="prompt" id="prompt" placeholder="Prompt the local WebLLM runtime..."></textarea>
<div class="row"><button class="primary" id="run">RUN INFERENCE</button></div>
<div class="log" id="log">Awaiting user action...</div>
<script>
const vscode = acquireVsCodeApi();
const statusEl = document.getElementById('status');
const logEl = document.getElementById('log');
if (navigator.gpu) { statusEl.textContent = 'WEBGPU READY'; } else { statusEl.textContent = 'WEBGPU UNAVAILABLE'; statusEl.style.color = 'var(--error)'; }
document.getElementById('run')?.addEventListener('click', () => {
  const prompt = document.getElementById('prompt').value;
  logEl.textContent = 'dispatch ▸ ' + prompt;
  vscode.postMessage({ type: 'run', prompt });
});
</script>
</body>
</html>`;
}
function fallbackHermesNativeHtml() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"/>
<meta name="theme-color" content="#050505"/>
<title>Hermes Native · WebLLM WebGPU Runtime</title>
<style>
  :root { --bg:#050505; --panel:#0a0a0f; --gold:#D4AF37; --gold-60:rgba(212,175,55,0.65); --text:#e6e6e6; --muted:#9a9a9a; --border:#1f1f1f; --neon:#00ffa3; --error:#ff7b72; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; height: 100%; background: var(--bg); color: var(--text); font-family: 'JetBrains Mono','Cascadia Mono',ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace; }
  body { padding: 18px; }
  .header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 18px; border-bottom: 1px solid var(--border); padding-bottom: 12px; }
  .title { font-size: 18px; font-weight: 700; color: var(--gold); letter-spacing: 0.08em; }
  .subtitle { font-size: 12px; color: var(--muted); text-transform: lowercase; letter-spacing: 0.12em; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
  .name { font-size: 12px; font-weight: 700; color: var(--gold); letter-spacing: 0.08em; }
  .meta { font-size: 11px; color: var(--muted); }
  .status { font-size: 11px; color: var(--neon); display: flex; align-items: center; gap: 6px; }
  .status::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: var(--neon); box-shadow: 0 0 8px var(--neon); }
  .prompt { width: 100%; min-height: 96px; background: #060609; color: var(--text); border: 1px solid var(--border); border-radius: 10px; padding: 10px; font: inherit; font-size: 12px; }
  .row { display: flex; align-items: center; gap: 10px; justify-content: space-between; margin-top: 14px; }
  button.primary { background: linear-gradient(135deg, rgba(212,175,55,0.15), rgba(0,255,163,0.08)); border: 1px solid var(--gold-60); color: var(--gold); padding: 10px 12px; border-radius: 10px; font: inherit; font-size: 12px; cursor: pointer; }
  .log { margin-top: 14px; background: #050508; border: 1px solid var(--border); border-radius: 10px; padding: 10px; min-height: 72px; font-size: 11px; color: var(--muted); white-space: pre-wrap; }
  .err { color: var(--error); }
</style>
</head>
<body>
<div class="header"><div class="title">Hermes Native · WebLLM WebGPU Runtime</div><div class="subtitle">Sovereign industrial-grade local inference surface</div></div>
<div class="grid">
  <div class="card"><div class="name">RUNTIME</div><div class="meta">Hermes Native</div><div class="status" id="status">INITIALIZING</div></div>
  <div class="card"><div class="name">PRIMITIVE</div><div class="meta" id="capability">Detecting WebGPU...</div></div>
  <div class="card"><div class="name">LATENCY</div><div class="meta" id="latency">Awaiting first inference</div></div>
  <div class="card"><div class="name">RUNTIME</div><div class="meta" id="runtime">Local viewport</div></div>
</div>
<div class="grid">
  <div class="card"><div class="name">APPS</div><div class="meta" id="apps">Loading...</div></div>
  <div class="card"><div class="name">BRIDGE</div><div class="meta" id="bridge">Idle</div></div>
  <div class="card"><div class="name">SESSION</div><div class="meta" id="session">Local viewport</div></div>
  <div class="card"><div class="name">RUNNER</div><div class="meta" id="runner">Scaffold available</div></div>
</div>
<div class="row">
  <textarea class="prompt" id="prompt" placeholder="Prompt: summarize the sovereign runtime stack in 3 bullets."></textarea>
  <button class="primary" id="run">RUN INFERENCE</button>
</div>
<div class="log" id="log">Awaiting user action...</div>
<script>
const logEl = document.getElementById('log');
const statusEl = document.getElementById('status');
const capabilityEl = document.getElementById('capability');
const latencyEl = document.getElementById('latency');
const runtimeEl = document.getElementById('runtime');
const promptEl = document.getElementById('prompt');
const runBtn = document.getElementById('run');
const log = (text, err=false) => { const el = document.createElement('div'); el.className = err ? 'err' : ''; el.textContent = new Date().toLocaleTimeString() + ' ' + text; logEl.appendChild(el); logEl.scrollTop = logEl.scrollHeight; };
const setStatus = (text, err=false) => { statusEl.className = err ? 'status err' : 'status'; statusEl.style.color = err ? '#ff7b72' : '#00ffa3'; statusEl.textContent = text; };
const detect = async () => {
  try {
    if (!navigator.gpu) throw new Error('navigator.gpu is unavailable');
    const adapter = await navigator.gpu.requestAdapter();
    if (!adapter) throw new Error('No GPU adapter found');
    capabilityEl.textContent = 'WebGPU runtime ready';
    runtimeEl.textContent = 'WebGPU viewport';
    setStatus('READY');
    log('WebGPU detect: adapter ready');
  } catch (e) {
    capabilityEl.textContent = 'WebGPU fallback required';
    runtimeEl.textContent = 'Fallback viewport';
    setStatus('FALLBACK', true);
    log('WebGPU detect failed: ' + e.message, true);
  }
};
let engine = null;
let loading = false;
const modelId = 'Qwen/Qwen3-0.6B';
const initEngine = async () => {
  if (engine) return engine;
  if (loading) return null;
  loading = true;
  setStatus('LOADING');
  log('WebLLM engine init: ' + modelId);
  try {
    const webllm = await import('https://esm.run/@mlc-ai/web-llm');
    engine = await webllm.CreateMLCEngine(modelId, {
      initProgressCallback: (p) => {
        const text = (p && (p.text || p.progress != null)) ? (p.progress != null ? Math.round(p.progress * 100) + '%' : p.text) : 'Loading...';
        log('Engine: ' + text);
      }
    });
    setStatus('READY');
    log('WebLLM engine ready');
    loading = false;
    return engine;
  } catch (e) {
    setStatus('ENGINE_FAILED', true);
    log('WebLLM init failed: ' + (e && e.message ? e.message : String(e)), true);
    loading = false;
    return null;
  }
};
const runInference = async () => {
  const text = (promptEl.value || '').trim();
  const ready = await initEngine();
  if (!ready) {
    setStatus('INFERENCE_FAILED', true);
    return;
  }
  log('Inference requested...');
  runBtn.disabled = true;
  runBtn.textContent = 'RUNNING...';
  const start = performance.now();
  try {
    const chat = await engine.chat.completions.create({
      messages: [
        { role: 'system', content: 'You are a concise sovereign runtime assistant.' },
        { role: 'user', content: text || 'Summarize the stack in 3 bullets.' }
      ],
      max_tokens: 256,
      temperature: 0.3
    });
    const reply = (chat && chat.choices && chat.choices[0] && chat.choices[0].message) ? chat.choices[0].message.content || '' : '';
    const elapsed = Math.max(1, Math.round(performance.now() - start));
    latencyEl.textContent = elapsed + 'ms';
    log('Reply:\n' + reply);
  } catch (e) {
    log('Inference failed: ' + (e && e.message ? e.message : String(e)), true);
    setStatus('INFERENCE_FAILED', true);
  }
  runBtn.disabled = false;
  runBtn.textContent = 'RUN INFERENCE';
};
const bridgeReady = typeof window !== 'undefined' && typeof acquireVsCodeApi === 'undefined';
const discoverApps = async () => {
  const appsEl = document.getElementById('apps');
  const runnerEl = document.getElementById('runner');
  try {
    const response = await fetch('vscode-resource:/.manifest', {headers: {'Cache-Control':'no-store'}}).catch(() => null);
    appsEl.textContent = 'NX';
    runnerEl.textContent = 'Scaffold ready';
  } catch (e) {
    appsEl.textContent = 'Scaffold only';
    runnerEl.textContent = 'Scaffold ready';
  }
};
const runAppNow = async () => {
  const bridgeEl = document.getElementById('bridge');
  const sessionEl = document.getElementById('session');
  bridgeEl.textContent = 'Running...';
  sessionEl.textContent = 'App session';
  try {
    const result = await runInference();
    bridgeEl.textContent = 'Idle';
    sessionEl.textContent = 'Local viewport';
    return result;
  } catch (e) {
    bridgeEl.textContent = 'Error: ' + (e && e.message ? e.message : String(e));
    bridgeEl.style.color = '#ff7b72';
    sessionEl.textContent = 'Local viewport';
    throw e;
  }
};
detect();
discoverApps().catch(() => {});
runBtn.addEventListener('click', async () => { try { await runAppNow(); } catch { /* logged in UI */ } });
promptEl.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); runInference(); } });
const vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : null;
if (vscode) {
  log('VS Code webview context acquired');
  window.hermesNative = { runInference };
  window.addEventListener('message', (event) => {
    const message = event && event.data;
    if (!message || !message.command) return;
    if (message.command === 'remoteUse.hermesNative') runInference();
  });
}
window.addEventListener('unhandledrejection', (event) => {
  const reason = event && event.reason;
  log('Unhandled rejection: ' + (reason && reason.message ? reason.message : String(reason)), true);
});
</script>
</body>
</html>
`;
}
function openHtmlSurface(title, path) {
    try {
        const html = require('fs').readFileSync(path, 'utf8');
        const baseDir = require('path').dirname(path);
        const panel = vscode.window.createWebviewPanel('remoteUseHtmlSurface', `Remote Use: ${title}`, vscode.ViewColumn.Beside, { enableScripts: true, localResourceRoots: [vscode.Uri.file(baseDir)] });
        panel.webview.html = html;
        vscode.window.showInformationMessage(`Remote Use: opened ${title}`);
    }
    catch {
        vscode.window.showWarningMessage(`Remote Use: HTML surface not found at ${path}`);
    }
}
function ensureBrain() {
    // Returns true if the local ollama brain is already serving on :11434.
    // If not, kick off `ollama serve` in a detached terminal so the offline
    // brain (+æ^glocal local model) comes up automatically on extension activate.
    const http = require('http');
    const { execSync } = require('child_process');
    try {
        execSync('curl -s -m 3 -o nul -w "%{http_code}" http://localhost:11434/api/tags', { stdio: ['ignore', 'pipe', 'ignore'] });
        return true;
    }
    catch {
        // not up -> start it (best-effort; user may not have ollama installed)
        try {
            const term = vscode.window.createTerminal('Local Brain (ollama)');
            term.sendText('ollama serve');
            term.hide();
            vscode.window.showInformationMessage('Remote Use: starting local brain (ollama serve) — offline model coming online');
        }
        catch {
            vscode.window.showWarningMessage('Remote Use: could not auto-start ollama — run `ollama serve` manually');
        }
        return false;
    }
}
const brainCmd = vscode.commands.registerCommand('remoteUse.brain', async () => {
    if (ensureBrain()) {
        vscode.window.showInformationMessage('Remote Use: local brain is online at http://localhost:11434');
    }
});
const CONDUCTOR_SURFACES = [
    { id: 'hub', glyph: 'æ', name: 'SOVEREIGN HUB', url: 'https://myaelmendez.github.io/', tag: 'mesh · fleet · cuda · secrets' },
    { id: 'aeaeae', glyph: 'æææ', name: 'BRANDED TOWER', url: 'https://myaelmendez.github.io/aaa-protocol.html', tag: 'æææ://neuromitosis · æææ://cuda' },
    { id: 'glocal', glyph: '◈', name: 'GLOCAL MESH', url: 'https://myaelmendez.github.io/glocal-mesh.html', tag: 'pc://mesh/<cap>/local' },
    { id: 'cuda', glyph: 'n', name: 'GLOCAL CUDA', url: 'https://myaelmendez.github.io/glocal-cuda-mesh.html', tag: 'RTX 3050 · cloud burst' },
    { id: 'rails', glyph: '$', name: 'RAILS · >_$', url: 'https://myaelmendez.github.io/rails.html', tag: 'Doola affiliate · zero custody' },
    { id: 'agentic', glyph: 'Æ', name: '#STARTABUSINESS', url: 'https://myaelmendez.github.io/agentic.html', tag: 'DAOLLC · #250' },
];
function renderConductorHtml() {
    const cards = CONDUCTOR_SURFACES.map((s) => `
    <div class="card hot" data-open="${escapeHtml(s.url)}" style="cursor:pointer;">
      <div class="row"><span class="v gold" style="font-family:'Orbitron';font-weight:900;font-size:16px;">${escapeHtml(s.glyph)}</span><span class="v gold" style="font-family:'Orbitron';font-weight:700;">${escapeHtml(s.name)}</span></div>
      <div class="row"><span class="v neon">${escapeHtml(s.tag)}</span></div>
      <div class="row"><span class="k">open</span><span class="v" style="color:var(--neon);">${escapeHtml(s.url)}</span></div>
    </div>`).join('');
    const body = `
    <div class="sub">HERMES AGENT CONDUCTOR · ONE SPINE, FOUR PRIMITIVES</div>
    <div class="grid" id="grid">${cards}</div>
    <div class="card">
      <h2>Stack</h2>
      <div class="row"><span class="k">&gt;_æ:</span><span class="v">sovereign protocol · +æ://mesh · +æ://secrets</span></div>
      <div class="row"><span class="k">&gt;_h:</span><span class="v">Hermes Agent conductor (SchemeDispatcher)</span></div>
      <div class="row"><span class="k">&gt;_n:</span><span class="v">NemoClaw · GLOCAL CUDA (RTX 3050)</span></div>
      <div class="row"><span class="k">&gt;_$:</span><span class="v">Doola affiliate · zero custody</span></div>
    </div>
    <div class="hash">#hermiphicationisinevitable</div>`;
    const script = `document.getElementById('grid')?.addEventListener('click',(e)=>{const c=e.target.closest('[data-open]');if(c)window.open(c.getAttribute('data-open'),'_blank');});`;
    return renderGoldShell('Remote Use: Conductor', body, { script });
}
function activate(context) {
    ensureBrain();
    const captureCmd = vscode.commands.registerCommand('remoteUse.capture', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showInformationMessage('Remote Use: no active text editor to capture');
            return;
        }
        const text = editor.document.getText();
        const selection = editor.selection;
        const path = editor.document.uri.toString();
        const surface = {
            kind: 'remote_user_capture',
            path,
            selection: `${selection.start.line}:${selection.start.character}-${selection.end.line}:${selection.end.character}`,
            length: text.length,
            preview: text.slice(0, 2000),
        };
        await vscode.env.clipboard.writeText(JSON.stringify(surface, null, 2));
        vscode.window.showInformationMessage(`Remote Use: captured ${surface.length} chars`);
    });
    const runTaskCmd = vscode.commands.registerCommand('remoteUse.runTask', async () => {
        const repo = getHermesRepoPath();
        const options = { cwd: repo };
        const definition = { type: 'remoteUse', task: 'run' };
        const task = new vscode.Task(definition, vscode.TaskScope.Workspace, 'Hermes Task', 'RemoteUse', new vscode.ShellExecution('hermes', ['hello'], options));
        await vscode.tasks.executeTask(task);
        vscode.window.showInformationMessage('Remote Use: dispatched Hermes task');
    });
    const chatCmd = vscode.commands.registerCommand('remoteUse.chat', async () => {
        await vscode.window.showInputBox({ placeHolder: 'Say something to Hermes...' }).then(async (value) => {
            if (!value) {
                return;
            }
            const terminal = vscode.window.createTerminal('Hermes Chat');
            terminal.sendText(`hermes chat "${value.replace(/"/g, '\\"')}"`);
            terminal.show();
        });
    });
    const mediaWindowCmd = vscode.commands.registerCommand('remoteUse.mediaWindow', async () => {
        const repo = getHermesRepoPath();
        const knownManifestCandidates = [
            `${repo}/media/vlc_manifest.json`,
            `${repo}/media/ffmpeg_manifest.json`,
        ];
        const knownMediaCandidates = [
            `${repo}/media/videos/private_client_super_agent_computer_use/out/private_client_super_agent_computer_use_draft.mp4`,
            `${repo}/media/videos/private_client_super_agent_computer_use/480p15/Scene0_Origin.mp4`,
            `${repo}/media/videos/private_client_super_agent_computer_use/480p15/Scene5_EndCard.mp4`,
        ];
        const foundManifest = knownManifestCandidates.find((p) => require('fs').existsSync(p));
        const foundMedia = knownMediaCandidates.find((p) => require('fs').existsSync(p));
        if (foundManifest) {
            try {
                const manifest = require(foundManifest);
                const manifestUri = vscode.Uri.file(foundManifest);
                await openMediaWindowFromManifest(manifest, manifestUri.fsPath);
                return;
            }
            catch {
                // fall through to media/webview fallback
            }
        }
        if (foundMedia) {
            const fallback = {
                action: 'vscode-player-fallback',
                input_path: foundMedia,
                output_path: foundMedia,
                engine: 'vscode-webview',
            };
            await openMediaWindowFromManifest(fallback, foundMedia);
            return;
        }
        const defaultUri = await findDefaultManifestUri();
        if (defaultUri) {
            await openMediaWindowFromUri(defaultUri);
            return;
        }
        vscode.window.showWarningMessage('Remote Use: media window unavailable; no manifest or media file found.');
    });
    const mediaOpenVlcCmd = vscode.commands.registerCommand('remoteUse.mediaOpenVlc', async () => {
        const picked = await vscode.window.showOpenDialog({
            canSelectMany: false,
            canSelectFiles: true,
            canSelectFolders: false,
            filters: { 'JSON': ['json'] },
            openLabel: 'Select Manifest For VLC',
        });
        if (!picked || picked.length === 0) {
            return;
        }
        try {
            const manifest = await readManifest(picked[0]);
            const inputPath = String(manifest?.input_path || '');
            if (!inputPath) {
                vscode.window.showErrorMessage('Manifest has no input_path for VLC playback.');
                return;
            }
            openInVlc(inputPath);
        }
        catch {
            vscode.window.showErrorMessage('Selected file is not a valid media manifest.');
        }
    });
    const mediaRunManifestCmd = vscode.commands.registerCommand('remoteUse.mediaRunManifest', async () => {
        const repo = getHermesRepoPath();
        const candidates = [`${repo}/media/vlc_manifest.json`, `${repo}/media/ffmpeg_manifest.json`];
        for (const candidate of candidates) {
            if (require('fs').existsSync(candidate)) {
                const manifest = require(candidate);
                vscode.window.showInformationMessage(`Remote Use: manifest loaded: ${manifest.manifest || candidate}`);
                return;
            }
        }
        vscode.window.showWarningMessage('Remote Use: no manifest found');
    });
    const mediaPlayerCmd = vscode.commands.registerCommand('remoteUse.mediaPlayer', async () => {
        await vscode.window.showQuickPick(['vlc', 'ffmpeg', 'omxplayer'], { placeHolder: 'Select media runtime' }).then((choice) => {
            if (!choice) {
                return;
            }
            const terminal = vscode.window.createTerminal(`Remote Use: ${choice}`);
            terminal.sendText(`${choice} --version`);
            terminal.show();
        });
    });
    const mediaCoevolveCmd = vscode.commands.registerCommand('remoteUse.mediaCoevolve', async () => {
        const repo = getHermesRepoPath();
        const goal = await vscode.window.showInputBox({ placeHolder: 'optimize for mobile shortform' });
        if (!goal) {
            return;
        }
        const terminal = vscode.window.createTerminal('Remote Use: Coevolve');
        terminal.sendText(`Set-Location ${toPowerShellSingleQuoted(repo)}; hermes coevolve --target=${goal}`);
        terminal.show();
    });
    const reachyProbeCmd = vscode.commands.registerCommand('remoteUse.reachyProbe', async () => {
        const repo = getHermesRepoPath();
        const candidates = [`${repo}/tools/reachy/reachy_probe.py`, `${repo}/tools/reachy_operator_bridge.py`];
        let cmd = '';
        for (const script of candidates) {
            if (require('fs').existsSync(script)) {
                cmd = `python "${script}" probe`;
                break;
            }
        }
        if (!cmd) {
            cmd = 'echo "Reachy primitive onboarded; driver/runtime contact not yet configured."';
        }
        const terminal = vscode.window.createTerminal('Remote Use: Reachy Probe');
        terminal.sendText(`Set-Location ${toPowerShellSingleQuoted(repo)}; ${cmd}`);
        terminal.show();
    });
    const reachyPanelCmd = vscode.commands.registerCommand('remoteUse.reachyPanel', async () => {
        const repo = getHermesRepoPath();
        const panel = vscode.window.createWebviewPanel('remoteUseReachyPanel', 'Remote Use: Reachy Primitive', vscode.ViewColumn.Beside, { enableScripts: true });
        panel.webview.html = renderReachyPanelHtml(repo);
        panel.webview.onDidReceiveMessage(async (message) => {
            if (message?.type === 'requestProbe') {
                await vscode.commands.executeCommand('remoteUse.reachyProbe');
            }
            if (message?.type === 'requestMediaWindow') {
                await vscode.commands.executeCommand('remoteUse.mediaWindow');
            }
        });
    });
    const agenticHtmlViewportCmd = vscode.commands.registerCommand('remoteUse.agenticHtmlViewport', async () => {
        const repo = getHermesRepoPath();
        const templatePath = `${repo}/templates/agentic.html`;
        const panel = vscode.window.createWebviewPanel('remoteUseAgenticHtmlViewport', 'Remote Use: Agentic HTML Viewport', vscode.ViewColumn.Beside, { enableScripts: true, localResourceRoots: [vscode.Uri.file(`${repo}/templates`)] });
        panel.webview.html = renderAgenticHtmlViewportHtml(templatePath);
    });
    const daoBlueprintCmd = vscode.commands.registerCommand('remoteUse.daoBlueprint', async () => {
        const repo = getHermesRepoPath();
        const panel = vscode.window.createWebviewPanel('remoteUseDaoBlueprint', 'Remote Use: DAO Blueprint', vscode.ViewColumn.Beside, { enableScripts: false });
        panel.webview.html = renderDaoBlueprintHtml(repo);
    });
    const daoSurfaceCmd = vscode.commands.registerCommand('remoteUse.daoSurface', async () => {
        const panel = vscode.window.createWebviewPanel('remoteUseDaoSurface', 'Remote Use: DAO Surface', vscode.ViewColumn.One, { enableScripts: true });
        panel.webview.html = renderDaoSurfaceHtml();
    });
    const hermesNativeCmd = vscode.commands.registerCommand('remoteUse.hermesNative', async () => {
        const repo = getHermesRepoPath();
        const panel = vscode.window.createWebviewPanel('remoteUseHermesNative', 'Remote Use: Hermes Native', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
        panel.webview.html = renderHermesNativeHtml(repo);
    });
    const webLLMCmd = vscode.commands.registerCommand('remoteUse.webLLM', async () => {
        const repo = getHermesRepoPath();
        const panel = vscode.window.createWebviewPanel('remoteUseWebLLM', 'Remote Use: Hermes Native · WebLLM WebGPU', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
        panel.webview.html = renderWebLLMHtml(repo);
    });
    const factoryCmd = vscode.commands.registerCommand('remoteUse.factory', async () => {
        const repo = getHermesRepoPath();
        const panel = vscode.window.createWebviewPanel('remoteUseFactory', 'Remote Use: Hermes Native Factory', vscode.ViewColumn.Beside, { enableScripts: true, retainContextWhenHidden: true });
        panel.webview.html = renderFactoryHtml(repo);
        panel.webview.onDidReceiveMessage(async (message) => {
            if (message?.command === 'remoteUse.factory.write') {
                const fs = require('fs');
                const path = require('path');
                const outDir = path.join(repo, 'site', 'generated');
                try {
                    fs.mkdirSync(outDir, { recursive: true });
                    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
                    const file = path.join(outDir, `surface-${stamp}.html`);
                    fs.writeFileSync(file, message.code || '', 'utf8');
                    vscode.window.showInformationMessage(`Remote Use: wrote ${path.basename(file)}`);
                }
                catch (e) {
                    vscode.window.showErrorMessage('Remote Use: factory write failed: ' + (e && e.message ? e.message : String(e)));
                }
            }
        });
    });
    const computerUseCmd = vscode.commands.registerCommand('remoteUse.computerUse', async () => {
        const panel = vscode.window.createWebviewPanel('remoteUseComputerUse', 'Remote Use: Computer Use', vscode.ViewColumn.Beside, { enableScripts: true, retainContextWhenHidden: true });
        panel.webview.html = renderComputerUseHtml();
        panel.webview.onDidReceiveMessage(async (message) => {
            if (message?.command === 'remoteUse.computerUse.ready') {
                vscode.window.showInformationMessage('Remote Use: Computer Use surface ready (cua-driver drives desktop in background).');
            }
        });
    });
    const surfacesHubCmd = vscode.commands.registerCommand('remoteUse.surfaces', async () => {
        const repo = getHermesRepoPath();
        const hub = `${repo}/templates/surfaces/index.html`;
        const panel = vscode.window.createWebviewPanel('remoteUseSurfaces', 'Remote Use: Local Surface System', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true, localResourceRoots: [vscode.Uri.file(`${repo}/templates/surfaces`), vscode.Uri.file(`${repo}/templates`), vscode.Uri.file('C:/æ/site'), vscode.Uri.file('C:/Users/yaelm/OneDrive/BEFORE 2023/Desktop/Y-L.com')] });
        // strip file:// scheme from embedded surface paths so the webview can convert them via asWebviewUri
        const fs = require('fs');
        let html = fs.readFileSync(hub, 'utf8').replace(/file:\/\/\//g, '').replace(/file:\/\//g, '');
        panel.webview.html = html;
        panel.webview.onDidReceiveMessage(async (message) => {
            const cmd = message?.command || '';
            if (cmd === 'remoteUse.surfaces.uri') {
                const p = String(message.path || '').replace(/^file:\/\/\/?/, '').replace(/\\/g, '/');
                try {
                    const uri = panel.webview.asWebviewUri(vscode.Uri.file(p));
                    panel.webview.postMessage({ command: 'remoteUse.surfaces.uri', id: message.id, uri: uri.toString() });
                }
                catch (e) {
                    panel.webview.postMessage({ command: 'remoteUse.surfaces.uri', id: message.id, uri: '', error: String(e) });
                }
            }
            else if (cmd === 'remoteUse.surfaces.openExternal') {
                const p = String(message.path || '').replace(/^file:\/\/\/?/, '').replace(/\\/g, '/');
                try {
                    await vscode.env.openExternal(vscode.Uri.file(p));
                }
                catch (e) { /* ignore */ }
            }
        });
    });
    const htmlSurfaceCmd = vscode.commands.registerCommand('remoteUse.htmlSurface', async () => {
        await vscode.commands.executeCommand('remoteUse.surfaces');
    });
    const nvidiaCmd = vscode.commands.registerCommand('remoteUse.nvidia', async () => {
        const repo = getHermesRepoPath();
        const hub = `${repo}/templates/surfaces/nvidia-tiles.html`;
        const panel = vscode.window.createWebviewPanel('remoteUseNvidia', 'Remote Use: NVIDIA Compute Surface', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true, localResourceRoots: [vscode.Uri.file(`${repo}/templates/surfaces`)] });
        panel.webview.html = require('fs').readFileSync(hub, 'utf8');
        panel.webview.onDidReceiveMessage(async (message) => {
            const action = message?.action || '';
            const { exec } = require('child_process');
            const run = (cmd) => new Promise((res) => exec(cmd, { maxBuffer: 1024 * 1024 }, (e, o, err) => res((e ? err : o) || '')));
            if (action === 'smi') {
                const out = await run('nvidia-smi --query-gpu=name,driver_version,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits');
                const parts = out.split(',').map((s) => s.trim());
                if (parts.length >= 6) {
                    const usedMib = parseFloat(parts[2]);
                    const totalMib = parseFloat(parts[3]);
                    panel.webview.postMessage({ command: 'remoteUse.nvidia', action: 'smi', data: {
                            name: parts[0], driver: parts[1], memory_used: usedMib * 1024 * 1024, memory_total: totalMib * 1024 * 1024,
                            memory_used_mib: usedMib, memory_total_mib: totalMib,
                            utilization_gpu: parseFloat(parts[4]), temperature_gpu: parseFloat(parts[5])
                        } });
                }
            }
            else if (action === 'compile') {
                const kernel = (message?.kernel || 'matmul');
                const src = `extern "C" __global__ void ${kernel}(float* a, float* b, float* c, int n){ int i=blockIdx.x*blockDim.x+threadIdx.x; if(i<n*n){ float s=0; for(int k=0;k<n;k++) s+=a[i/n*n+k]*b[k*n+i%n]; c[i]=s; } }`;
                const tmp = require('path').join(require('os').tmpdir(), `${kernel}.cu`);
                require('fs').writeFileSync(tmp, src);
                const compileOut = await run(`nvcc "${tmp}" -o "${require('path').join(require('os').tmpdir(), kernel)}" 2>&1`);
                panel.webview.postMessage({ command: 'remoteUse.nvidia', action: 'compile', data: { kernel, ok: compileOut.trim().length === 0, output: compileOut.slice(0, 400) } });
            }
            else if (action === 'procs') {
                const out = await run('nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits');
                const procs = out.split('\n').filter(Boolean).map((l) => { const p = l.split(',').map((s) => s.trim()); return { pid: p[0], name: p[1], used_memory: parseFloat(p[2]) * 1024 * 1024 }; });
                panel.webview.postMessage({ command: 'remoteUse.nvidia', action: 'procs', data: procs });
            }
            else if (action === 'torch') {
                let torch = false, version = '';
                try {
                    const r = require('child_process').execSync('python -c "import torch;print(torch.__version__)"', { encoding: 'utf8' });
                    version = r.trim();
                    torch = true;
                }
                catch (e) { /* not installed */ }
                panel.webview.postMessage({ command: 'remoteUse.nvidia', action: 'torch', data: { torch, version } });
            }
        });
    });
    const gpuAgentCmd = vscode.commands.registerCommand('remoteUse.gpuAgent', async () => {
        const repo = getHermesRepoPath();
        const agent = require('path').join(repo, 'templates', 'surfaces', 'gpu_agent.py');
        const terminal = vscode.window.createTerminal('GPU-Driven Agent');
        terminal.sendText(`python "${agent}" "Probe the GPU, then compile and run a CUDA matmul kernel, and report what happened."`);
        terminal.show();
    });
    const commandPromptCmd = vscode.commands.registerCommand('remoteUse.commandPrompt', async () => {
        const repo = getHermesRepoPath();
        const psProfilePath = require('path').join(repo, 'shell', '_commandPrompt.ps1');
        const terminal = vscode.window.createTerminal('commandprompt.ai');
        terminal.sendText(`Set-Location ${toPowerShellSingleQuoted(repo)}; if (Test-Path ${toPowerShellSingleQuoted(psProfilePath)}) { . ${toPowerShellSingleQuoted(psProfilePath)} }; $env:HERMES_REPO=${toPowerShellSingleQuoted(repo)}`);
        terminal.show();
    });
    const homeOSCmd = vscode.commands.registerCommand('remoteUse.homeOS', async () => {
        const panel = vscode.window.createWebviewPanel('remoteUseHomeOS', 'Remote Use: home://', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
        panel.webview.html = renderHomeOS();
        panel.webview.onDidReceiveMessage(async (message) => {
            if (!message?.command) {
                return;
            }
            switch (message.command) {
                case 'remoteUse.commandPrompt':
                    await vscode.commands.executeCommand('remoteUse.commandPrompt');
                    break;
                case 'remoteUse.editor': {
                    const repo = getHermesRepoPath();
                    await vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(repo), true);
                    break;
                }
                case 'remoteUse.files': {
                    const repo = getHermesRepoPath();
                    await vscode.env.openExternal(vscode.Uri.file(repo));
                    break;
                }
                case 'remoteUse.victus': {
                    const terminal = vscode.window.createTerminal('Victus');
                    terminal.sendText(`Set-Location ${toPowerShellSingleQuoted(getHermesRepoPath())}; hermes conductor +æ://victus`);
                    terminal.show();
                    break;
                }
                case 'remoteUse.nvidia': {
                    const terminal = vscode.window.createTerminal('NVIDIA');
                    terminal.sendText(`Set-Location ${toPowerShellSingleQuoted(getHermesRepoPath())}; hermes conductor NVIDIA://status`);
                    terminal.show();
                    break;
                }
                case 'remoteUse.vlc':
                    await vscode.commands.executeCommand('remoteUse.mediaOpenVlc');
                    break;
                case 'remoteUse.ffmpeg': {
                    const terminal = vscode.window.createTerminal('FFmpeg');
                    terminal.sendText('ffmpeg -version');
                    terminal.show();
                    break;
                }
                case 'remoteUse.qr': {
                    const input = await vscode.window.showInputBox({ placeHolder: '<html>...</html>' });
                    if (input) {
                        await vscode.commands.executeCommand('remoteUse.commandPrompt');
                        const terminal = vscode.window.activeTerminal;
                        terminal?.sendText(`hermes conductor +æ://qrcode payload ${toPowerShellSingleQuoted(input)}`);
                    }
                    break;
                }
                case 'remoteUse.mesh':
                    await vscode.window.showInformationMessage('Mesh surface: pc://mesh/victus/local');
                    break;
                case 'remoteUse.webLLM':
                    await vscode.commands.executeCommand('remoteUse.webLLM');
                    break;
                default:
                    if (typeof message.command === 'string' && message.command.startsWith('remoteUse.')) {
                        await vscode.commands.executeCommand(message.command);
                    }
                    break;
            }
        });
    });
    const conductorCmd = vscode.commands.registerCommand('remoteUse.conductor', async () => {
        const panel = vscode.window.createWebviewPanel('remoteUseConductor', 'Remote Use: Conductor', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
        panel.webview.html = renderConductorHtml();
    });
    context.subscriptions.push(captureCmd, runTaskCmd, chatCmd, mediaWindowCmd, mediaOpenVlcCmd, mediaRunManifestCmd, mediaPlayerCmd, mediaCoevolveCmd, reachyProbeCmd, reachyPanelCmd, agenticHtmlViewportCmd, daoBlueprintCmd, daoSurfaceCmd, hermesNativeCmd, webLLMCmd, factoryCmd, computerUseCmd, htmlSurfaceCmd, surfacesHubCmd, nvidiaCmd, gpuAgentCmd, commandPromptCmd, homeOSCmd, conductorCmd, brainCmd);
    void launchDefaultMediaWindow();
}
function deactivate() {
    // Cleanup/noop boundary for future extension state.
}
//# sourceMappingURL=extension.js.map