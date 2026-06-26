$ErrorActionPreference = "Stop"

$projectRoot = Join-Path $PSScriptRoot "VocalNote-main"
if (-not (Test-Path $projectRoot)) {
    $projectRoot = $PSScriptRoot
}

$frontendDir = Join-Path $projectRoot "frontend"
$nodeModulesDir = Join-Path $frontendDir "node_modules"
$viteCacheDir = Join-Path $nodeModulesDir ".vite"

Push-Location $frontendDir
try {
    if (-not (Test-Path $nodeModulesDir)) {
        Write-Host "Installing frontend dependencies"
        npm install
    }

    if (Test-Path $viteCacheDir) {
        Write-Host "Clearing Vite cache"
        Remove-Item $viteCacheDir -Recurse -Force
    }

    Write-Host "Running frontend from $frontendDir"
    npm run dev -- --force
}
finally {
    Pop-Location
}
