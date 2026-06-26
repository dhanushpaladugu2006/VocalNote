$ErrorActionPreference = "Stop"

$projectRoot = Join-Path $PSScriptRoot "VocalNote-main"
if (-not (Test-Path $projectRoot)) {
    $projectRoot = $PSScriptRoot
}

$backendDir = Join-Path $projectRoot "backend"
$requirementsFile = Join-Path $backendDir "requirements.txt"
$apiFile = Join-Path $backendDir "api.py"
$venvDir = Join-Path $backendDir ".venv-run"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

function New-BackendVenv {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        & $pythonCommand.Source -m venv $venvDir
        return
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        & $pyCommand.Source -3.11 -m venv $venvDir
        return
    }

    throw "Python 3.11 was not found on PATH. Install Python 3.11, then re-run this script."
}

function Test-BackendVenv {
    if (-not (Test-Path $venvPython)) {
        return $false
    }

    & $venvPython -c "import fastapi, uvicorn" *> $null
    return $LASTEXITCODE -eq 0
}

Push-Location $backendDir
try {
    if (-not (Test-BackendVenv)) {
        if (-not (Test-Path $venvDir)) {
            Write-Host "Creating backend virtual environment in $venvDir"
            New-BackendVenv
        }

        Write-Host "Installing backend dependencies"
        & $venvPython -m pip install --upgrade pip
        & $venvPython -m pip install -r $requirementsFile
    }

    Write-Host "Running backend from $backendDir"
    & $venvPython $apiFile
}
finally {
    Pop-Location
}
