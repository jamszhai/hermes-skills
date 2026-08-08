---
name: windows-msix-deploy-debug
description: Debug why a Microsoft Store / MSIX / AppX package fails to install or register on Windows — the "Windows 安装未完成" / "Windows installation incomplete" / "needs one-time permission" symptom, AND the post-install "Complete Windows setup" wizard that fails to elevate (openai/codex bug #32149). Covers region locks, running-process blocks (0x80073D02), admin-token misdiagnosis, PowerShell GBK/UTF-16 encoding pitfalls, and the non-interactive UAC wall.
trigger: User reports a Store or MSIX desktop app (ChatGPT, Codex, etc.) shows "installation incomplete", "安装未完成", a "完成 Windows 设置" loop, "needs one-time permission", or won't launch after install on Windows.
---

# Windows MSIX / Store App Install-Failure Debugging

Use this when a Windows desktop app installed from Microsoft Store (or sideloaded
`.msix` / `.msixbundle`) won't open and shows an install/setup error, typically:
"Complete Windows setup" -> "Windows installation incomplete" -> Retry does nothing.

The Hermes terminal on the user's Windows box is git-bash/MSYS; run PowerShell via
`powershell.exe -NoProfile -Command "..."`.

## Diagnostic sequence

1. **Confirm real admin status.** Do NOT trust `WindowsPrincipal.IsInRole` or
   `-is [admin]` from this terminal — the agent shell runs under a UAC *filtered*
   (non-elevated) token, so it reports `False` even for true admins. Use:
   ```
   net localgroup administrators
   ```
   If the user's account appears in the list, they ARE an admin. The filtered token
   is the only reason `IsInRole` said False.

2. **Check whether the package is registered to the current user:**
   ```powershell
   # Write to a .ps1 file (ASCII); piping via bash mangles UTF-16 / $ signs.
   Get-AppxPackage OpenAI.Codex | Select Name,Version,PackageFullName,InstallLocation,Status | Out-File -Encoding utf8 C:\tmp\pkgs.txt
   ```
   Check the package family. On this machine the merged ChatGPT+Codex app IS the
   `OpenAI.Codex` package (there is no `OpenAI.ChatGPT` package).

2b. **Check for already-running same-family processes BEFORE any re-register.** This is
    the #1 real cause of the "完成设置 → 安装未完成" loop:
    ```powershell
    Get-Process ChatGPT,codex -ErrorAction SilentlyContinue | Select Name,Id,CPU
    ```
    If processes are present, the first-run config is blocked. Kill them (user-authorized
    app termination), wait 2s, THEN re-register.

2c. **Read the app's own log BEFORE assuming bug #32149 (UAC) AND BEFORE any re-register.**
    Order rule (learned the hard way 2026-07-12: re-registering the MSIX was wasted effort
    because the real cause was a config parse error). The "完成设置 → 安装未完成" loop has a
    far more common root cause on THIS machine: a **TOML parse error in
    `C:\Users\<user>\.codex\config.toml`** (rewritten by CC Switch live-config management).
    The app cannot parse its config → its Windows-integration setup (`windowsSandbox/setupStart`)
    fails wholesale → surfaces identical to bug #32149, but it is NOT a UAC/permission issue,
    and `Add-AppxPackage -Register` will NOT fix it.
    Find the latest log and grep for the signature:
    ```powershell
    # write to .ps1 (ASCII); the log is under the MSIX package local cache:
    $logdir = Join-Path $env:LOCALAPPDATA "Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\Codex\Logs"
    Get-ChildItem $logdir -Recurse -Filter codex-desktop-*.log | Sort LastWriteTime -Desc | Select -First 1
    ```
    Then grep that file for `too few unicode value digits` / `invalid unicode escape` /
    `failed to load configuration`. If present → fix config.toml:
    - The offending line is usually a `notify` path in double quotes; backslashes (`\U`,
      `\A`, `\c`) are read as malformed unicode escapes.
    - Convert it to a TOML **literal string**: single-quoted — backslashes are then NOT
      treated as escapes. Keep the CC Switch proxy routing (`base_url`, `model`) intact.
    - **Subtlety:** the app parses config.toml with a **Rust TOML parser**, which is STRICTER
      than `python -m tomllib`. A file that passes `tomllib.load` can still fail in the app with
      `too few unicode value digits`. So do NOT trust a Python "TOML OK" as proof — the safest
      fix is to eliminate backslash escapes entirely by using **forward-slash paths**
      (e.g. `C:/Users/jams_/...`) or single-quoted literals in the `notify` line.
    - Verify with Python 3.11 (no third-party dep): `tomllib.load(open(config.toml,'rb'))`
      must succeed. Then re-open ChatGPT normally from the Start menu.
    - If the model picker is STILL empty after config is valid, the CC Switch codex proxy
      takeover is likely inactive: check `proxy_config.live_takeover_active` for `codex`
      in `~/.cc-switch/cc-switch.db`; set it to 1 and restart CC Switch.
    Full triage + gotchas: `references/config-toml-setup-incomplete.md` (also see the
    `cc-switch-hermes-config` skill's `session-2026-07-12-*` reference).

3. If `Get-AppxPackage` returns nothing but the Store says "installed", the package is
   either staged-but-not-registered, or the Store shows a phantom "installed"
   (download/registration actually failed).

## Common root causes

| Symptom | Root cause | Fix |
|---|---|---|
| Store can't find app / "content not available" | Region lock (e.g. ChatGPT blocked in CN Store) | Switch Store region to US (registry `HKCU:\Control Panel\International\Geo` `Nation=244`), run `wsreset.exe`, re-open Store |
| "needs one-time permission" then "installation incomplete" / retry dead | MSIX fullTrust registration blocked, or same-family app already running holding resources | Kill lingering same-family processes, then re-register |
| `0x80073D02` "resource currently in use" | Another app in same package family (e.g. `OpenAI.Codex`) is running | `Stop-Process -Name codex` etc., wait 2s, re-register |
| Script parse errors with garbled Chinese | PowerShell 5.1 reads `.ps1` as system ANSI (GBK on zh-CN); UTF-8 Chinese breaks string quotes | Write all `.ps1` in pure ASCII/English; never embed Chinese in scripts run by `powershell.exe` |
| `Get-ChildItem C:\Program Files\WindowsApps` returns 0 | ACL denies listing, not actually empty | Use `Get-AppxPackage -AllUsers` instead of listing the folder |
| App launches, shows "Complete Windows setup", click "Finish setup" → **no UAC appears** → "Windows installation incomplete" with dead "Retry"/"Continue with limited access" | **openai/codex bug #32149** (issue still open, no official patch): the first-run Windows-integration helper needs elevation but its internal UAC never fires | `Add-AppxPackage -Register` will NOT fix this (package is already `Ok`). The only community-verified fix is to **launch the app elevated** (Start menu → right-click → Run as administrator → Yes). Hand this to the user as manual desktop steps — see Pitfalls. |
| Package `Status: Ok` but the app still loops on first run | Registration succeeded; the remaining blocker is the #32149 elevation bug, or a config-parse failure (see below) | Diagnose which: read the app log (below). If it shows a TOML parse error → fix config.toml. If it shows a failed UAC → only community fix is Run-as-admin (see pitfall, but note the MSIX Run-as-admin path caveat). |
| App opens but "自定义模型" picker is empty AND/OR "完成设置" re-prompts every launch | **`~/.codex/config.toml` TOML syntax error** (most common real cause on THIS machine, NOT bug #32149) OR the CC Switch codex proxy takeover is inactive (`proxy_config.live_takeover_active=0`) | Read the latest `codex-desktop-*.log` under the app's LocalCache Logs. If it says `config.toml:..: too few unicode value digits` / `invalid unicode escape`, fix the offending line (use single-quoted TOML literal strings for backslash paths). Then verify with Python 3.11 `tomllib.load`. If config is clean, check `proxy_config` for codex and set `live_takeover_active=1`, restart CC Switch. |

## Self-elevating script pattern
The agent's own terminal cannot self-elevate; the script must run on the user's
machine so the UAC prompt appears to *them* (they click one "Yes"). Pattern:
```powershell
function Test-Admin { $id=[Security.Principal.WindowsIdentity]::GetCurrent(); $p=New-Object Security.Principal.WindowsPrincipal($id); return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) }
if (-not (Test-Admin)) { Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"; exit }
# ... elevated body ...
```

## Re-register an already-downloaded (staged) package
```
Add-AppxPackage -Register "<InstallLocation>\AppxManifest.xml" -DisableDevelopmentMode
```
Run ONLY after killing any running same-family processes, and only from an elevated
context.

## Verify
Two checks, both required:
1. `Get-AppxPackage OpenAI.Codex` should list the package for the current user with
   `Status: Ok` (after an `Add-AppxPackage -Register`, the AppX deployment log shows
   Event ID 400 "部署 Register 操作已成功完成").
2. **Actually launch it.** `Status: Ok` is necessary but NOT sufficient — the app can
   still loop on first run. Launch via AUMID and confirm a process appears:
   ```powershell
   # (write to a .ps1, ASCII only; see scripts/launch_aumid.ps1)
   $p = Get-AppxPackage OpenAI.Codex
   [Xml]$x = Get-Content (Join-Path $p.InstallLocation 'AppxManifest.xml')
   $ns = New-Object Xml.XmlNamespaceManager($x.NameTable)
   $ns.AddNamespace('a','http://schemas.microsoft.com/appx/manifest/foundation/windows10')
   $app = $x.SelectNodes('//a:Applications/a:Application',$ns)[0]
   explorer.exe ("shell:appsFolder\" + $p.PackageFamilyName + "!" + $app.Id)
   Start-Sleep 6
   if ((Get-Process ChatGPT -ErrorAction SilentlyContinue).Count -gt 0) { "LAUNCH OK" } else { "LAUNCH FAILED" }
   ```
   If the process appears but the UI still shows "完成设置", the blocker is now likely
   network-side (first-run config/licence fetch needs the proxy, or Store region is CN).
   That is a different problem from registration — see region-lock entry.

## Pitfalls
- The ChatGPT Store product ID is **`9NT1R1C2HH7J`** (NOT `9NT1M9S3F2QF`). Wrong ID -> Store "can't find content".
- As of 2026, **Codex is built INTO the ChatGPT desktop app**. On THIS machine the
  merged app ships via the **`OpenAI.Codex` package** — there is **NO separate
  `OpenAI.ChatGPT` package** registered. The `ChatGPT.exe` you launch lives inside
  `OpenAI.Codex_<ver>_x64__<pub>\app\ChatGPT.exe`. Do NOT look for or try to install an
  `OpenAI.ChatGPT` package; the merged app IS the `OpenAI.Codex` package. Diagnose with
  `Get-AppxPackage OpenAI.Codex` and treat that package as the ChatGPT app.
- **Most common real root cause of the "完成设置 → 安装未完成" loop: the app's
  process is already running.** Before re-registering, check `tasklist` / `Get-Process
  ChatGPT` — if multiple `ChatGPT.exe` (+ `codex.exe`) are alive, first-run setup is
  blocked by the same-family process holding resources. Kill them first (normal app
  termination, not a system process — only when the user authorizes), THEN re-register.
  This alone fixes the loop far more often than region switches.
- **Verify by actually launching, not just `Status: Ok`.** After re-register, launch
  via AUMID (see `scripts/launch_aumid.ps1`) and confirm `(Get-Process ChatGPT).Count > 0`
  a few seconds later. Write the launch command to a `.ps1` file (ASCII only) and run it;
  never inline via bash — `$` gets mangled by the MSYS shell.
- **The agent CANNOT pop a UAC prompt.** The Hermes terminal runs in a non-interactive
  (headless / filtered-token) session, so `Start-Process -FilePath <exe> -Verb RunAs` from
  the agent fails with "non-interactive window station / access denied". Any step that needs
  the user to click "Yes" — app *Run as administrator*, or `Add-AppxPackage -Register` from
  an elevated shell — must be handed to the user as **manual desktop instructions**, or
  wrapped in a self-elevating `.ps1` the *user* double-clicks. Do not claim the agent
  performed elevation. (See `references/agent-terminal-diag.md`.)
- **openai/codex bug #32149: "Finish setup" never elevates → "Windows installation incomplete".**
  If the package is `Status: Ok` and processes were killed/re-registered yet the app STILL
  loops on "Complete Windows setup" with no UAC, this is NOT a registration fault — it is the
  app's first-run Windows-integration helper failing to request elevation (GitHub issue
  #32149, still open, no patch). `Add-AppxPackage -Register` will not fix it.
  **IMPORTANT — do NOT send the user to "Run as administrator" on the exe inside
  `C:\Program Files\WindowsApps\...`:** that path is MSIX-protected and immediately fails with
  "Windows cannot access the specified device, path, or file" (seen 2026-07-12). The only valid
  Run-as-admin route is the **Start menu** shortcut (AppExecutionAlias): Start → ChatGPT/Codex →
  right-click → Run as administrator → Yes. An empty `LocalState`/`RoamingState` under the
  package dir means the first-run wizard never completed. Tell the user to try the Start-menu
  Run-as-admin route and report back; do NOT loop on re-registering. BUT FIRST rule out the
  config.toml TOML error (step 2c) — that is a more common real cause and is fully fixable by
  the agent without any UAC.
- `winget` cannot install region-locked Store apps even after a region switch if
  winget's source hasn't synced; fall back to the Store UI or
  `ms-windows-store://search/?query=ChatGPT`.
- `Get-AppxPackage -AllUsers` requires elevation; from the filtered agent token it
  throws `UnauthorizedAccessException` — that is expected, NOT proof the package is absent.
- Killing the lingering same-family process is often the actual fix for the
  "installation incomplete" loop; do it only when the user authorizes (it is a normal
  app termination, not a system process kill).

See `references/common-failures.md` for the full 0x80073D02 transcript and the exact
region-switch registry keys. Reusable scripts: `scripts/diag_register.ps1`
(self-elevating diagnose+register) and `scripts/launch_aumid.ps1` (AUMID launch smoke test).
`references/agent-terminal-diag.md` covers the openai/codex bug #32149 loop, the
non-interactive UAC wall, and how to run PowerShell safely from the git-bash/MSYS terminal.
`references/config-toml-setup-incomplete.md` covers the config.toml TOML-error root cause
(most common real cause of the "完成设置" loop on this machine) and the empty-model-picker symptom.
