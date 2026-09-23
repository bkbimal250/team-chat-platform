param([Parameter(ValueFromRemainingArguments=$true)][string[]]$CommandArgs)
$ErrorActionPreference = 'Stop'
$taskEnvPath = Join-Path $PSScriptRoot '../../.env'
foreach ($line in Get-Content -LiteralPath $taskEnvPath) {
    if ($line -match '^([A-Z_]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
    }
}
$env:DATABASE_URL = "postgresql://organization_migrator:$($env:DB_PASSWORD)@127.0.0.1:55432/organization_db"
$env:RABBITMQ_URL = "amqp://organization_service:$($env:RABBITMQ_PASSWORD)@127.0.0.1:5672/organization"
$env:DJANGO_SETTINGS_MODULE = 'config.settings.local'
Push-Location $PSScriptRoot
try {
    uv run @CommandArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
