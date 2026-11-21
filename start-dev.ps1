$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPython = Join-Path $backend "venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating the backend virtual environment..."
    python -m venv (Join-Path $backend "venv")
}

Write-Host "Installing backend dependencies..."
& $venvPython -m pip install -r (Join-Path $backend "requirements-dev.txt")

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $frontend
    npm install
    Pop-Location
}

Write-Host "Starting the backend on http://127.0.0.1:8000"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", "Set-Location '$backend'; & '$venvPython' -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
)

Write-Host "Starting the frontend on http://localhost:5173"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", "Set-Location '$frontend'; npm run dev"
)

Write-Host "Both services are starting. Open http://localhost:5173/login when Vite is ready."