# Launch an MSIX app via its AUMID and assert a process appears.
# ASCII-only (avoid GBK decode breakage on zh-CN PowerShell 5.1).
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File launch_aumid.ps1
$out = "C:\Users\jams_\.cc-switch\launch_result.txt"
"=== launch test $(Get-Date) ===" | Out-File -Encoding utf8 $out

$before = (Get-Process ChatGPT -ErrorAction SilentlyContinue).Count

$p = Get-AppxPackage OpenAI.Codex
if (-not $p) { "OpenAI.Codex NOT registered for this user." | Out-File -Encoding utf8 -Append $out; exit 1 }

[Xml]$x = Get-Content (Join-Path $p.InstallLocation 'AppxManifest.xml')
$ns = New-Object Xml.XmlNamespaceManager($x.NameTable)
$ns.AddNamespace('a','http://schemas.microsoft.com/appx/manifest/foundation/windows10')
$app = $x.SelectNodes('//a:Applications/a:Application',$ns)[0]
$aumid = $p.PackageFamilyName + '!' + $app.Id
"PackageFamily = $($p.PackageFamilyName)" | Out-File -Encoding utf8 -Append $out
"App Id        = $($app.Id)" | Out-File -Encoding utf8 -Append $out
"AUMID         = $aumid" | Out-File -Encoding utf8 -Append $out

explorer.exe ("shell:appsFolder\" + $aumid)
Start-Sleep -Seconds 6

$after = Get-Process ChatGPT -ErrorAction SilentlyContinue
"ChatGPT.exe before launch: $before" | Out-File -Encoding utf8 -Append $out
"ChatGPT.exe after launch : $($after.Count)" | Out-File -Encoding utf8 -Append $out
if ($after.Count -gt 0) {
  "LAUNCH OK - process running (PID(s): $($after.Id -join ','))" | Out-File -Encoding utf8 -Append $out
} else {
  "LAUNCH FAILED - no ChatGPT.exe appeared (registration may be fine but first-run config blocked)" | Out-File -Encoding utf8 -Append $out
}
"=== done $(Get-Date) ===" | Out-File -Encoding utf8 -Append $out
