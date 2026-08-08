---
name: hermes-windows-config
description: "Troubleshoot and manage Hermes Agent configuration on Windows — config file locations, HERMES_HOME resolution, AppData vs ~/.hermes path mismatches, custom_providers not appearing, and third-party tool integration issues."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [hermes, windows, config, troubleshooting, setup]
    related_skills: [hermes-agent, systematic-debugging]
---

# Hermes Windows Configuration

## Overview

On Windows, Hermes Agent can read its configuration from different paths depending on how it was installed (CLI pip install vs Desktop GUI app). This often leads to confusion when:
- You add a `custom_providers` entry but it doesn't show up in `/model`
- A third-party tool (like CC Switch, model switchers) writes config changes that Hermes doesn't pick up
- `hermes config` shows different settings than you expected

The root cause is almost always a **config file path mismatch** — there are two different `config.yaml` files and Hermes reads the wrong one.

## Windows Config Paths

| Install Method | `HERMES_HOME` location | Config file path |
|---------------|----------------------|-----------------|
| **Desktop GUI App** | `%LOCALAPPDATA%\hermes` | `C:\Users\<user>\AppData\Local\hermes\config.yaml` |
| **CLI / pip install** | `~\.hermes` (default) | `C:\Users\<user>\.hermes\config.yaml` |
| **Custom HERMES_HOME** | Whatever you set | `<HERMES_HOME>\config.yaml` |

### Finding the actual config path

```bash
hermes config path
```

This always returns the path Hermes is **actually reading**. Trust this over intuition.

### Check both locations

```bash
# The AppData location (Desktop install)
ls "/c/Users/<user>/AppData/Local/hermes/config.yaml"

# The ~/.hermes location (CLI install / third-party tools)
ls /c/Users/<user>/.hermes/config.yaml
```

## Common Issues

### Third-party tools write to the wrong config

Tools like **CC Switch**, model switchers, or config managers often assume Hermes uses `~/.hermes/config.yaml` (the CLI default). But the Hermes Desktop App on Windows sets `HERMES_HOME` to `%LOCALAPPDATA%\\hermes`, so changes written to `~/.hermes/config.yaml` are invisible to the running instance.

**Symptom:** You add a provider/model in CC Switch → it shows in `~/.hermes/config.yaml` → but `hermes model` doesn't list it.

**Fix — one-time merge + permanent symlink:**

```bash
# 1. Find the real config
hermes config path

# 2. Merge custom_providers from the ghost config into the real config
#    (manually copy the `custom_providers:` block)

# 3. Set HERMES_HOME as a persistent user env var so future tools find it
setx HERMES_HOME "C:\Users\<user>\AppData\Local\hermes"

# 4. Remove the ghost config and create a symlink from old to new location
#    (run in an elevated cmd prompt:)
#    mklink "C:\Users\<user>\.hermes\config.yaml" "C:\Users\<user>\AppData\Local\hermes\config.yaml"

# 5. Verify
ls -la ~/.hermes/config.yaml   # should show -> AppData/Local/hermes/...
hermes config path              # should return the AppData path
hermes model                    # should list the custom providers
```

**Why this works:** After step 4, CC Switch writes to `~/.hermes/config.yaml` which is now a symlink to the real config. Hermes sees every change immediately on next session start. The `HERMES_HOME` env var ensures any tool that checks `$HERMES_HOME` finds the right directory.

### Custom providers not appearing in /model

If you added `custom_providers` to the config but they don't show up:

1. Find the actual config: `hermes config path`
2. Verify `custom_providers` exists in that file: `cat "$(hermes config path)"`
3. If not there, copy/add the `custom_providers` section to the correct file
4. Start a new session (`/reset` or exit and relaunch)

### Dual config files contain different settings

Sometimes you end up with two config files — one in `AppData\Local\hermes\` and one in `~\.hermes\` — that contradict each other. The `HERMES_HOME`-pointed file wins. The other is a ghost config.

**Fix:** Merge the relevant sections (`custom_providers`, `model`, `provider`) from the ghost config into the real one, or just delete the ghost to avoid confusion.

## Custom Providers Config Format

The `custom_providers` section in `config.yaml` follows this format:

```yaml
custom_providers:
- name: my-provider
  base_url: https://api.example.com/v1
  api_key: sk-xxx...xxx
  api_mode: chat_completions       # or completions
  models:
    model-id-1:
      name: Display Name 1
    model-id-2:
      name: Display Name 2
  model: model-id-1                 # default model for this provider
