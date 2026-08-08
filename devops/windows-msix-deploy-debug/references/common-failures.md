# Common MSIX / Store install failures — transcripts & fixes

## 0x80073D02 — resource currently in use
Error:
```
Add-AppxPackage : 部署失败，原因是 HRESULT: 0x80073D02, 无法安装程序包，
原因是它修改的资源当前正在使用中。
错误 0x80073D02: 无法安装，因为需要关闭以下应用: OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0。
```
Meaning: another app in the **same package family** is running and holds a resource
the new registration needs. In the ChatGPT/Codex case, the standalone `OpenAI.Codex`
package was still running (multiple `ChatGPT.exe` + `codex.exe` PIDs) and blocked the
new ChatGPT package's fullTrust registration.
Fix: `Stop-Process -Name codex`, `Stop-Process -Name ChatGPT` (force), `Start-Sleep 2`,
then `Add-AppxPackage -Register`.

## Phantom "已安装" in Store but package absent
Symptom: Store shows the app as "已安装", but `Get-AppxPackage *ChatGPT*` returns empty
for the current user, and `C:\Program Files\WindowsApps` shows no ChatGPT folder
(actually ACL-denied, so the listing returns 0 — not proof it's absent).
Likely cause: the download/deploy stage failed or the package is staged but never
registered. Resolution path: switch region to US + `wsreset.exe` so the Store re-syncs,
then re-trigger install; OR if a staged package exists, `Add-AppxPackage -Register` it
after killing same-family processes.

## Region lock (ChatGPT in CN Store)
- Store search and `winget show --id 9NT1R1C2HH7J` both report "找不到" / "not found".
- Fix registry (HKCU, no admin needed): `HKCU:\Control Panel\International\Geo`
  `Nation` = `244` (United States). Optionally `Set-Culture en-US`. Then `wsreset.exe`
  and re-open Store. This does NOT change the display language.
- Correct ChatGPT Store product ID: **9NT1R1C2HH7J** (the wrong `9NT1M9S3F2QF` yields
  "content not available").

## PowerShell GBK encoding pitfall
Writing a `.ps1` with Chinese (UTF-8) and running it via `powershell.exe` on a zh-CN
box causes PowerShell 5.1 to decode as GBK, breaking string-quote pairing:
```
所在位置 :21 字符: 44  ... 字符串缺少终止符: "
Try 语句缺少自己的 Catch 或 Finally 块
```
Fix: author all `.ps1` files in pure ASCII/English. Never embed Chinese literals.

## Admin-status misdiagnosis
Running `WindowsPrincipal.IsInRole([Admin])` from the Hermes terminal returned `False`
even though `net localgroup administrators` listed the user. The agent shell runs under
a UAC *filtered token*. Always confirm admin with `net localgroup administrators`, not
`IsInRole`, when using this terminal.

## "完成设置 → 安装未完成" loop: running process is the actual root cause
Symptom: app opens, prompts "完成 Windows 设置", you click through, then "Windows 安装未完成"
/ Retry does nothing. MANY occurrences are NOT a registration defect — the app's own
process is already running and holds first-run resources.
Diagnosis (real case, 2026-07-12, jams_ machine):
- `tasklist` showed 9+ `ChatGPT.exe` + `codex.exe` PIDs alive before any fix.
- `Get-AppxPackage OpenAI.Codex` already returned `Status: Ok` — package was fine.
- `%LOCALAPPDATA%\ChatGPT` and `%LOCALAPPDATA%\OpenAI` did NOT exist → first-run
  config had never completed because the running process blocked it.
Fix: `Stop-Process -Name ChatGPT -Force` + `Stop-Process -Name codex -Force` (user
authorized; normal app termination), wait 2s, then `Add-AppxPackage -Register` the
`OpenAI.Codex` manifest. After re-register, launch and confirm process appears.
Note: the merged ChatGPT+Codex app ships as the `OpenAI.Codex` package on this machine —
there is NO `OpenAI.ChatGPT` package to look for.

## Verify by launching via AUMID (don't trust Status: Ok alone)
After `Add-AppxPackage -Register`, `Get-AppxPackage` shows `Status: Ok` but the app can
still loop on first run. Actually launch it and assert a process appears. Build the AUMID
from the manifest (App Id is usually `App`):
```powershell
$p = Get-AppxPackage OpenAI.Codex
[Xml]$x = Get-Content (Join-Path $p.InstallLocation 'AppxManifest.xml')
$ns = New-Object Xml.XmlNamespaceManager($x.NameTable)
$ns.AddNamespace('a','http://schemas.microsoft.com/appx/manifest/foundation/windows10')
$app = $x.SelectNodes('//a:Applications/a:Application',$ns)[0]
$aumid = $p.PackageFamilyName + '!' + $app.Id
explorer.exe ("shell:appsFolder\" + $aumid)
Start-Sleep 6
if ((Get-Process ChatGPT -ErrorAction SilentlyContinue).Count -gt 0) { "LAUNCH OK" } else { "LAUNCH FAILED" }
```
Write to a `.ps1` (ASCII only). The reusable version is `scripts/launch_aumid.ps1`.
If LAUNCH OK but UI still loops, the blocker is now network-side (first-run config/licence
fetch needs proxy, or Store region is CN) — a different problem from registration.
