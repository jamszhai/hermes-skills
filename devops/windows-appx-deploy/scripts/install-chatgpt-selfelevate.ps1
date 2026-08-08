# Self-elevating MSIX/Store installer. ASCII only (avoid GBK .ps1 corruption on zh-CN).
# Run in any PowerShell. If not elevated it auto-relaunches with -Verb RunAs (UAC prompt),
# user clicks YES, then install proceeds under a real admin token.
param()
$ErrorActionPreference = 'Stop'

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "Not elevated. Relaunching as administrator (UAC prompt will appear)..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host "=== Running as ADMINISTRATOR ===" -ForegroundColor Green

# Step 1: install from Store via winget (handles fullTrust registration)
Write-Host "== 1. Install ChatGPT via winget (Store product) ==" -ForegroundColor Cyan
try {
    winget install --id 9NT1M9S3F2QF -e --accept-package-agreements --accept-source-agreements
    Write-Host "winget finished" -ForegroundColor Green
} catch {
    Write-Host "winget failed: $_" -ForegroundColor Red
}

# Step 2: verify
Write-Host "== 2. Verify registration (current user) ==" -ForegroundColor Cyan
$pkg = Get-AppxPackage *ChatGPT*
if ($pkg) {
    $pkg | Select-Object Name, Version, PackageFullName, InstallLocation | Format-List
    Write-Host "SUCCESS: ChatGPT registered." -ForegroundColor Green
} else {
    Write-Host "Still not registered via winget. Opening Store page..." -ForegroundColor Yellow
    try { Start-Process "ms-windows-store://pdp/?ProductId=9NT1M9S3F2QF" } catch { Write-Host "Store launch failed: $_" -ForegroundColor Red }
}

Write-Host "== Done. Press Enter to close ==" -ForegroundColor Cyan
Read-Host