```

After adding, run `hermes model` or `/model` in a new session to see and select the provider.

## Verification Checklist

- [ ] Run `hermes config path` — know the real config location
- [ ] Check `custom_providers` exists in the real config
- [ ] Verify API keys and base URLs are correct
- [ ] Start a new session (`/reset` or relaunch)
- [ ] Run `hermes model` to confirm providers appear
- [ ] If problem persists, compare both possible config files side by side

## CC Switch 重复 custom_providers 键故障

当 config.yaml 中出现重复的 `custom_providers:` 键时，YAML 解析失败，CC Switch 的"添加"/"启动"按钮也会失效。

### 症状
```
配置错误: Failed to parse Hermes config as YAML: duplicate entry with key "custom_providers"
```

### 根因
CC Switch 写入 hermes config 时采用**追加**策略，不是替换。如果 config.yaml 中已存在 `custom_providers`（手动合并的或 CC Switch 之前写入的），再次写入就会产生两个同名顶级键。

CC Switch 在**每次启动时**都会尝试导入 hermes providers，如果 config.yaml 有重复键，导入失败。

### 诊断
```bash
grep -n '^custom_providers:' <config.yaml>
# 如果返回 2+ 行 → 有重复
```

### 修复

**Step 1: 清空 config.yaml 中的所有 custom_providers**

```python
import yaml
path = "<config.yaml>"
with open(path, 'r') as f:
    data = yaml.safe_load(f)
if 'custom_providers' in data:
    del data['custom_providers']
with open(path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

**Step 2: 从 CC Switch 数据库读取 provider 信息**

```python
import sqlite3, json
conn = sqlite3.connect("~/.cc-switch/cc-switch.db")
cursor = conn.cursor()
cursor.execute("SELECT id, name, settings_config FROM providers WHERE app_type='hermes'")
for row in cursor.fetchall():
    print(dict(row))
conn.close()
```

**Step 3: 根据 DB 数据重建 custom_providers**，然后写入 config.yaml。

**Step 4: 重启 CC Switch**——它现在会干净地写入，不会再有重复。
**Step 5: 清理 CC Switch 数据库缓存的旧记录**

即使 config.yaml 已修复，CC Switch 可能仍持有从损坏配置中解析出的旧 provider 行。重启后若"启动"按钮仍缺失，清空其缓存让它重新导入：

```python
import sqlite3
db_path = r'C:\Users\<user>\.cc-switch\cc-switch.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('DELETE FROM providers WHERE app_type = "hermes"')
cur.execute('DELETE FROM provider_endpoints WHERE app_type = "hermes"')
conn.commit()
conn.close()
# 重新打开 CC Switch → 它会从修复后的 config.yaml 重新导入
```

### 预防
- 如果 CC Switch 管理 providers，**不要手动合并** `custom_providers` 到 config.yaml，让 CC Switch 统一处理。
- 修改前先用 `grep -n '^custom_providers:'` 确认重复键数量，确保只有一个。

## Changing Model / Provider Programmatically

When you need to switch models or providers from a script or automated session (non-interactive), `hermes model` refuses to work through pipes:

```
Error: 'hermes model' requires an interactive terminal.
It cannot be run through a pipe or non-interactive subprocess.
```

**Correct approach — use `hermes config set` for each key:**

```bash
# 1. Find the real config path
hermes config path

# 2. Set the provider (e.g., switch to a custom provider named "Mass")
hermes config set model.provider "custom:Mass"

# 3. Set the default model within that provider
hermes config set model.default "spark-4.0-max"

# 4. Verify
hermes config | grep -A5 "Model"
```

**Provider naming convention:** Custom providers use `custom:<name>` where `<name>` matches the `name` field in the `custom_providers` list (not the display name). You can discover registered custom providers by reading the `custom_providers` block from the config file or by running `hermes model` interactively.

**⚠ `patch` is blocked for `config.yaml`.** The security guard refuses writes to `C:\Users\jams_\AppData\Local\hermes\config.yaml` (and `~/.hermes/config.yaml`). Always use `hermes config set KEY VAL` instead of file patches for config changes.

**Changes require a new session.** Model/provider config is read at session start. After changing it, use `/reset` or relaunch Hermes for the change to take effect.

## Common Pitfalls

1. **Editing the wrong config.yaml.** Always verify with `hermes config path` first.
2. **Expecting config changes to apply mid-session.** Config is read at session start. Use `/reset` or relaunch.
3. **Third-party tools writing to `~/.hermes/`.** The Desktop GUI app uses `%LOCALAPPDATA%\hermes\`. These are different files on Windows.
4. **Not checking `HERMES_HOME` env var.** If set, it overrides the default path completely.
6. **Creating symlinks without Admin rights.** On Windows, `New-Item -ItemType SymbolicLink` requires Administrator privileges (or Developer Mode). Use `mklink` from an elevated Command Prompt instead: `mklink "src" "target"`.
7. **Verifying the wrong evidence.** `ls -la` showing a symlink arrow (`->`) confirms it's active. `hermes config path` returning the AppData path confirms Hermes is reading the right file. Check both.
