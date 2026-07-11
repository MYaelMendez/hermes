# Hermes commandprompt.ai PowerShell profile
# Lightweight prelude for VS Code / local terminal.

$ErrorActionPreference = 'SilentlyContinue'

$repo = 'C:\æ\hermes-fork'
if ($env:HERMES_REPO) {
    $repo = $env:HERMES_REPO
}

$HERMES_DEFAULT_ARGS = '--repl'

function prompt {
    $id = 'cp'
    Write-Host -NoNewline ('>' + '_' + $id + ': ')
    return ' '
}

try {
    $env:HERMES_REPO = $repo
    $env:Path = ($env:Path.Split(';') + @($repo, Join-Path $repo 'hermes_cli\bin') | Sort-Object -Unique) -join ';'
} catch {
    # continue without path mutation
}

$Host.UI.RawUI.WindowTitle = 'commandprompt.ai'
$Host.UI.RawUI.ForegroundColor = 'Yellow'
$Host.UI.RawUI.BackgroundColor = 'DarkBlue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
