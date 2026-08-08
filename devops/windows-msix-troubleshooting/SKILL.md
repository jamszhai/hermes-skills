---
name: windows-msix-troubleshooting
description: Debug Windows Store / MSIX / UWP desktop app install & registration failures — "Windows 安装未完成 / installation incomplete", fullTrust one-time-permission prompts, 0x80073D02, packages staged-but-not-registered. Includes PowerShell pitfalls (UTF-8/GBK script corruption, UAC-token admin false-negatives) and a self-elevating script template.
---

# Windows MSIX / Store App Install Troubleshooting

## When to use
A Windows desktop app (Store-distributed or MSIX) won't finish installing, shows "Windows 安装未完成 / Windows installation incomplete", "needs one-time permission to run", retry does nothing, or the app won't launch after a seemingly-finished install. Also covers "package not registered to current user" and first-launch fullTrust registration loops.

## CRITICAL PowerShell pitfalls (these waste real cycles — obey strictly)
1. **Never write .ps1 containing Chinese / non-ASCII in UTF-8 for PowerShell 5.1.** It decodes as GBK and corrupts string quotes → `ParserError: 表达式中缺少右")"` or `MissingArgument`. **Write every .ps1 in pure ASCII/English** (comments + strings). If you must show Chinese to the user, print it in the chat reply, not inside the script file.
2. **Admin-token FALSE NEGATIVE:** `WindowsPrincipal.IsInRole([Administrator])` returns **False** under a non-elevated UAC token EVEN FOR REAL ADMINS. To verify true group membership use `net localgroup administrators` (reads the group directly, not the filtered token). To obtain an elevated token, self-elevate (see references/scripts/self_elevate_template.ps1).
3. `Get-AppxPackage -AllUsers` throws `UnauthorizedAccessException` under a non-elevated token — must run under an elevated token.

## Diagnostic playbook (run under ELEVATED token where noted)
1. Is it registered to the current user? `Get-AppxPackage *<name>*`. Empty ⇒ not registered to this user.
2. Find staged / AllUsers packages (ELEVATED): `Get-AppxPackage -AllUsers *<name>*` and `Get-AppxPackageManifest <PackageFullName>`.
3. List the actual payload: `Get-ChildItem 'C:\Program Files\WindowsApps'` (needs elevation to even enumerate).
4. Runtime state/logs: `$env:LOCALAPPDATA\<Vendor>` (e.g. `OpenAI`). Absence of a `logs` dir while the process runs ⇒ app stuck before main window.
5. UAC policy: `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'`.
   - `ConsentPromptBehaviorUser = 3` ⇒ standard-user elevation is **silently denied** (no UAC prompt) → silent "installation incomplete".
   - `ConsentPromptBehaviorAdmin` controls admin prompt behavior (0 = elevate without prompting).
6. Event log: `Get-WinEvent -LogName 'Microsoft-Windows-AppXDeploymentServer/Operational' -MaxEvents 200`.

## Common failure: 0x80073D02 "资源当前正在使用中 / resource in use"
The package can't (re-)register because ITS OWN PROCESS is running and holds resources. **Kill the app process FIRST**, then re-register:
```
Get-Process -Name <exe> | Stop-Process -Force
Add-AppxPackage -Register "<InstallLocation>\AppxManifest.xml" -DisableDevelopmentMode
```
(Stopping the app is not "killing the system" — it's ending the stuck app; safe and expected here.)

## Common failure: "installation incomplete" / one-time-permission loop
MSIX apps with a **fullTrust capability** need admin registration at first launch. If it loops:
- Launch / register under an ELEVATED token (self-elevate).
- Temporarily set `ConsentPromptBehaviorAdmin=0` (admin elevates without prompting) + GPO `AllowAllTrustedApps=1` to unblock fullTrust registration.
- If it's the app's own first-run wizard bug (seen with OpenAI ChatGPT/Codex desktop after updates — see references/openai_chatgpt_codex.md), do a CLEAN REINSTALL: kill process → `Remove-AppxPackage` → delete `$env:LOCALAPPDATA\<Vendor>` → reboot → reinstall from Store.
- Verify region lock: Store apps may be geo-blocked (e.g. ChatGPT not findable in CN region). Switch Store region to US (`Set-ItemProperty 'HKCU:\Control Panel\International\Geo' Nation 244` + `wsreset.exe`) before install.

## Launch a packaged app programmatically
- AUMID = `<PackageFamilyName>!<AppId>` (AppId from `Get-AppxPackageManifest`).
- Activate under the current token: `$sh = New-Object -ComObject Shell.Application; $sh.Open("shell:AppsFolder\$aumid")`.
- NOTE: `[Activator]::CreateInstance([Type]::GetTypeFromProgID("ApplicationActivationManager")).ActivateApplication(...)` often fails in PowerShell with "找到 CreateInstance 的多个不确定重载" — prefer the Shell.Application fallback.

## Self-elevating script pattern
Copy references/scripts/self_elevate_template.ps1 and append your logic after the admin check. Always write it in ASCII.

## App-specific knowledge
See references/openai_chatgpt_codex.md for the OpenAI ChatGPT/Codex desktop quirks (package is `OpenAI.Codex`, not `ChatGPT`; region-lock; wrong Store product ID).
