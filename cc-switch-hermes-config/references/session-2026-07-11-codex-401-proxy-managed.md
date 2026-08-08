# Codex 401 PROXY_MA*AGED — `live_takeover_active = 0`

Date: 2026-07-11
Provider: sensenova (商汤科技)
Model: deepseek-v4-flash

## Symptom

Codex CLI returns 401 with the proxy-managed placeholder key going to OpenAI:

```
unexpected status 401 Unauthorized: Incorrect API key provided: PROXY_MA*AGED.
url: https://api.openai.com/v1/responses
cf-ray: a193df0e987fbf9e-LAX
```

The key `PROXY_MA*AGED` is CC Switch's internal placeholder — it has never been a valid OpenAI key and is NOT meant to be sent to OpenAI.

## Root Cause

CC Switch proxy_config table had `live_takeover_active = 0` for the `codex` row:

```sql
-- From proxy_config table (columns: app_type, proxy_enabled, listen_address, listen_port, enable_logging, enabled, auto_failover_enabled, ..., live_takeover_active)
('codex', 1, '127.0.0.1', 15721, 1, 1, 0, ..., 0)
```

Meaning:
- `proxy_enabled = 1` → proxy server is running ✓
- `enabled = 1` → Codex routing is enabled ✓  
- `live_takeover_active = 0` → **live takeover NOT active** ✗

When `live_takeover_active = 0`, the proxy accepts Codex requests but falls back to routing them to OpenAI instead of the configured upstream provider (sensenova). The placeholder key `PROXY_MA*AGED` gets sent to OpenAI, which naturally rejects it.

Compare to the `claude` row which shows how it looked for a working provider.

## Fix

```python
import sqlite3
con = sqlite3.connect(str(r'C:\Users\jams_\.cc-switch\cc-switch.db'))
cur = con.cursor()
cur.execute('UPDATE proxy_config SET live_takeover_active=1 WHERE app_type="codex"')
con.commit()
con.close()
```

Or via CC Switch UI: Routing → toggle Codex routing OFF → ON.

## Triage Steps

1. Check proxy_config in CC Switch DB:
   ```sql
   SELECT proxy_enabled, enabled, live_takeover_active 
   FROM proxy_config WHERE app_type = 'codex';
   ```
2. Expected: all three = `1`. Any `0` means a layer is missing.
3. Also verify provider is active (`is_current=1`):
   ```sql
   SELECT name, is_current FROM providers WHERE app_type='codex';
   ```
4. Verify config.toml `base_url = "http://127.0.0.1:15721/v1"`

## Distinguishing

| Signal | Means |
|--------|-------|
| URL = `api.openai.com` with `PROXY_MA*AGED` key | Proxy fallback → `live_takeover_active = 0` |
| URL = upstream API, 401 | Real auth failure — bad API key in provider config |
| URL = `api.openai.com` with real-looking key | Codex bypassing proxy entirely |