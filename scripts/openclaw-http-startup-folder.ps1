param(
    [ValidateSet("status", "install", "remove")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$startupDir = [Environment]::GetFolderPath("Startup")
$shortcut = Join-Path $startupDir "VideoKnowledgeOpenClawHttp.cmd"
$backgroundScript = Join-Path $root "scripts\start-openclaw-http-background.ps1"

function Status-Payload {
    param([bool]$Exists)
    [pscustomobject]@{
        ok = $Exists
        status = if ($Exists) { "installed" } else { "not_installed" }
        startup_file = $shortcut
        target_script = $backgroundScript
    } | ConvertTo-Json -Depth 4
}

switch ($Action) {
    "status" {
        Status-Payload -Exists (Test-Path -LiteralPath $shortcut)
    }
    "install" {
        if (-not (Test-Path -LiteralPath $backgroundScript)) {
            throw "Missing VKP OpenClaw HTTP background script: $backgroundScript"
        }
        $content = @(
            "@echo off",
            "powershell -NoProfile -ExecutionPolicy Bypass -File `"$backgroundScript`""
        )
        Set-Content -LiteralPath $shortcut -Value $content -Encoding ASCII
        Status-Payload -Exists $true
    }
    "remove" {
        if (Test-Path -LiteralPath $shortcut) {
            Remove-Item -LiteralPath $shortcut -Force
        }
        Status-Payload -Exists $false
    }
}

