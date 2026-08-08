---
name: cc-switch-codex-desktop
description: Configure and troubleshoot CC Switch together with the merged ChatGPT/Codex desktop app on Windows — fix "Finish setup / Windows 安装未完成" loops, empty custom-model picker, and proxy 400 errors (invalid tool_call_id). Use when the user reports CC Switch not routing third-party models to Codex/ChatGPT, the model picker is empty / models can't be selected, or proxy errors like "CC Switch local proxy failed ... invalid tool_call_id" (HTTP 400). Also covers reading ~/.cc-switch/cc-switch.db and ~/.codex/config.toml for the Codex app.
---

# CC Switch + ChatGPT/Codex Desktop App

## When to use
- User runs CC Switch and the merged ChatGPT desktop app and reports: third-party models don't appear / can't be selected in the picker, "完成 Windows 设置 / 安装未完成" setup loop, or proxy errors such as `CC Switch local proxy failed while handling Codex endpoint /responses ... upstream_status: HTTP 400; cause: invalid tool_call_id`.
- Any investigation touching `~/.codex/config.toml`, `~/.codex/cc-switch-model-catalog.json`, or `~/.cc-switch/cc-switch.db` for the Codex/ChatGPT desktop app.

## Mental model (verify before assuming)
- The merged ChatGPT desktop app IS the **OpenAI.Codex MSIX package** (`OpenAI.Codex_*` under `C:\Program Files\WindowsApps`). There is no separate `OpenAI.ChatGPT` package; `ChatGPT.exe` lives inside the Codex package. App data: `C:\Users\<user>\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\Codex\Logs`.
- CC Switch routing sets `~/.codex/config.toml` `base_url = http://127.0.0.1:15721/v1`. **This localhost address is BY DESIGN (CC Switch local proxy), NOT a misconfiguration.** Do not "fix" it back to a remote URL — that breaks routing. (User twice suspected the localhost address was wrong; it wasn't.)
- config.toml is parsed by a **Rust TOML parser** (Codex is Rust). `Python tomllib` is MORE LENIENT than Rust. A file that parses OK in Python can still fail in Codex with `too few unicode value digits` / `invalid unicode escape`. Rule: avoid backslash escapes in double-quoted strings — use forward-slash paths or single-quoted literals.

## Troubleshooting playbook

### 1. "Finish setup / Windows 安装未完成" loop
ROOT CAUSE is usually a **TOML syntax error in `~/.codex/config.toml`**, NOT a UAC / permission / MSIX-registration problem. Do not burn time re-registering the package or admin-launching the exe — WindowsApps blocks direct admin launch with "无法访问指定设备/路径或文件".
- Symptom: app log shows `failed to load configuration: ... too few unicode value digits` / `Invalid TOML document: invalid unicode escape`, and the `windowsSandbox/setupStart` step fails → "install incomplete".
- The offending line is usually `notify = [ "C:\Users\..." ]` written by CC Switch's takeover (double quotes; `\U`/`\A`/`\c` read as illegal unicode escapes by Rust).
- Fix: rewrite that line with forward slashes (`C:/Users/...`) or a single-quoted literal. Then fully quit and reopen ChatGPT from the Start menu (no admin needed).
- Verify with `scripts/verify_codex_config.py`.

### 2. Custom model picker empty / can't select CC Switch models
This is **upstream Codex desktop gating**, confirmed by the CC Switch FAQ "Can't See Custom Models in the Codex Desktop App?" (ccswitch.io, applies v3.16.1+):
- The desktop GUI picker shows custom models only when it detects an **official ChatGPT/Codex login state**. No official login → picker collapses to the official default and hides the `config.toml` custom models. Upstream marked GUI exposure of custom models as "not planned"; CC Switch cannot fully fix it at the GUI level.
- The generated `~/.codex/cc-switch-model-catalog.json` is consumed by the CLI/catalog path; the desktop GUI picker is gated separately by login identity. (Editing the catalog's `model` field does NOT fix the GUI — wasted effort; see Workflow pitfalls.)
- CLI (`codex debug models` / `/model`) is unaffected and sees custom models correctly.
- Mitigation (official): enable **Settings → General → Codex App Enhancements → Keep official login when switching third-party providers** (off by default; stored as `preserveCodexOfficialAuthOnSwitch` in `~/.cc-switch/settings.json`). Turn it ON, keep an official login, route through local routing, fully quit + restart Codex. The preserved official token is never sent to the third party.

### 3. Proxy error `invalid tool_call_id` (HTTP 400)
- **CC Switch v3.16.5 regression**, GitHub issue #4973. When routing Codex → SenseNova/deepseek-v4-flash via `/responses` local routing, the Responses→Chat-Completions translator mangles `tool_call_id` → upstream 400 after the first tool call. v3.16.4 worked.
- Same config with some other models (e.g. `gpt-5.4-mini` via miniMax) works — it's model/upstream-specific, not universal.
- Workarounds: (a) switch to a provider/model not affected; (b) roll back CC Switch to v3.16.4; (c) wait for upstream patch on #4973.
- Do NOT waste time re-editing config.toml — it's a CC Switch conversion bug, not your config.

## Workflow pitfalls (user explicitly said "不要盲目修" — research first)
- **Research official sources BEFORE patching.** Before editing config/proxy/DB, check ccswitch.io changelog + GitHub issues for the exact error string. The user corrected me for blind-fixing; a catalog `model`-field edit was wasted because the real cause was GUI login-gating, not a missing field.
- **CC Switch overwrites `~/.codex/config.toml` on every takeover.** Hand-edits are clobbered on next launch/provider-switch. To change routing behavior, use the CC Switch UI (provider form → 上游格式 / local routing toggle) or edit the DB (`~/.cc-switch/cc-switch.db` `proxy_config` / `providers` tables) + restart CC Switch.
- **DB state edits** (`enabled`, `live_takeover_active` in `proxy_config`) need a CC Switch restart to take effect; the app recomputes its takeover list at startup from `live_takeover_active`.
- **Never kill CC Switch / ChatGPT processes** unless the user explicitly instructs. Ending a stuck *App's own* process is only acceptable as part of a fix the user is already debugging.
- **`netstat -ano` output is GBK on this host** — don't pipe it into Python `subprocess` (UnicodeDecodeError). Check a port with a `socket.connect` probe instead. Also `search_files` fails on MSIX `Packages` paths (IO error 3); use `execute_code` with `os.walk` / direct file reads.

## Quick reference
- `references/v3165-regression.md` — condensed quotes from the CC Switch FAQ + issue #4973.
- `scripts/verify_codex_config.py` — validate config.toml (Rust-escape heuristics), catalog model fields, and proxy DB state in one shot.
