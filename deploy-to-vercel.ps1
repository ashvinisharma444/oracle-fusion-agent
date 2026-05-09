# =============================================================
# Oracle Fusion AI Agent - Vercel Frontend Deployment Script
# =============================================================
# Run this from PowerShell in the oracle-fusion-agent folder:
#   .\deploy-to-vercel.ps1
# =============================================================

$ErrorActionPreference = "Continue"

$VERCEL_TOKEN = $env:VERCEL_TOKEN  # Set via: $env:VERCEL_TOKEN = "your-token"
$API_URL      = "https://oracle-fusion-backend-production.up.railway.app"
$FRONTEND_DIR = "$PSScriptRoot\frontend"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Oracle Fusion AI Agent - Vercel Deployment" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify frontend directory
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "ERROR: frontend\ directory not found at $FRONTEND_DIR" -ForegroundColor Red
    exit 1
}
Write-Host "[1/5] Frontend directory found: $FRONTEND_DIR" -ForegroundColor Green

# Step 2: Check / install Vercel CLI
Write-Host "[2/5] Checking Vercel CLI..." -ForegroundColor Yellow
$vercelCmd = Get-Command vercel -ErrorAction SilentlyContinue
if (-not $vercelCmd) {
    Write-Host "      Vercel CLI not found - installing globally..." -ForegroundColor Yellow
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Vercel CLI" -ForegroundColor Red
        exit 1
    }
}
$vercelVersion = (vercel --version 2>&1) | Where-Object { $_ -match '\d' } | Select-Object -First 1
Write-Host "      Vercel CLI ready: $vercelVersion" -ForegroundColor Green

# Step 3: Initial deployment
Write-Host ""
Write-Host "[3/5] Deploying to Vercel (production)..." -ForegroundColor Yellow
Write-Host "      This uploads source and builds on Vercel's servers." -ForegroundColor Gray
Write-Host ""

Set-Location $FRONTEND_DIR

$env:VERCEL_TOKEN = $VERCEL_TOKEN

# Deploy and capture output
$deployOutput = vercel --yes --prod --token $VERCEL_TOKEN 2>&1
$deployOutput | ForEach-Object { Write-Host $_ }

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Initial deployment failed (exit code $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

# Extract the production URL from the output
$deployUrl = ($deployOutput | Select-String -Pattern "https://[a-z0-9\-]+\.vercel\.app" | Select-Object -Last 1).Matches.Value
if (-not $deployUrl) {
    $deployUrl = ($deployOutput | Select-String -Pattern "https://\S+" | Select-Object -Last 1).Matches.Value
}

Write-Host ""
Write-Host "[3/5] Initial deployment complete." -ForegroundColor Green
Write-Host "      URL: $deployUrl" -ForegroundColor Cyan

# Step 4: Get project info and set env var
Write-Host ""
Write-Host "[4/5] Setting NEXT_PUBLIC_API_URL environment variable..." -ForegroundColor Yellow

# Get project name from .vercel/project.json
$projectJsonPath = "$FRONTEND_DIR\.vercel\project.json"
if (Test-Path $projectJsonPath) {
    $projectInfo = Get-Content $projectJsonPath | ConvertFrom-Json
    $projectId   = $projectInfo.projectId
    $orgId       = $projectInfo.orgId
    Write-Host "      Project ID: $projectId" -ForegroundColor Gray
} else {
    Write-Host "      Warning: .vercel\project.json not found - env var must be set manually." -ForegroundColor Yellow
}

# Add env var for all environments via CLI
Write-Host "      Adding NEXT_PUBLIC_API_URL to production, preview, and development..." -ForegroundColor Gray

$apiUrlValue = $API_URL

# Remove existing env var (ignore errors if it doesn't exist)
vercel env rm NEXT_PUBLIC_API_URL production --yes --token $VERCEL_TOKEN 2>$null | Out-Null
vercel env rm NEXT_PUBLIC_API_URL preview    --yes --token $VERCEL_TOKEN 2>$null | Out-Null
vercel env rm NEXT_PUBLIC_API_URL development --yes --token $VERCEL_TOKEN 2>$null | Out-Null

# Add the env var using echo to pipe the value (non-interactive)
$apiUrlValue | vercel env add NEXT_PUBLIC_API_URL production    --token $VERCEL_TOKEN --force
$apiUrlValue | vercel env add NEXT_PUBLIC_API_URL preview        --token $VERCEL_TOKEN --force
$apiUrlValue | vercel env add NEXT_PUBLIC_API_URL development   --token $VERCEL_TOKEN --force

Write-Host "      NEXT_PUBLIC_API_URL set successfully." -ForegroundColor Green

# Step 5: Redeploy so the env var takes effect
Write-Host ""
Write-Host "[5/5] Redeploying with env var applied..." -ForegroundColor Yellow

$redeployOutput = vercel --yes --prod --token $VERCEL_TOKEN 2>&1
$redeployOutput | ForEach-Object { Write-Host $_ }

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Redeploy failed (exit code $LASTEXITCODE)" -ForegroundColor Red
    Write-Host "       Initial deploy is still live at: $deployUrl" -ForegroundColor Yellow
    exit 1
}

# Extract final production URL
$finalUrl = ($redeployOutput | Select-String -Pattern "https://[a-z0-9\-]+\.vercel\.app" | Select-Object -Last 1).Matches.Value
if (-not $finalUrl) {
    $finalUrl = ($redeployOutput | Select-String -Pattern "https://\S+" | Select-Object -Last 1).Matches.Value
}
if (-not $finalUrl) { $finalUrl = $deployUrl }

# Done
Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Live URL : $finalUrl" -ForegroundColor Cyan
Write-Host "  Backend  : $API_URL" -ForegroundColor Gray
Write-Host ""
Write-Host "  The frontend is connected to the Railway backend." -ForegroundColor Gray
Write-Host "  Open the URL above in your browser to verify." -ForegroundColor Gray
Write-Host ""

# Save the URL to a file for reference
$deployInfo = "Vercel Frontend URL: $finalUrl`nBackend URL: $API_URL`nDeployed: $(Get-Date)"
$deployInfo | Out-File -FilePath "$PSScriptRoot\deployment-urls.txt" -Encoding UTF8
Write-Host "  Deployment info saved to: deployment-urls.txt" -ForegroundColor Gray
Write-Host ""
