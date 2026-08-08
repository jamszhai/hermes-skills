# OpenAI ChatGPT / Codex Desktop App — gotchas (verified 2026-07-11)

## Package identity
- The "ChatGPT" desktop app in the Microsoft Store actually deploys the package
  `OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0` (PackageFamilyName
  `OpenAI.Codex_2p2nqsd0c76g0`). There is NO package literally named "ChatGPT".
- As of 2026, Codex is BUILT INTO the ChatGPT desktop app (OpenAI merged them).
  So `OpenAI.Codex` IS the new ChatGPT desktop client. Don't hunt for a "ChatGPT" package.

## Symptom: "完成 Windows 设置 / 需要一次性权限才能运行 → Windows 安装未完成 → 重试无反应"
- Root cause pattern: fullTrust-capability MSIX needs admin registration at first
  launch. Loops when the registration is silently blocked. NOT a download problem
  once the package is staged in `C:\Program Files\WindowsApps`.
- This is a KNOWN POST-UPDATE BUG for OpenAI's desktop app — multiple community
  reports (linux.do, Reddit r/codex) of "Windows installation incomplete after an
  update" with no single official fix. A clean reinstall often resolves it.

## Store product ID correction
- WRONG (commonly quoted): `9NT1M9S3F2QF`  -> Store says "we might not have that".
- RIGHT (US Store): `9NT1R1C2HH7J`. But the app is geo-blocked in some regions
  (e.g. CN), so winget / Store may not find it at all without switching region.

## Region lock workaround
- Microsoft Store hides ChatGPT in CN region. Switch region to US:
  `Set-ItemProperty 'HKCU:\Control Panel\International\Geo' Nation 244`
  then `wsreset.exe`, then search "ChatGPT" in Store.
- Network note: Store + winget + CDN need reachable external network (proxy/TUN).
  If `Invoke-WebRequest` to MS CDN fails with "连接已关闭", the machine has no
  system-level proxy — Store/winget can't fetch even after region switch.

## 0x80073D02 during re-register
- Means the app's own process is still running and holding resources. Kill it
  (Get-Process codex | Stop-Process -Force) BEFORE Add-AppxPackage -Register.

## Launch via COM
- Prefer: `$sh = New-Object -ComObject Shell.Application; $sh.Open("shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App")`
- AUMID AppId comes from Get-AppxPackageManifest -> Package.Applications.Application.Id
- Avoid ApplicationActivationManager COM (PowerShell "CreateInstance overload" error).
