# Session 2026-07-12 — ChatGPT+Codex "Windows 安装未完成" caused by config.toml TOML error

## Symptom
Merged ChatGPT desktop app (ships inside `OpenAI.Codex` MSIX package) opens and shows
"完成 Windows 设置" (Finish Windows setup) → clicking it → "Windows 安装未完成"
(Windows installation incomplete). Retry / Continue-with-limited-access both dead.
Looks identical to openai/codex bug #32149 (UAC never pops). But UAC bug #32149 was a
red herring here.

Separately: after the app finally opens, the右下角 "自定义模型" (custom model) picker
shows only the word "模型" with no `deepseek-v4-flash` entry, even though
`cc-switch-model-catalog.json` contains it.

## Root cause (real)
`C:\Users\jams_\.codex\config.toml` had a TOML syntax error on line 11 — the `notify`
array used a double-quoted string whose backslashes (`\U`, `\A`, `\c`) TOML parsed as
unicode escapes that were malformed:

```
notify = [ "C:\Users\jams_\AppData\Local\OpenAI\Codex\runtimes\...codex-computer-use.exe", "turn-ended" ]
```

App log signature (in `Packages\OpenAI.Codex_*\LocalCache\Local\Codex\Logs\*\codex-desktop-*.log`):
```
failed to load configuration: C:\Users\jams_\.codex\config.toml:11:17: too few unicode value digits, expected unicode hexadecimal value
Invalid TOML document: invalid unicode escape
... windowsSandbox/setupStart ... failed to load configuration ...
```

Because the app cannot parse its own config, the "Windows integration setup"
(`windowsSandbox/setupStart`) fails wholesale → surfaces as "安装未完成".
NOT a UAC/permission/region issue.

## Fix
Convert the `notify` line to a TOML literal string (single quotes → backslashes NOT
treated as escapes). Keep CC Switch proxy routing intact.

Before:
```toml
notify = [ "C:\Users\jams_\AppData\Local\OpenAI\Codex\runtimes\cua_node\ecfc0d9aa02807e3\bin\node_modules\@oai\sky\bin\windows\codex-computer-use.exe", "turn-ended" ]
```
After:
```toml
notify = [ 'C:\Users\jams_\AppData\Local\OpenAI\Codex\runtimes\cua_node\ecfc0d9aa02807e3\bin\node_modules\@oai\sky\bin\windows\codex-computer-use.exe', "turn-ended" ]
```

Verify with Python 3.11 tomllib (no third-party dep):
```python
import tomllib
with open(r'C:\Users\jams_\.codex\config.toml','rb') as f:
    d = tomllib.load(f)
print('OK', d.get('model'), d.get('model_providers',{}).get('custom',{}).get('base_url'))
```
Expected: TOML loads; `base_url = http://127.0.0.1:15721/v1` preserved; model picker
catalog (`cc-switch-model-catalog.json`) untouched.

## Second, independent cause of BOTH symptoms: codex `live_takeover_active = 0`
Even with config.toml valid, the codex proxy takeover was never activated
(`proxy_config.live_takeover_active = 0`, `enabled = 0`). CC Switch startup log shows
`应用列表: ["claude"]` — only Claude was taken over. Consequences:
- Opening ChatGPT after CC Switch re-triggers the "完成 Windows 设置" prompt.
- The "自定义模型" picker stays empty (catalog not injected into the UI).

Fix: set the takeover bits in the DB, then RESTART CC Switch (DB change is only
re-read on CC Switch launch; do not force-kill CC Switch — user prohibits that):
```python
import sqlite3
con = sqlite3.connect(r'C:\Users\jams_\.cc-switch\cc-switch.db')
con.execute("UPDATE proxy_config SET enabled=1, live_takeover_active=1 WHERE app_type='codex'")
con.commit(); con.close()
```
Then user: close ChatGPT → close CC Switch (tray → quit) → reopen CC Switch → reopen ChatGPT.

## Triage order for "安装未完成" on merged ChatGPT/Codex
1. Read latest `codex-desktop-*.log` under the app's LocalCache Logs. If it says
   `config.toml:...: too few unicode value digits` / `invalid unicode escape` →
   fix config.toml (above). This is the most common real cause; bug #32149 UAC is a
   distraction unless the log explicitly shows a failed UAC/elevation attempt.
2. If config.toml is clean, check `proxy_config` for codex: `SELECT enabled,
   live_takeover_active FROM proxy_config WHERE app_type='codex'`. If not both 1,
   set them and restart CC Switch.
3. Only if both above are clean and it still loops → investigate the real bug #32149
   (try launching from Start menu normally; do NOT right-click Run-as-admin the exe
   inside WindowsApps — that gives "cannot access the specified device/path").

## Gotchas
- Do NOT launch `ChatGPT.exe` directly from `C:\Program Files\WindowsApps\...\app\`
  via "Run as administrator" — MSIX-protected path → "Windows cannot access the
  specified device, path, or file". Always launch from the Start menu (AppExecutionAlias).
- The merged app's main chat model dropdown lists OpenAI-official GPT-5.x (chatgpt.com
  account) and NEVER shows third-party models. Third-party models only appear in the
  Codex/agent "自定义模型" picker, and only when codex proxy takeover is active.
- config.toml is rewritten by CC Switch live-config management; after fixing, confirm
  it stays valid on next CC Switch sync (re-run the tomllib check).
