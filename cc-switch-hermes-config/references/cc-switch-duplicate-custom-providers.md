# CC Switch Duplicate `custom_providers` Fix

## Problem

After CC Switch writes hermes `custom_providers` to config.yaml, and a previous manual merge also added them, the config has **two `custom_providers` keys** at the top level. YAML parser fails to load the config.

### Error

```
Failed to parse Hermes config as YAML: duplicate entry with key "custom_providers"
```

All hermes models in CC Switch fail to start.

## Diagnosis

```python
import yaml
with open("CONFIG_PATH", "r") as f:
    data = yaml.safe_load(f)
print("custom_providers in keys:", "custom_providers" in data)

# Check for duplicate top-level keys:
with open("CONFIG_PATH", "r") as f:
    for i, line in enumerate(f, 1):
        if line.strip() == "custom_providers:":
            print(f"Line {i}: {line.rstrip()}")
```

## Root Cause

CC Switch manages Hermes providers by writing `custom_providers` to the config file. If providers were manually merged into config.yaml beforehand (as a workaround for the CC Switch path-mismatch issue), then CC Switch's next write creates a duplicate top-level `custom_providers` key.

## Fix

### Option 1: Let CC Switch Manage (Recommended)

Delete `custom_providers` from config.yaml so CC Switch controls it:

```python
import yaml
path = "CONFIG_PATH"
with open(path, "r") as f:
    data = yaml.safe_load(f)
if "custom_providers" in data:
    del data["custom_providers"]
with open(path, "w") as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

Then restart CC Switch — it will rewrite `custom_providers` from its DB (`~/.cc-switch/cc-switch.db`, table `providers` where `app_type='hermes'`).

### Option 2: Manual Merge Only

Keep manually merged `custom_providers`, remove CC Switch's written copy. Only works for providers you've manually added; cline and others from CC Switch won't be available.

## Prevention

- When fixing path-mismatch with CC Switch, prefer **symlink** (`~/.hermes/config.yaml -> real-path/config.yaml`) over manual merge. This way CC Switch writes to the right place automatically.
- Never manually merge `custom_providers` if CC Switch manages the same providers.
