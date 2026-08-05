param(
    [int]$WaitSeconds = 5
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$logDir = Join-Path $root ".local\logs"
$stdoutLog = Join-Path $logDir "openclaw-http.stdout.log"
$stderrLog = Join-Path $logDir "openclaw-http.stderr.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$env:PYTHONPATH = Join-Path $root "src"
$env:PYTHONIOENCODING = "utf-8"
$process = Start-Process `
    -FilePath "python" `
    -ArgumentList @("-m", "video_knowledge_pipeline.openclaw_http") `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

$deadline = (Get-Date).AddSeconds($WaitSeconds)
$health = $null
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 300
    if ($process.HasExited) {
        break
    }
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8931/health" -TimeoutSec 1
        break
    } catch {
        $health = $null
    }
}

Start-Sleep -Milliseconds 300
$process.Refresh()
$stillRunning = -not $process.HasExited
$status = if ($health -and $stillRunning) {
    "running"
} elseif ($health -and -not $stillRunning) {
    "started_then_exited"
} elseif (-not $health -and -not $stillRunning) {
    "exited_before_health"
} else {
    "started_without_health"
}

[pscustomobject]@{
    ok = [bool]$health -and $stillRunning
    status = $status
    pid = $process.Id
    running = $stillRunning
    exit_code = if ($process.HasExited) { $process.ExitCode } else { $null }
    health = $health
    stdout_log = $stdoutLog
    stderr_log = $stderrLog
    next_actions = if ($health -and $stillRunning) { @("openclaw_can_call_vkp_http_bridge") } else { @("inspect_openclaw_http_logs", "rerun_openclaw_bridge_doctor") }
} | ConvertTo-Json -Depth 8
