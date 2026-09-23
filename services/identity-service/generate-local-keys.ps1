$ErrorActionPreference = 'Stop'
python $PSScriptRoot/generate_local_keys.py
Write-Output 'Local Ed25519 signing keys are ready.'
