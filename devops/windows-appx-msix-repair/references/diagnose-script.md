# AppX / MSIX install-failure diagnostic + repair script (Windows host)

Verified against the "Windows 安装未完成 / installation incomplete" ChatGPT-Codex case.
Run each block via: `powershell.exe -NoProfile -Command "<block>"` (terminal is git-bash/MSYS).
Ignore mojibake in Chinese; trust re-queries, not the garbled text.

## 1. Locate registered packages (current user)
Get-AppxPackage *OpenAI* | Select-Object Name,Version,PackageFullName | Format-List
Get-AppxPackage *ChatGPT* | Select-Object Name,Version,PackageFullName | Format-List

## 2. All-users scope (needs elevation; throws UnauthorizedAccessException otherwise)
Get-AppxPackage -AllUsers *OpenAI* | Select-Object Name,Version,PackageFullName | Format-List

## 3. Local data dirs
Get-ChildItem "$env:LOCALAPPDATA" | Where-Object { $_.Name -match 'OpenAI|ChatGPT|Codex' } | Select-Object Name,LastWriteTime | Format-Table -AutoSize

## 4. Runtime deps (usually present)
Get-ChildItem 'C:\Program Files (x86)\Microsoft\EdgeWebView\Application'   # WebView2
Get-AppxPackage *WindowsAppRuntime* | Select-Object Name,Version | Format-Table -AutoSize

## 5. Uninstall (current user, no elevation)
Get-AppxPackage *OpenAI* | Remove-AppxPackage
# admin only if current-user removal is insufficient:
# Get-AppxPackage -AllUsers *OpenAI* | Remove-AppxPackage

## 6. Clear residual local data (drops local login state)
Remove-Item "$env:LOCALAPPDATA\OpenAI" -Recurse -Force

## 7. Verify removal
Get-AppxPackage *OpenAI*   # expect: no output / "无 OpenAI 包"

## 8. Reinstall (pick one)
# A) Microsoft Store: search "ChatGPT" (publisher OpenAI) -> Get/Install  [most reliable]
# B) winget (admin PowerShell) — verify product ID is current first:
#    winget search ChatGPT
#    winget install --id <PRODUCT_ID> -e

## 9. Verify successful (re)install
Get-AppxPackage *OpenAI* | Select-Object Name,Version,PackageFullName | Format-List
Get-AppxPackage *ChatGPT* | Select-Object Name,Version,PackageFullName | Format-List

## Notes
- Root cause of "安装未完成" + dead Retry: package not fully registered for current user.
- Codex is now built into the ChatGPT desktop app (OpenAI, 2026) — reinstall ChatGPT, not standalone Codex.
- Remove-Item on LocalAppData\OpenAI clears Codex sessions; warn the user first.
