# ============================================================
# SELF-ELEVATING PowerShell template (ASCII ONLY — never put
# Chinese/UTF-8 text in a .ps1 for PS 5.1, it corrupts quotes).
# Copy this header + the admin check, then put your logic after
# the "ADMIN OK" line. Run normally; it auto-prompts UAC.
# ============================================================
$ErrorActionPreference = 'Continue'

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
if (-not (Test-Admin)) {
    Write-Host "Not elevated. Relaunching as admin (UAC will appear)..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host "=== ADMIN OK ===" -ForegroundColor Green

# ===== YOUR LOGIC HERE =====
# Example: register a staged package after killing its process
# Get-Process -Name codex -ErrorAction SilentlyContinue | Stop-Process -Force
# $pkg = Get-AppxPackage -AllUsers *OpenAI.Codex* | Select-Object -First 1
# $m = Join-Path $pkg.InstallLocation "AppxManifest.xml"
# Add-AppxPackage -Register $m -DisableDevelopmentMode

Read-Host "Press Enter to close"
