# Self-elevating diagnose + register script for a stalled Store/MSIX package.
# Run on the USER's machine (not the agent terminal). It relaunches itself as admin
# via UAC; the user clicks one "Yes". Pure ASCII to avoid GBK decode breakage.
# Edit the $family filter / package name as needed.

$ErrorActionPreference = 'Continue'

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
if (-not (Test-Admin)) {
    Write-Host "Not elevated. Relaunching as admin (UAC will appear)..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"
    exit
}

Write-Host "=== ADMIN OK ===" -ForegroundColor Green

# 1) Kill lingering same-family processes (the usual 0x80073D02 cause)
Write-Host "== 1. Stop OpenAI/Codex/ChatGPT processes ==" -ForegroundColor Cyan
foreach ($n in @('Codex','ChatGPT','OpenAI')) {
    Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host ("  stopping: " + $_.Name + " pid=" + $_.Id)
        try { $_ | Stop-Process -Force } catch {}
    }
}
Start-Sleep -Seconds 2

# 2) Find all OpenAI-family packages (AllUsers sees staged ones)
Write-Host "== 2. All OpenAI-family packages (AllUsers) ==" -ForegroundColor Cyan
$fam = Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'OpenAI|ChatGPT|Codex' }
if ($fam) { $fam | Select-Object Name,Version,PackageFullName,InstallLocation | Format-List }
else { Write-Host "  (none found)" }

# 3) Register
Write-Host "== 3. Register ChatGPT/OpenAI packages ==" -ForegroundColor Cyan
$ok = $false
foreach ($p in $fam) {
    $m = Join-Path $p.InstallLocation "AppxManifest.xml"
    if (Test-Path $m) {
        try { Add-AppxPackage -Register $m -DisableDevelopmentMode; Write-Host ("  OK: " + $p.PackageFullName) -ForegroundColor Green; $ok=$true }
        catch { Write-Host ("  FAIL " + $p.PackageFullName + " : " + $_.Exception.Message) -ForegroundColor Red }
    } else { Write-Host ("  no manifest: " + $m) -ForegroundColor Red }
}

# 4) Verify
Write-Host "== 4. Verify current user ==" -ForegroundColor Cyan
$r = Get-AppxPackage *ChatGPT*
if ($r) { $r | Select Name,Version,PackageFullName | Format-List; Write-Host "SUCCESS" -ForegroundColor Green }
else { Write-Host "STILL NOT REGISTERED — package may not be staged; use Store to reinstall." -ForegroundColor Red }

# 5) Launch smoke-test via AUMID (Status: Ok is not enough — the app can still loop).
Write-Host "== 5. Launch smoke-test ==" -ForegroundColor Cyan
$c = Get-AppxPackage OpenAI.Codex
if ($c) {
    [Xml]$xm = Get-Content (Join-Path $c.InstallLocation 'AppxManifest.xml')
    $nm = New-Object Xml.XmlNamespaceManager($xm.NameTable)
    $nm.AddNamespace('a','http://schemas.microsoft.com/appx/manifest/foundation/windows10')
    $ap = $xm.SelectNodes('//a:Applications/a:Application',$nm)[0]
    $aid = $c.PackageFamilyName + '!' + $ap.Id
    explorer.exe ("shell:appsFolder\" + $aid)
    Start-Sleep -Seconds 6
    $cnt = (Get-Process ChatGPT -ErrorAction SilentlyContinue).Count
    if ($cnt -gt 0) { Write-Host ("LAUNCH OK (ChatGPT.exe x" + $cnt + ")") -ForegroundColor Green }
    else { Write-Host "LAUNCH FAILED - no process; first-run config may be network-blocked (proxy/region)." -ForegroundColor Red }
} else { Write-Host "  OpenAI.Codex not found - skip launch test." -ForegroundColor Yellow }

Read-Host "Press Enter"
