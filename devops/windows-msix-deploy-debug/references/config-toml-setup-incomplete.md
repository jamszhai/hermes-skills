# config.toml TOML error → "Windows 安装未完成" (merged ChatGPT/Codex)

## Why this is a separate root cause from bug #32149
The merged ChatGPT+Codex app's "完成 Windows 设置 → 安装未完成" loop is usually blamed on
openai/codex bug #32149 (UAC never fires). On THIS machine the actual recurring cause is a
**TOML syntax error in `~/.codex/config.toml`** that CC Switch live-config management wrote.
The app cannot parse its own config, so its first-run Windows-integration step
(`windowsSandbox/setupStart`) fails → identical symptom, different (and agent-fixable) cause.

## Diagnosis
Latest log: `C:\Users\<user>\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\Codex\Logs\*\codex-desktop-*.log`
Grep for: `too few unicode value digits`, `invalid unicode escape`, `failed to load configuration`.
Confirm also with Python 3.11 (no deps):
```python
import tomllib
try:
    with open(r'C:\Users\jams_\.codex\config.toml','rb') as f: tomllib.load(f)
    print('TOML OK')
except Exception as e:
    print('TOML BROKEN:', e)   # e gives line:col of the bad string
```

## Typical bad line (CC Switch-written `notify` path in double quotes)
```toml
notify = [ "C:\Users\jams_\AppData\Local\OpenAI\Codex\runtimes\cua_node\ecfc0d9aa02807e3\bin\node_modules\@oai\sky\bin\windows\codex-computer-use.exe", "turn-ended" ]
```
The `\U`, `\A`, `\c` are read as malformed unicode escapes.

## Fix
Rewrite that line as a TOML **literal string** (single quotes → backslashes NOT escapes):
```toml
notify = [ 'C:\Users\jams_\AppData\Local\OpenAI\Codex\runtimes\cua_node\ecfc0d9aa02807e3\bin\node_modules\@oai\sky\bin\windows\codex-computer-use.exe', "turn-ended" ]
```
Keep CC Switch proxy routing (`base_url = http://127.0.0.1:15721/v1`, `model`) intact.
Re-run the tomllib check — must print OK. Re-open ChatGPT from the Start menu (NOT Run-as-admin on the exe).

## Empty "自定义模型" picker (third symptom)
Even with config valid, the codex proxy takeover may be inactive:
`SELECT enabled, live_takeover_active FROM proxy_config WHERE app_type='codex'` in
`~/.cc-switch/cc-switch.db`. If not both 1, set them and RESTART CC Switch (DB only re-read
on launch; do not force-kill CC Switch — user prohibits that). User sequence: close ChatGPT →
close CC Switch (tray quit) → reopen CC Switch → reopen ChatGPT.

## Gotchas
- Never "Run as administrator" the exe under `C:\Program Files\WindowsApps\...` — MSIX-protected
  path → "Windows cannot access the specified device, path, or file". Use the Start menu shortcut.
- The main chat model dropdown lists OpenAI-official GPT-5.x (chatgpt.com account) and NEVER
  third-party models. Third-party models appear only in the Codex "自定义模型" picker, and only
  when codex proxy takeover is active.
- CC Switch rewrites config.toml on sync; re-verify validity after the next CC Switch provider switch.
