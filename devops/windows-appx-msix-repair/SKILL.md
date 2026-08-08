---
name: windows-appx-msix-repair
description: Diagnose and repair Windows AppX/MSIX packaged desktop-app install failures — e.g. "完成 Windows 设置 → Windows 安装未完成" / "Windows installation incomplete", app won't launch, Retry does nothing. Covers OpenAI ChatGPT/Codex and generally any MSIX app on this Windows host.
---

# Windows AppX / MSIX install failure repair

## When to use
- A packaged Windows desktop app (ChatGPT, Codex, etc.) shows "完成 Windows 设置 → Windows 安装未完成" or "Windows installation incomplete", and clicking 重试 / Retry does nothing.
- App "installed" but won't open, or a fresh install never completes.
- Symptom: Retry has no effect — because the MSIX package was never fully registered for the current user, so Retry just re-triggers the same failed deploy loop.

## Environment note (this host)
The Hermes `terminal` tool runs through **git-bash / MSYS**, NOT PowerShell. To run PowerShell:
`powershell.exe -NoProfile -Command "<commands>"`
Chinese output often renders as **mojibake** in the terminal — that's a code-page artifact, not a failure. Verify success by re-querying state, not by reading the garbled text.

## Diagnostic workflow (run in order)
1. Find registered packages (current user):
   `Get-AppxPackage *OpenAI*`  and  `Get-AppxPackage *ChatGPT*`
2. All-users scope needs elevation; without it you get `UnauthorizedAccessException`:
   `Get-AppxPackage -AllUsers *OpenAI*`
3. Check local data dirs:
   `Get-ChildItem "$env:LOCALAPPDATA" | Where-Object { $_.Name -match 'OpenAI|ChatGPT|Codex' }`
4. Confirm runtime deps present (usually fine — the real failure is registration, not deps):
   - WebView2: `Get-ChildItem 'C:\Program Files (x86)\Microsoft\EdgeWebView\Application'`
   - Windows App SDK: `Get-AppxPackage *WindowsAppRuntime*`

## Root cause
"安装未完成" with a dead Retry button = the MSIX package is not fully registered/deployed for the current user. A plain user "卸载重装" often fails because MSIX registry residue isn't cleared, so the broken/partial registration persists and the reinstall loops.

## Remediation
1. Uninstall (current user, no elevation needed):
   `Get-AppxPackage *OpenAI* | Remove-AppxPackage`
   If needed, as admin: `Get-AppxPackage -AllUsers *OpenAI* | Remove-AppxPackage`
2. Clear residual local data (this drops local login state — acceptable when the app never installed properly):
   `Remove-Item "$env:LOCALAPPDATA\OpenAI" -Recurse -Force`
3. Reinstall via the cleanest channel:
   - **Microsoft Store** (most reliable — auto-handles deps + registration): search the app, publisher OpenAI, Get/Install.
   - **winget** (admin PowerShell): `winget install --id <PRODUCT_ID> -e`. Verify the current product ID first via `winget search ChatGPT` or the Store URL — do NOT hardcode an ID that may have changed.
4. Verify: re-run `Get-AppxPackage *OpenAI*` / `*ChatGPT*` and confirm a full `PackageFullName` now appears for the current user.

## Pitfalls
- **Do NOT tell the user to reinstall the standalone Codex app.** As of 2026 OpenAI merged Codex into the new ChatGPT desktop app (Windows + macOS). The correct target is the single "ChatGPT" desktop app; Codex is built in. Sources: OpenAI Help Center "Moving to the new ChatGPT desktop app"; OpenAI blog "ChatGPT is now a partner for your most ambitious work" ("With Codex technology built-in").
- A bare user-side "卸载重装" fails when MSIX residue remains — you must `Remove-AppxPackage` AND delete `LocalAppData\<Vendor>`.
- `Remove-Item` on `LocalAppData\OpenAI` wipes Codex login state; warn the user it clears local sessions before running it.
- Never kill the app/installer process unless the user explicitly says so (matches this user's standing instruction).

## References
- `references/diagnose-script.md` — copy-paste PowerShell diagnostic + repair one-liner set, verified on this host.
