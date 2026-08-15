$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")

# The registry health probe must not pay the cost of loading or inspecting the
# ASR/model stack.  Keep this dispatch before environment-file parsing and the
# remote-destination allowlist; detailed capability diagnostics remain under
# `asr-env-status`.
if ($args.Count -gt 0 -and $args[0] -eq "quick-health") {
    $env:PYTHONPATH = Join-Path $root "src"
    $env:PYTHONIOENCODING = "utf-8"
    $quickArgs = @()
    if ($args.Count -gt 1) {
        $quickArgs = $args[1..($args.Count - 1)]
    }
    python -m video_knowledge_pipeline.quick_health @quickArgs
    $exitCode = $LASTEXITCODE
    exit $exitCode
}

foreach ($envFile in @((Join-Path $root ".local\video-knowledge.env"), (Join-Path $root ".local\vision.env"))) {
    if (Test-Path -LiteralPath $envFile) {
        foreach ($line in Get-Content -LiteralPath $envFile) {
            $trimmed = $line.Trim()
            if (-not $trimmed -or $trimmed.StartsWith("#")) {
                continue
            }
            if ($trimmed -match '^(?:\$env:)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
                $name = $Matches[1]
                $value = $Matches[2].Trim()
                if ($value.Length -ge 2) {
                    $quote = $value.Substring(0, 1)
                    if (($quote -eq '"' -or $quote -eq "'") -and $value.EndsWith($quote)) {
                        $value = $value.Substring(1, $value.Length - 2)
                    }
                }
                if ($name -like "LECTURE_*" -or $name -in @("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "AGNES_API_KEY", "ARK_API_KEY", "VOLCENGINE_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "LOCAL_QWEN_VL_API_KEY", "LOCAL_QWEN_VL_BASE_URL", "LOCAL_QWEN_VL_MODEL", "LOCAL_VLM_API_KEY", "LOCAL_VLM_BASE_URL", "LOCAL_VLM_MODEL")) {
                    [Environment]::SetEnvironmentVariable($name, $value, "Process")
                }
            }
        }
    }
}
$env:PYTHONPATH = Join-Path $root "src"
$env:PYTHONIOENCODING = "utf-8"
$env:LITELLM_TELEMETRY = "False"
$env:LITELLM_LOCAL_MODEL_COST_MAP = "True"

# Keep the CLI's consent front door aligned with the Broker. The reviewed
# model settings are the single source of configured remote destinations;
# individual plans and consent v2 still narrow this set to exact routes.
if (-not $env:VKP_MODEL_CONNECTOR_ALLOWED_ROOTS) {
    $roots = @([string]$root)
    $managedOutputRoot = Join-Path (Split-Path -Parent $root) "video-knowledge-output"
    if (Test-Path -LiteralPath $managedOutputRoot -PathType Container) {
        $roots += (Resolve-Path -LiteralPath $managedOutputRoot).Path
    }
    $env:VKP_MODEL_CONNECTOR_ALLOWED_ROOTS = ($roots -join [IO.Path]::PathSeparator)
}
if (-not $env:VKP_MODEL_CONNECTOR_ALLOWED_DESTINATIONS) {
    $settingsPath = if ($env:VKP_MODEL_API_SETTINGS_PATH) {
        $env:VKP_MODEL_API_SETTINGS_PATH
    } else {
        Join-Path $root ".local\model-api-settings.json"
    }
    if (Test-Path -LiteralPath $settingsPath) {
        $rawStatus = & python -m video_knowledge_pipeline.model_destination_allowlist `
            --settings-path $settingsPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to derive configured remote model destinations."
        }
        $destinationStatus = ConvertFrom-Json -InputObject ($rawStatus -join "`n")
        $env:VKP_MODEL_CONNECTOR_ALLOWED_DESTINATIONS = `
            (@($destinationStatus.destinations) -join ",")
    }
}
python -m video_knowledge_pipeline.cli @args
$exitCode = $LASTEXITCODE
exit $exitCode
