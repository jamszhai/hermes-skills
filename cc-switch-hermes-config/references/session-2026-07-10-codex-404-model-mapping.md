# Codex 404/400: sensenova Model Mapping — Session 2026-07-10

## Error Chain

Three distinct failures over two debug cycles:

### Cycle 1 — 404 "model is not found"

```
unexpected status 404 Not Found: CC Switch local proxy failed while handling
Codex endpoint /responses. Provider: sensenova; model: gpt-5.5;
upstream_status: HTTP 404; cause: model is not found
```

**Partial fix**: Changed `model = "gpt-5.5"` → `deepseek-v4-flash` in both CC Switch DB and config.toml. Added `modelCatalog`. This resolved 404s but uncovered deeper issue — CC Switch overwrote config.toml with old format.

### Cycle 2 — 400 "invalid tool_call_id" + model rollback

After restart, Codex config.toml had `model = "gpt-5.4"` (CC Switch live config management reverted the change). Proxy request logs showed:
- Some requests correctly remapped (`deepseek-v4-flash` upstream → 200 ✅)
- Other requests NOT remapped (`gpt-5.4` / `gpt-5.5` sent upstream → 400 `invalid tool_call_id` ❌)
- **Intermittent model remapping** — CC Switch proxy bug #4143

## Environment

| Item | Value |
|------|-------|
| Provider | sensenova (`https://token.sensenova.cn/v1`) |
| Upstream model | `deepseek-v4-flash` |
| CC Switch DB | `C:\Users\jams_\.cc-switch\cc-switch.db` |
| Codex config | `C:\Users\jams_\.codex\config.toml` |
| Proxy | `127.0.0.1:15721` (CC Switch local routing, Codex routing enabled) |

## Root Cause: `model_provider = "custom"` Trap

The Codex config format was:

```toml
model_provider = "custom"       # ← THIS triggers Codex's internal model selection
model = "gpt-5.4"               # ← Codex IGNORES this line
[model_providers.custom]
name = "custom"
wire_api = "responses"
requires_openai_auth = true
base_url = "http://127.0.0.1:15721/v1"
```

When `model_provider = "custom"` is set, Codex uses its own internal model selection logic (`gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`) regardless of what `model` says. The CC Switch proxy receives these internal names and forwards them to sensenova, which doesn't recognize them.

## What DID NOT Fully Work

| Attempt | Result |
|---------|--------|
| Just changing model in config.toml | Overwritten by CC Switch live config management on next sync |
| Setting model = "deepseek-v4-flash" in DB + keeping commonConfigEnabled = true | CC Switch regenerates `model_provider = "custom"` format |
| Only fixing modelCatalog | CC Switch auto-populates with extra models from upstream `/v1/models` |

## What WORKED

Three changes together:

### 1. DB: Disable live config management

```python
m['commonConfigEnabled'] = False
m['endpointAutoSelect'] = False
```

### 2. DB: Flat config format (no `model_provider = "custom"`)

```python
s['config'] = 'base_url = "http://127.0.0.1:15721/v1"\nwire_api = "responses"\nmodel = "deepseek-v4-flash"\n'
s['modelCatalog'] = {'models': [{'model': 'deepseek-v4-flash', 'displayName': 'DeepSeek V4 Flash'}]}
```

### 3. config.toml: Match the flat format

```toml
model = "deepseek-v4-flash"
base_url = "http://127.0.0.1:15721/v1"
wire_api = "responses"
disable_response_storage = true
model_reasoning_effort = "medium"
```

## Key DB Queries Used

```sql
-- List all providers by type
SELECT id, app_type, name, settings_config, meta FROM providers;

-- Proxy config (routing status)
SELECT * FROM proxy_config;

-- Model catalog (Codex built-in model names)
SELECT * FROM model_pricing;

-- Provider health (circuit breaker state)
SELECT * FROM provider_health;

-- Proxy request logs (what model was actually sent upstream)
SELECT model, request_model, status_code, error_message 
FROM proxy_request_logs ORDER BY created_at DESC LIMIT 20;

-- Live backup (CC Switch restore point)
SELECT * FROM proxy_live_backup;
```

## Provider Comparison

| Aspect | agnes-ai (working) | sensenova (broken → fixed) |
|--------|-------------------|---------------------------|
| config format | Flat: `model = "agnes-2.0-flash"` | Custom → Flat |
| modelCatalog | Single entry, correct | Auto-populated → cleaned to one entry |
| commonConfigEnabled | true (OK for presets) | true → **false** |
| Codex sends in request | `agnes-2.0-flash` | `gpt-5.x` → `deepseek-v4-flash` |

## Remaining Known Bug

CC Switch Issue #4143: Responses-to-Chat conversion produces malformed `tool_call_id` for some providers, causing 400 errors. This is open. The fix above addresses the model name issue; if tool call conversion still fails, it's a CC Switch-side bug that needs their update.