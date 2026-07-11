Param()
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$base = (Resolve-Path (Join-Path $scriptDir '..')).Path
$vsixFiles = @(Get-ChildItem -LiteralPath $base -Filter 'vscode-remote-use-*.vsix' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
if (-not $vsixFiles) {
    Write-Host "No VSIX found in: $base"
    Write-Host 'Run: cd vscode-remote-use; npm run compile; npx vsce package'
    exit 1
}
$vsix = $vsixFiles[0].FullName

$codeCli = $null
$codePaths = @(
    (Get-Command code -ErrorAction SilentlyContinue).Source,
    "${env:ProgramFiles}\Microsoft VS Code\bin\code.cmd",
    "${env:ProgramFiles(x86)}\Microsoft VS Code\bin\code.cmd",
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"
)
foreach ($p in $codePaths) {
    if ($p -and (Test-Path -LiteralPath $p)) {
        $codeCli = $p
        break
    }
}

if (-not $codeCli) {
    Write-Host "VS Code CLI not found. Install manually from VSIX path:"
    Write-Host $vsix
    exit 2
}

Write-Host "Using VS Code CLI: $codeCli"
Write-Host "Installing Hermes Agent VS Code surface from: $vsix"

$installArgs = @('--install-extension', $vsix, '--force')
& $codeCli @installArgs
$rc = $LASTEXITCODE
if ($rc -eq 0) {
    Write-Host 'Install complete.'
    exit 0
}
Write-Host "VS Code install returned $rc"
Write-Host "VSIX path: $vsix"
exit $rc
