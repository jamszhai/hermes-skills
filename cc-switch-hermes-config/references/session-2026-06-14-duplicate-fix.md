# Session 2026-06-14 duplicate-fix notes

- Duplicate-entry root cause: CC Switch append/write loop left two `custom_providers` blocks in `~/.hermes/config.yaml` (on Windows that is the same file as `AppData\Local\hermes\config.yaml` when HERMES_HOME points there).
- Symptoms in CC Switch UI: "Failed to parse Hermes config as YAML: duplicate entry with key custom_providers" and all model action buttons disappeared.
- Recovery proven command: `python "$(cygpath -w "$HOME/AppData/Local/hermes/skills/cc-switch-hermes-config/references/sync_cc_switch_to_desktop.py")"`
- After rebuild: restart Hermes.
- Rebuild result this session: 2 providers restored (`agnes-ai`, `Mass`).
- Missing after rebuild: `cline` provider had no `app_type='hermes'` endpoint row in the DB, so the rebuild did not restore it.
- Pitfall: on Windows, relying on manual merges or symlinks breaks because CC Switch re-opens configs in append/repeat mode and can create duplicate list-item fields inside provider blocks (`base_url`, `api_key`).
- Recovery check: after rebuild, verify there is exactly one `custom_providers` top-level key and that it parses cleanly.
