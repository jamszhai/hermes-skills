# Agent-terminal MSIX / Store diagnosis + openai/codex bug #32149

## 1. Running PowerShell from the Hermes (git-bash / MSYS) terminal
- The pipe `powershell.exe -Command "..."` mangles non-ASCII output (GBK / UTF-16): Chinese
  error text and even `Get-AppxPackage` rows come back as garbage, and `$var` in the `-Command`
  string is expanded by bash, breaking scripts.
- Fix: write a `.ps1` with pure ASCII/English content, run
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File script.ps1`, and have the script write
  results with `Out-File -Encoding utf8 <path>`. Then read the `.txt` with `read_file`.
  Keep `.ps1` content ASCII (PowerShell 5.1 on zh-CN reads UTF-8-with-BOM fine, but ASCII is safest).
- Never inline Chinese in a `.ps1` — PowerShell 5.1 decoding UTF-8 Chinese as GBK breaks string
  quotes and throws a ParserError.

## 2. You cannot pop a UAC from the agent
- `Start-Process -FilePath <exe> -Verb RunAs` executed by the Hermes terminal fails with
  "non-interactive window station / access denied" — the agent runs headless / filtered token.
- Any elevation the user must click (Run-as-admin app launch, `Add-AppxPackage -Register`) must be
  handed to the user as manual desktop steps, OR wrapped in a self-elevating `.ps1` that the *user*
  double-clicks. Do not claim the agent performed elevation.

## 3. openai/codex bug #32149 — "Windows installation incomplete" after launch
Symptom (verbatim match): the merged ChatGPT/Codex Windows desktop app asks to "Complete Windows
setup"; clicking "Finish setup" shows **no real UAC prompt**; then "Windows installation incomplete"
with two dead buttons — "Retry Windows setup" (repeats, no UAC) and "Continue with limited access"
(does nothing). App stuck on the setup page.
Root cause: the app's first-run Windows-integration helper (file/protocol registration) needs
elevation but its internal UAC never appears. Issue still open, no official patch as of 2026-07.
NOT fixed by: `Add-AppxPackage -Register` (package is already `Ok`), killing processes, reinstalling.
Workaround (only community-verified fix): launch the app **elevated**.
- Start menu → ChatGPT / Codex → right-click → Run as administrator → Yes.
- Or run the exe directly:
  `C:\Program Files\WindowsApps\OpenAI.Codex_<ver>_x64__2p2nqsd0c76g0\app\ChatGPT.exe` as admin.
- 2026 merge note: ChatGPT ships INSIDE the `OpenAI.Codex` package; no separate `OpenAI.ChatGPT`
  AppX exists. App state under `%LOCALAPPDATA%\Packages\OpenAI.Codex_2p2nqsd0c76g0\`. An empty
  `LocalState` + `RoamingState` means the first-run wizard never completed.

## 4. Quick triage order for "installation incomplete"
1. `Get-AppxPackage *Codex* | Select Name,Version,Status` — if not listed, it's a staging /
   registration failure → re-register. If `Status` is `Ok`, go to 2.
2. Kill same-family ChatGPT / codex processes, retry launch.
3. If the wizard is still stuck with no UAC → bug #32149 → tell the user to Run as administrator.
