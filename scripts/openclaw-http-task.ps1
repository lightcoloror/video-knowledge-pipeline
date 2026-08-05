param(
    [ValidateSet("status", "register", "start", "stop", "unregister")]
    [string]$Action = "status",
    [string]$TaskName = "VideoKnowledgeOpenClawHttp"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$startCmd = Join-Path $root "scripts\start-openclaw-http.cmd"
$backgroundScript = Join-Path $root "scripts\start-openclaw-http-background.ps1"

function Get-TaskStatus {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & cmd.exe /c "schtasks /Query /TN `"$TaskName`" /FO LIST /V 2>&1"
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    if ($exitCode -ne 0) {
        [pscustomobject]@{
            ok = $false
            task_name = $TaskName
            exists = $false
            status = "not_registered"
            message = ($output | Out-String).Trim()
            start_command = $startCmd
        } | ConvertTo-Json -Depth 4
        return
    }
    $output
}

function Assert-StartCommand {
    if (-not (Test-Path -LiteralPath $startCmd)) {
        throw "Missing VKP OpenClaw HTTP startup script: $startCmd"
    }
}

function Write-TaskFailure {
    param(
        [string]$Status,
        [string]$Message
    )
    [pscustomobject]@{
        ok = $false
        task_name = $TaskName
        exists = $false
        status = $Status
        message = $Message
        start_command = $startCmd
        fallback_command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$backgroundScript`""
    } | ConvertTo-Json -Depth 4
}

switch ($Action) {
    "status" {
        Get-TaskStatus
    }
    "register" {
        Assert-StartCommand
        $taskRun = "cmd.exe /c `"`"$startCmd`"`""
        $output = & cmd.exe /c "schtasks /Create /TN `"$TaskName`" /SC ONLOGON /TR `"$taskRun`" /RL LIMITED /F 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-TaskFailure -Status "register_failed" -Message (($output | Out-String).Trim())
            exit 1
        }
        Get-TaskStatus
    }
    "start" {
        $output = & cmd.exe /c "schtasks /Run /TN `"$TaskName`" 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-TaskFailure -Status "start_failed" -Message (($output | Out-String).Trim())
            exit 1
        }
        Get-TaskStatus
    }
    "stop" {
        $output = & cmd.exe /c "schtasks /End /TN `"$TaskName`" 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-TaskFailure -Status "stop_failed" -Message (($output | Out-String).Trim())
            exit 1
        }
        Get-TaskStatus
    }
    "unregister" {
        $output = & cmd.exe /c "schtasks /Delete /TN `"$TaskName`" /F 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-TaskFailure -Status "unregister_failed" -Message (($output | Out-String).Trim())
            exit 1
        }
    }
}
