---
name: cc-switch-preflight
description: "Run Hermes-related preflight checks before using CC Switch or starting Hermes — rebuild Hermes config from CC Switch DB, detect duplicate YAML keys, and log request logs from CC Switch proxy."
version: 1.0.0
---

# CC Switch Hermes Preflight

Use this to keep Hermes config healthy when CC Switch manages providers.

## When to run

- Before starting Hermes after changing providers in CC Switch
- When Hermes reports `duplicate entry with key "custom_providers"`
- Periodically, as part of Hermes startup

## Commands

### Rebuild Hermes config from CC Switch DB

Windows-proven form:
```bash
python "$(cygpath -w "$HOME/AppData/Local/hermes/skills/cc-switch-hermes-config/references/sync_cc_switch_to_desktop.py")"
```

This rewrites `AppData\Local\hermes\config.yaml` from `~/.cc-switch\cc-switch.db`, so CC Switch’s append mode won’t corrupt Hermes.

### Diagnose duplicates

Quick check — count how many times `custom_providers:` appears in config:
```bash
grep -c 'custom_providers:' "$HOME/AppData/Local/hermes/config.yaml"
```
Expected: 1. Anything > 1 means duplicates exist (CC Switch append bug).

Note: the former `diagnostic.py` script no longer exists in this skill.

### Import request logs from CC Switch proxy

CC Switch captures some Hermes traffic. To read it:
```bash
python "$(cygpath -w "$HOME/AppData/Local/hermes/skills/cc-switch-preflight/scripts/read_request_logs.py")"
```

## Recovery

If Hermes reports duplicate/corrupt YAML:
1. Run the rebuild command above
2. Restart Hermes

## Related

- `cc-switch-hermes-config` for provider collection and DB queries
- Issue tracked upstream: CC Switch cannot reliably rewrite Hermes config; best practice is rebuild-before-use.
