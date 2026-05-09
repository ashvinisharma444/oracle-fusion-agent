# Oracle Fusion Agent - GitHub Push Script
# Run this from PowerShell as: .\push-to-github.ps1
# Prerequisites: git installed, GitHub account logged in or PAT ready

param(
    [string]$GitHubUsername = "ashvinisharma444",
    [string]$RepoName = "oracle-fusion-agent",
    [string]$PAT = ""  # Optional: paste your GitHub PAT here if prompted
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n=== Oracle Fusion AI Agent - GitHub Push ===" -ForegroundColor Cyan
Write-Host "Project folder: $ScriptDir`n"

# Step 1: Remove stale .git if exists
$gitDir = Join-Path $ScriptDir ".git"
if (Test-Path $gitDir) {
    Write-Host "Removing existing .git folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $gitDir
}

# Step 2: Init git
Set-Location $ScriptDir
Write-Host "Initializing git repository..." -ForegroundColor Green
git init -b main
git config user.email "ashvini.sharma444@gmail.com"
git config user.name "Ashwini Sharma"

# Step 3: Stage all files
Write-Host "Staging all files..." -ForegroundColor Green
git add -A
$count = (git status --short | Measure-Object -Line).Lines
Write-Host "  $count files staged" -ForegroundColor Gray

# Step 4: Commit
Write-Host "Creating initial commit..." -ForegroundColor Green
git commit -m "feat: Oracle Fusion AI Autonomous Diagnostic Agent - initial release

Production-grade enterprise platform for diagnosing Oracle Fusion Cloud issues.

Stack: Python 3.12 + FastAPI + Playwright + Gemini 2.5 Pro + PostgreSQL + Redis + ChromaDB + Next.js 14

Modules: Subscription, Order, Pricing, Billing, Revenue, Installed Base, Orchestration, Service Contracts

Architecture: Hexagonal (Clean) + DDD, provider-agnostic AI interface, read-only browser automation"

# Step 5: Set remote URL
if ($PAT -ne "") {
    $RemoteURL = "https://${PAT}@github.com/${GitHubUsername}/${RepoName}.git"
} else {
    $RemoteURL = "https://github.com/${GitHubUsername}/${RepoName}.git"
}

Write-Host "Setting remote origin..." -ForegroundColor Green
git remote add origin $RemoteURL

# Step 6: Push
Write-Host "`nPushing to GitHub..." -ForegroundColor Green
Write-Host "  Remote: https://github.com/${GitHubUsername}/${RepoName}" -ForegroundColor Gray

try {
    git push -u origin main
    Write-Host "`n✅ SUCCESS! Code pushed to GitHub." -ForegroundColor Green
    Write-Host "   View at: https://github.com/${GitHubUsername}/${RepoName}" -ForegroundColor Cyan
} catch {
    Write-Host "`n❌ Push failed. This usually means:" -ForegroundColor Red
    Write-Host "   1. The repo doesn't exist yet on GitHub" -ForegroundColor Yellow
    Write-Host "      → Go to https://github.com/new and create: $RepoName (empty, no README)" -ForegroundColor Yellow
    Write-Host "   2. Authentication failed" -ForegroundColor Yellow
    Write-Host "      → Run: git remote set-url origin https://YOUR_PAT@github.com/${GitHubUsername}/${RepoName}.git" -ForegroundColor Yellow
    Write-Host "      → Then run: git push -u origin main" -ForegroundColor Yellow
}

Write-Host "`n=== NEXT STEPS AFTER PUSH ===" -ForegroundColor Cyan
Write-Host "1. Deploy to Railway:" -ForegroundColor White
Write-Host "   → https://railway.app/new → Deploy from GitHub Repo → oracle-fusion-agent/backend" -ForegroundColor Gray
Write-Host "2. Add Railway services: PostgreSQL, Redis" -ForegroundColor White
Write-Host "3. Copy variables from .env.example to Railway environment" -ForegroundColor White
Write-Host "4. Run DB migration: railway run python -c `"from app.infrastructure.database.postgres import create_tables; import asyncio; asyncio.run(create_tables())`"" -ForegroundColor Gray
Write-Host "5. Create admin user via POST /api/v1/auth/register" -ForegroundColor White
Write-Host ""
