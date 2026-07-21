# One-command start for AIOps Platform (Docker)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed. Install Docker Desktop first:" -ForegroundColor Red
    Write-Host "https://www.docker.com/products/docker-desktop/"
    exit 1
}

try {
    docker info *> $null
} catch {
    Write-Host "Docker Desktop is not running. Start Docker Desktop, wait until it is ready, then run this script again." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host ""
Write-Host "Starting AIOps Platform..." -ForegroundColor Cyan
Write-Host "  UI:  http://localhost"
Write-Host "  API: http://localhost:8000/docs"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host ""

docker compose up --build
