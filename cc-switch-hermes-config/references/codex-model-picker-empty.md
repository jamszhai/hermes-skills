# Codex Model Picker Empty — Diagnosis and Fix

## Problem

Codex CLI model picker (`/model`) shows no models. The dropdown is empty even though:
- `model_catalog_json` points to a valid JSON file
- The JSON file has models with `slug` and `display_name`
- `model = "deepseek-v4-flash"` is set in config.toml

## Root Cause

**Missing `model_provider` section.** When Codex doesn't see `model_provider = "custom"` + `[model_providers.custom]` in config.toml, it doesn't know there's a custom provider and shows no models in the picker.

## Trade-off

| Config format | API calls | Model picker |
|-------------|-----------|-------------|
| Flat (no `model_provider`) | ✅ Correct model name sent upstream | ❌ Empty |
| `model_provider = "custom"` | ❌ Codex sends internal names (gpt-5.x) | ✅ Shows models |

## Fix

Add the `model_provider` section to `~/.codex/config.toml`:

```toml
model = "deepseek-v4-flash"
model_provider = "custom"
model_catalog_json = "cc-switch-model-catalog.json"

[model_providers.custom]
name = "custom"
wire_api = "responses"
requires_openai_auth = true
base_url = "http://127.0.0.1:15721/v1"
```

## Additional Notes

- `model_catalog_json` path can be relative (resolves against `$CODEX_HOME` aka `~/.codex/`)
- The JSON catalog's model object MUST have BOTH a `slug` field AND a `model` field, both matching the `model` value in config.toml. CC Switch generates the file with `slug` but NOT `model` — you must add it manually:
  ```python
  cat['models'][0]['model'] = cat['models'][0]['slug']
  ```
- The `visibility` field should be `"list"` (not `"hidden"`) for the model to appear in the picker
- Known Codex bug: model picker filters out models from local `model_catalog_json` — Issue #19694
- After Codex/ChatGPT merged desktop app, the config file path is still `~/.codex/config.toml`