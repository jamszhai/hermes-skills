# CC Switch Duplicate `custom_providers` Bug

## Symptom

CC Switch startup log:
```
WARN Failed to import Hermes providers: 配置错误: Failed to parse Hermes config as YAML: duplicate entry with key "custom_providers"
WARN Failed to import Hermes MCP: 配置错误: Failed to parse Hermes config as YAML: duplicate entry with key "custom_providers"
```

Clicking "添加"/"启动" in CC Switch's Hermes tab throws the same error. No models have "启动" (start) buttons.

Observed error patterns across sessions:
1. Duplicate top-level `custom_providers`
2. Duplicate top-level `model:`
3. Corrupted nested list items inside `custom_providers[0]`: a single provider entry gets two `base_url` keys (e.g. lines 628 and 630), making YAML unparseable even when top-level keys are unique.

Any of these produce `Failed to parse Hermes config as YAML`.

## Root cause

CC Switch hardcodes a write to `~/.hermes/config.yaml`. On every launch/action it appends a **complete second** `custom_providers:` block to end-of-file rather than merging. `yaml.safe_load` silently returns the last duplicate value, so the file "parses OK" under lenient loaders but is irrecoverable under strict parsing.

CC Switch never reads `~/.hermes/config.yaml` for the fix — it writes to it as its **output** path, pulling source data from its SQLite DB (`~/.cc-switch/cc-switch.db`).

## Diagnosis

```python
import yaml
path = r"C:\Users\<user>\.hermes\config.yaml"
with open(path) as f:
    lines = f.readlines()
dup_keys = [i for i, l in enumerate(lines)
            if l.strip() == "custom_providers:" and not l[0].isspace()]
print(f"Top-level custom_providers at lines: {[i+1 for i in dup_keys]}")
# [627, 666] means two full blocks
```

## Fix (line-based block removal)

```python
path = r"C:\Users\<user>\.hermes\config.yaml"
lines = open(path).readlines()
first = last = None
for i, line in enumerate(lines):
    if line.strip() == "custom_providers:" and not line[0].isspace():
        if first is None:
            first = i
        last = i
lines = lines[:last]
while lines and lines[-1].strip() in ("", "#"):
    lines.pop()
lines.append("\n")
open(path, "w").writelines(lines)
```

## Re-populate CC Switch DB so it skips import

CC Switch logs `"<app> already has providers; live import skipped"` when DB rows exist. After fixing the YAML, insert back into the DB so CC Switch stops writing during startup:

```python
import sqlite3, json
from datetime import datetime

db_path = r"C:\Users\<user>\.cc-switch\cc-switch.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
# Read current providers from the cleaned YAML
with open(r"C:\Users\<user>\AppData\Local\hermes\config.yaml") as f:
    import yaml; data = yaml.safe_load(f)
now_ms = int(datetime.now().timestamp() * 1000)

for p in data.get("custom_providers", []):
    settings = {
        k: p[k] for k in ("name", "base_url", "api_key")
        if k in p
    }
    if "api_mode" in p: settings["api_mode"] = p["api_mode"]
    if "models" in p: settings["models"] = p["models"]
    if "model" in p: settings["model"] = p["model"]
    c.execute("""INSERT OR REPLACE INTO providers
        (id, app_type, name, settings_config, category, created_at, sort_index, meta, is_current)
        VALUES (?, 'hermes', ?, ?, 'custom', ?, 0, '{}', 0)""",
        (p["name"], p["name"], json.dumps(settings), now_ms))
conn.commit()
conn.close()
```

## Prevention: decouple `~/.hermes/config.yaml`

Write an independent file at `~/.hermes/config.yaml` so CC Switch writes there harmlessly. Hermes Desktop App on Windows reads only `AppData\Local\hermes\config.yaml` because `HERMES_HOME=C:\Users\<user>\AppData\Local\hermes`.

```python
import shutil, os
src = r"C:\Users\<user>\AppData\Local\hermes\config.yaml"
dst = r"C:\Users\<user>\.hermes\config.yaml"
if os.path.exists(dst):
    os.remove(dst)
# Prefer hardlink (same inode, zero disk overhead); fall back to copy
try:
    os.link(src, dst)
except OSError:
    shutil.copy2(src, dst)
```

A hardlink on Windows requires Developer Mode or admin elevation; `shutil.copy2` works without either but will drift if Hermes rewrites its config.
