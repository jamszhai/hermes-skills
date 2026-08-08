# CC Switch — Hermes Config Path Mismatch

## Background

[CC Switch](https://github.com/farion1231/cc-switch) is a Windows GUI tool (Tauri/Rust) that centrally manages AI model provider configurations across multiple code agents: Claude Code, Codex CLI, Google Gemini, OpenCode, and **Hermes Agent**.

It stores its data in a SQLite database at `~/.cc-switch/cc-switch.db`.

## The Problem

CC Switch writes Hermes `custom_providers` to `~/.hermes/config.yaml`, but the Hermes Desktop GUI App on Windows reads its config from `%LOCALAPPDATA%\hermes\config.yaml` (which is `C:\Users\<user>\AppData\Local\hermes\config.yaml`).

These are **two different files**. The running Hermes instance never sees CC Switch's changes.

## Diagnosis Steps

### 1. Find CC Switch config store

```bash
# CC Switch stores its data here:
ls ~/.cc-switch/
# => cc-switch.db, settings.json, logs/, backups/
```

### 2. Examine CC Switch's Hermes providers

```python
import sqlite3, json
db = sqlite3.connect(r"C:\Users\<user>\.cc-switch\cc-switch.db")
cur = db.cursor()

# List all Hermes providers CC Switch knows about
cur.execute("""
    SELECT id, name, settings_config, website_url
    FROM providers WHERE app_type = 'hermes'
""")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")
    print(json.dumps(json.loads(row[2]), indent=2))
```

### 3. Locate the actual Hermes config

```bash
hermes config path
# => C:\Users\<user>\AppData\Local\hermes\config.yaml
```

### 4. Compare to the ghost config

```bash
cat ~/.hermes/config.yaml         # what CC Switch wrote
cat "$(hermes config path)"      # what Hermes actually reads
```

### 5. Merge custom_providers into the real config

If the ghost config has `custom_providers` that the real config lacks, copy that section into the real config file.

## Full Fix Recipe

For a permanent fix so CC Switch writes to the correct location:

### 1. Merge custom_providers into the real config

Copy the `custom_providers:` block from the ghost config into the real config. Use `python -c "import yaml; ..."` or `hermes config edit`.

### 2. Set HERMES_HOME as a persistent Windows user env var

```cmd
setx HERMES_HOME "C:\Users\<user>\AppData\Local\hermes"
```

This ensures any tool that checks `$HERMES_HOME` finds the correct directory.

### 3. Create a symlink

**Run this in an elevated (Admin) cmd prompt:**

```cmd
del "C:\Users\<user>\.hermes\config.yaml"
mklink "C:\Users\<user>\.hermes\config.yaml" "C:\Users\<user>\AppData\Local\hermes\config.yaml"
```

After this, CC Switch writes to `~/.hermes/config.yaml` → which resolves through the symlink → to the real AppData config. Hermes sees every change on next session start.

### 4. Verify

```bash
ls -la ~/.hermes/config.yaml     # should show -> AppData/Local/hermes/...
hermes config path                # should return AppData path
hermes model                      # should list custom providers
```

## Safety Note

CC Switch writes only `custom_providers` and `model.provider` sections to the config — it does not overwrite other config keys. The symlink is safe as long as this behavior holds. If CC Switch updates to write the full config, verify it preserves unrelated YAML keys.

## Verification (manual merge, no symlink)

After manual merging:

```bash
hermes config path           # confirm correct file
hermes model                 # should show the new providers
```

Start a new session (`/reset` or relaunch the app) — provider changes are read at session start.

## DB Schema (key tables)

| Table | Purpose |
|-------|---------|
| `providers` | Provider definitions per app type (claude, codex, gemini, hermes) |
| `provider_endpoints` | API endpoint URLs per provider |
| `provider_health` | Health check results per provider |
| `stream_check_logs` | Stream connectivity test results |
| `model_pricing` | 148+ model pricing entries |
| `settings` | Key-value config (e.g. `official_providers_seeded`) |
| `proxy_config` | Local proxy settings (for Claude/Codex/Gemini only, not Hermes) |
