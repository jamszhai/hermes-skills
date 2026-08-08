# Config Path Mismatch — Third-Party Tool Debugging

## Problem

Third-party model managers (CC Switch, etc.) write Hermes `custom_providers` to a path that Hermes doesn't read. Models added via the tool never appear in `/model` or `hermes model`.

## Diagnosis

```bash
# 1. Find where Hermes ACTUALLY reads config
hermes config path

# 2. Check the third-party tool's database/log for where it writes
# For CC Switch: check ~/.cc-switch/logs/cc-switch.log
# CC Switch manages: claude, codex, gemini, hermes, opencode, openclaw
# Its DB: ~/.cc-switch/cc-switch.db

# 3. Compare paths
#   CC Switch writes to: ~/.hermes/config.yaml
#   Hermes Desktop App reads: C:\Users\<user>\AppData\Local\hermes\config.yaml
```

## CC Switch Specifics

- **Binary**: `C:\Users\<user>\AppData\Local\Programs\CC Switch\cc-switch.exe`
- **Version**: ~3.16.1
- **DB**: `~/.cc-switch/cc-switch.db` (SQLite)
- **Settings**: `~/.cc-switch/settings.json`
- **Providers table**: `providers` table with `app_type='hermes'` columns
- **Logs**: `~/.cc-switch/logs/cc-switch.log`

### CC Switch Hermes Providers

CC Switch stores Hermes providers as `providers` rows with `app_type='hermes'`:

```sql
SELECT id, name, settings_config, meta
FROM providers
WHERE app_type = 'hermes';
```

Each row has a `settings_config` JSON with `base_url`, `api_key`, `api_mode`, `models[]`.

## Fix Pattern

### 1. Merge providers (one-shot)

```python
import yaml

# Read the real Hermes config (from `hermes config path`)
with open("REAL_CONFIG_PATH", "r") as f:
    config = yaml.safe_load(f)

# Read the old/wrong config (from the third-party tool's output dir)
with open("OLD_CONFIG_PATH", "r") as f:
    old = yaml.safe_load(f)

# Merge custom_providers if they exist
if "custom_providers" in old and old["custom_providers"]:
    config["custom_providers"] = old["custom_providers"]

with open("REAL_CONFIG_PATH", "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

### 2. Create symlink (persistent)

```bash
# On Windows (requires admin):
# mklink "~/.hermes/config.yaml" "<real-path>/config.yaml"

# On Linux/Mac:
ln -s "/real/path/to/config.yaml" "~/.hermes/config.yaml"
```

### 3. Set HERMES_HOME

```bash
# Windows (user env):
setx HERMES_HOME "C:\Users\<user>\AppData\Local\hermes"

# Linux/Mac:
export HERMES_HOME="$HOME/.hermes"  # or wherever it should be
```

## CC Switch Critical Bug: Duplicate `custom_providers` on Every Write

CC Switch v3.16.1 on Windows has a known bug: **it appends** `custom_providers` to `~/.hermes/config.yaml` instead of replacing the existing block. The result is two (or more) top-level `custom_providers:` keys, which causes:

```
配置错误: Failed to parse Hermes config as YAML: duplicate entry with key "custom_providers"
```

This happens on:
- App startup (CC Switch tries to "import" Hermes providers)
- Clicking "Add" in the Hermes provider UI
- Clicking "Start/Launch" for any Hermes model

### Why symlinks/hardlinks don't fully solve it

- **Symlinks**: Require Developer Mode or admin on Windows. Without it, `mklink` fails with WinError 1314.
- **Hardlinks**: Work without admin. BUT CC Switch writes append to the same inode, still creating duplicates in the shared file.
- **Separate copies**: If `~/.hermes/config.yaml` and `AppData\\Local\\hermes\\config.yaml` are independent, CC Switch corrupts its own copy and Hermes is unaffected. But Hermes won't see CC Switch's providers either.

### Observed failure modes

1. `duplicate entry with key "custom_providers"` — two top-level sections
2. `duplicate entry with key "model"` — two top-level `model:` blocks
3. `duplicate entry with key "base_url"` (or `"name"`, etc.) at line X column Y — a **single list item under `custom_providers`** got two providers merged into one record from a partial append

The third form requires more than stripping the second top-level block; the corrupted list item has duplicate keys and must be rebuilt.

### Working Solution: Watcher + Separate Copies

The reliable pattern on Windows:

1. **Keep configs separate**: Hermes reads `AppData\Local\hermes\config.yaml` (`HERMES_HOME`). Let `~/.hermes/config.yaml` be CC Switch's scratch file.
2. **Watcher script**: A background Python process monitors `~/.hermes/config.yaml` for duplicate `custom_providers` blocks. When detected, it removes the trailing duplicate and syncs the cleaned result to `AppData\Local\hermes\config.yaml`.

Watcher script template: `scripts/cc-switch-hermes-sync.py` (see below).

3. **Auto-start watcher**: Register the watcher in Windows Startup so it runs after login.

### Watcher Script

Template available at `scripts/cc-switch-hermes-sync.py`. Key logic:

```python
# Key snippet from the watcher
def has_duplicate_cp(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return sum(1 for line in content.split('\n')
               if line.strip() == 'custom_providers:' and line and not line[0].isspace()) > 1

def fix_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    first_idx = second_idx = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s == 'custom_providers:' and line and not line[0].isspace():
            if first_idx is None: first_idx = i
            else: second_idx = i; break
    if second_idx is None: return False
    new_lines = lines[:second_idx]
    while new_lines and new_lines[-1].strip() == '': new_lines.pop()
    new_lines.append('\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    return True
```

### One-Shot Reset (When Corrupted)

```python
import yaml, sqlite3

db = sqlite3.connect(os.path.expanduser(r'~\.cc-switch\cc-switch.db'))
for table in ['providers', 'provider_endpoints', 'provider_health', 'stream_check_logs']:
    db.execute(f'DELETE FROM {table} WHERE app_type = \"hermes\"')
db.commit(); db.close()

for path in [os.path.expanduser(r'~\.hermes\config.yaml'),
             os.path.expandvars(r'%LOCALAPPDATA%\hermes\config.yaml')]:
    if os.path.exists(path):
        with open(path) as f: data = yaml.safe_load(f)
        data.pop('custom_providers', None)
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

## Prevention

When a third-party tool adds providers that Hermes can't see:
1. Always run `hermes config path` first to confirm the real path
2. Don't assume `~/.hermes/` is the canonical location
3. Check if `HERMES_HOME` is set and matches expectations
4. Create a symlink from the tool's expected path to the real path
