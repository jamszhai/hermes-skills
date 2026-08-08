---
name: cc-switch-hermes-config
description: "Manage CC Switch integration with Hermes Agent — config paths, duplicate provider fixes, DB queries, and custom_providers management."
version: 1.4.0
---

# CC Switch and Hermes Configuration Management

CC Switch (cc-switch.exe) is a multi-tool model manager that also manages Hermes custom providers. It writes `custom_providers` to config.yaml.

## Key Paths

| Item | Path |
|------|------|
| CC Switch binary | `C:\Users\<user>\AppData\Local\Programs\CC Switch\cc-switch.exe` |
| CC Switch DB | `~/.cc-switch/cc-switch.db` (on Windows: may resolve to `C:\Users\<user>\.cc-switch\` or `AppData\Local\.cc-switch\` depending on how CC Switch was installed) |
| Hermes config (Desktop App) | `C:\Users\<user>\AppData\Local\hermes\config.yaml` |
| Hermes config (link path) | `~/.hermes/config.yaml` |

**DB path tip**: on this user's Windows install, CC Switch DB is at `C:\\Users\\jams_\\\\.cc-switch\\\\cc-switch.db` (not `AppData\\\\Local`). Try `~/.cc-switch/cc-switch.db` or `C:\\Users\\\\<user>\\\\.cc-switch\\\\cc-switch.db` first; fall back to `AppData\\\\Local\\\\` only if the first path fails.

**Config path pitfall**: Windows desktop setups commonly have **two** Hermes config files, and they are **not auto-synced**:
- `C:\Users\<user>\AppData\Local\hermes\config.yaml`  — Hermes Desktop working copy
- `C:\Users\<user>\.hermes\config.yaml`  — link/history/fallback copy

If CC Switch reads `~/.hermes/config.yaml` while Hermes is using the `AppData\Local\hermes` path with a different file, CC Switch can believe the config is still corrupted even after rebuilding the AppData copy. Always check both paths when diagnosing missing-button / duplicate-key symptoms.

## Duplicate `custom_providers` Key Bug

**Fixed in CC Switch v3.16.1.** GitHub Issue #2973, PR #3267. The fix handles CRLF-aware section detection and adds "self-heal" logic to tolerate duplicates on read and clean them on write.

**If still affected** (pre-v3.16.1 or corrupted configs):

**Symptoms**:
- Hermes/CC Switch reports duplicate-key YAML parse failure for `custom_providers`
- CC Switch UI shows the custom provider, but Start/Switch/config action buttons are missing or greyed out, so the model cannot be launched from the UI
- `hermes model` picker does not list the CC Switch-added providers

**Why UI buttons disappear**: CC Switch cannot parse a corrupted Hermes config, so it cannot build the valid provider list needed to render working model actions.

**Recovery** (if still affected): See "Rebuild Hermes config from CC Switch DB" below. After rebuild, restart Hermes so provider changes take effect.

**Pitfall: `hermes model` may not persist.** The interactive `hermes model` command can be session-scoped — it may change the current session's model without updating the `default:` field in `config.yaml`. After switching, always verify with `hermes status` or `grep 'default:' config.yaml`. If it hasn't persisted, use the reliable CLI way to make it sticky:

```bash
hermes config set model.default <provider-name>
hermes config set model.provider <provider-name>
```

This writes directly to config.yaml and survives restarts. Do NOT use `patch` to edit config.yaml directly — the write tool refuses security-sensitive config paths. Always use `hermes config set` instead.

## Recovery: Rebuild Hermes config from CC Switch DB

Preferred workflow: rebuild Hermes Desktop config from the CC Switch database, so CC Switch keeps its own copy and Hermes always receives a clean file.

Windows-proven command (use absolute path for reliability on this install):
```bash
python "C:\\Users\\jams_\\AppData\\Local\\hermes\\skills\\cc-switch-hermes-config\\references\\sync_cc_switch_to_desktop.py"
```
Cygpath variant may fail on Git Bash paths — prefer the absolute `C:\\` path directly.

After rebuild, restart Hermes so provider changes take effect.

## CC Switch database repairs

If rebuild alone does not restore Hermes provider buttons, the DB rows can be structurally incomplete. These are runnable DB fixes for `app_type='hermes'` rows in `C:\Users\<user>\.cc-switch\cc-switch.db`:

```python
import sqlite3, json
from pathlib import Path

db = Path(r'C:\Users\<user>\.cc-switch\cc-switch.db')
con = sqlite3.connect(str(db))
cur = con.cursor()

cur.execute("SELECT id, settings_config FROM providers WHERE app_type='hermes'")
rows = cur.fetchall()
for pid, settings in rows:
    s = json.loads(settings)
    s.setdefault('name', pid)
    cur.execute(
        'UPDATE providers SET settings_config=?, is_current=1 WHERE id=?',
        (json.dumps(s, ensure_ascii=False), pid),
    )
con.commit()
con.close()
```

Why this fixes UI:
1. CC Switch sometimes writes `settings_config` with an empty string `name`, which prevents provider cards from rendering action buttons.
2. Hermes provider rows are not always auto-activated; set `is_current=1` unless you are intentionally versioning providers.

## Before-Launch Guard (wrapper)

Before launching or switching Hermes, run the rebuild:

```bash
hermes-preflight hermes-sync
```

If `hermes-preflight` is unavailable, call the rebuild script directly.
For Hermes restart, see `references/hermes-launch.md`.

## DB Queries

```sql
-- List all hermes providers
SELECT id, name, settings_config, meta
FROM providers WHERE app_type = 'hermes';

-- List endpoints
SELECT * FROM provider_endpoints WHERE app_type = 'hermes';
```

## Architecture

See `references/cc-switch-architecture.md`.

## Codex Provider 404 / 400: Model Name Mapping Issues

When Codex CLI sends a request through the CC Switch proxy and gets:

```
unexpected status 404 Not Found: CC Switch local proxy failed while handling Codex endpoint /responses.
Provider: <provider>; model: <model_name>; upstream_status: HTTP 404; cause: model is not found
```

or

```
unexpected status 400 Bad Request: ... upstream_status: HTTP 400; cause: invalid tool_call_id
```

**Root cause — two distinct failure modes**:
- **404**: The model name Codex sends (e.g. `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`) does not match any model the upstream recognizes.
- **400 `invalid tool_call_id`**: The model IS found and auth passes, but the CC Switch Responses→Chat conversion emits a `tool_call_id` the upstream rejects. **In v3.16.5 this is regression Issue #4973** (NOT #4143 — #4143 was the older model-remap issue). #4973 is specific to certain Chat-Completions providers/models (e.g. routing Codex → SenseNova on `deepseek-v4-flash`); other providers (miniMax `gpt-5.4-mini`, `agens-ai`) work fine on the same version. Switching provider or downgrading to v3.16.4 avoids it.

### Architecture

The latest Codex CLI uses the **Responses API** (`/v1/responses`) but many third-party providers only support **Chat Completions** (`/v1/chat/completions`). CC Switch's local proxy at `127.0.0.1:15721` converts between the two protocols:

1. Codex sends `POST /v1/responses` with `model: "gpt-5.5"` → CC Switch proxy
2. Proxy rewrites `/v1/responses` to `/v1/chat/completions` (Responses-to-Chat conversion)
3. Proxy forwards to upstream with model name (may or may not be remapped — intermittent)
4. Upstream Chat response → proxy converts back to Responses format

### The `model_provider = "custom"` Trade-off

**Key finding**: The `model_provider` section controls **two different things** in Codex, and the optimal choice depends on the priority:

| Format | API request model name | Model picker dropdown |
|--------|----------------------|---------------------|
| **Flat** (no `model_provider`) | ✅ Uses `model = "<name>"` as configured — CC Switch proxy sees the real upstream model name (e.g. `deepseek-v4-flash`). | ❌ **Empty** — Codex does not show models for providers without a `[model_providers]` section. |
| **`model_provider = "custom"`** | ❌ Codex sends **internal names** (`gpt-5.5`, `gpt-5.4`) in the request body, ignoring the `model` line. CC Switch proxy forwards these upstream → 404. | ✅ Shows the model(s) from `model_catalog_json`. |

**When to use each:**

- **Use flat format** (no `model_provider`) when the CC Switch proxy can handle the model name mapping (most stable). The model picker will be empty, but API calls work.
- **Use `model_provider = "custom"` format** when you NEED the model picker dropdown. But you MUST also model-map in CC Switch or accept intermittent 404/400 errors from CC Switch bugs #4143.

**Flat format** (for API-correctness priority):
```toml
model = "deepseek-v4-flash"          # actual upstream model name
base_url = "http://127.0.0.1:15721/v1"
wire_api = "responses"
```

**`model_provider` format** (for model-picker priority):
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
*Note: with this format, Codex sends `model: "deepseek-v4-flash"` in some requests and internal names in others (intermittent — CC Switch bug #4143).*

### Root Cause: CC Switch Live Config Management

CC Switch's live config management (`meta.commonConfigEnabled = true`) actively rewrites Codex config.toml on every provider activation — and regenerates the `model_provider = "custom"` format. Even after manually fixing config.toml, CC Switch overwrites it on the next sync.

**Fix — disable live config management in the CC Switch DB**:

```python
import sqlite3, json

con = sqlite3.connect(str(r'C:\Users\<user>\.cc-switch\cc-switch.db'))
cur = con.cursor()
cur.execute("SELECT id, settings_config, meta FROM providers WHERE app_type='codex' AND name='<provider-name>'")
pid, raw_settings, raw_meta = cur.fetchone()
s = json.loads(raw_settings)
m = json.loads(raw_meta)

# 1. Disable live config management
m['commonConfigEnabled'] = False
m['endpointAutoSelect'] = False

# 2. Simplify config — flat format, no model_provider/custom section
s['config'] = 'base_url = "http://127.0.0.1:15721/v1"\nwire_api = "responses"\nmodel = "<actual_upstream_model>"\n'

# 3. Clean modelCatalog to only the upstream model
s['modelCatalog'] = {
    'models': [{'model': '<actual_upstream_model>', 'displayName': '<Display Name>'}]
}

cur.execute('UPDATE providers SET settings_config=?, meta=? WHERE id=?',
            (json.dumps(s, ensure_ascii=False), json.dumps(m, ensure_ascii=False), pid))
con.commit()
con.close()
```

Then write config.toml manually (see below). Also update the proxy_live_backup table to prevent CC Switch restoring the old config from backup on next restart.

### Diagnosis Steps

1. **Check config.toml format** at `~/.codex/config.toml`:
   - `model_provider = "custom"` + `[model_providers.custom]` → **broken format**
   - `model = "<name>"` at top level directly → **correct format**

2. **Check CC Switch DB meta**:
   ```bash
   sqlite3 ~/.cc-switch/cc-switch.db "SELECT id, meta FROM providers WHERE app_type='codex' AND name='<name>'"
   ```
   - `meta.commonConfigEnabled = true` → CC Switch will overwrite config.toml

3. **Check proxy request logs** for actual model name sent upstream:
   ```sql
   SELECT model, request_model, status_code, error_message 
   FROM proxy_request_logs ORDER BY created_at DESC LIMIT 20;
   ```
   - `model` (upstream) == `request_model` (Codex) both as `gpt-5.x` → model NOT being remapped
   - `model == "deepseek-v4-flash"` but `request_model == "gpt-5.4"` → model IS being remapped (working)

### Fix (config.toml)

Write `~/.codex/config.toml` with flat format. Preserve existing sections (marketplaces, plugins, mcp_servers) but rewrite the model config header:

```toml
model = "deepseek-v4-flash"                # actual upstream model name
base_url = "http://127.0.0.1:15721/v1"     # CC Switch proxy — NOT the upstream URL
wire_api = "responses"
disable_response_storage = true
model_reasoning_effort = "medium"

[model_providers]
[marketplaces...]
# ... (preserve all existing sections unchanged)
```

### Known CC Switch Bugs

| Issue | Description | Status |
|-------|-------------|--------|
| #4143 | Model name not reliably remapped on `/responses` route — intermittent 404/400 | Open |
| #4973 | **v3.16.5 regression**: `invalid tool_call_id` (HTTP 400) when routing Codex → SenseNova on `deepseek-v4-flash` (Chat-Completions providers). v3.16.4 worked. Switching provider or downgrading to v3.16.4 avoids it. | Open |
| #3980 | Leaving a tier blank on third-party endpoints forwards literal model name → 404 | Fixed v3.16.3 |

### 401 `PROXY_MA*AGED` Error: Proxy Forwards to OpenAI

**Error pattern**:
```
unexpected status 401 Unauthorized: Incorrect API key provided: PROXY_MA*AGED
url: https://api.openai.com/v1/responses
cf-ray: a193df0e987fbf9e-LAX
```

This is NOT an OpenAI key problem — it means the CC Switch proxy is **forwarding Codex requests to OpenAI** instead of the configured upstream (e.g. sensenova).

**Root cause**: the `proxy_config` table has `live_takeover_active = 0`:

| Column | Value | Meaning |
|--------|-------|---------|
| `proxy_enabled` | `1` | Proxy server is running ✓ |
| `enabled` (routing) | `1` | Codex routing is enabled ✓ |
| `live_takeover_active` | `0` | **Not active** — proxy accepts requests but routes them to OpenAI as default fallback |

**Fix — set `live_takeover_active = 1`** in the DB:

```python
import sqlite3
con = sqlite3.connect(str(r'C:\Users\<user>\.cc-switch\cc-switch.db'))
cur = con.cursor()
cur.execute('UPDATE proxy_config SET live_takeover_active=1 WHERE app_type="codex"')
con.commit()
con.close()
```

Or in CC Switch UI: **Routing** page → toggle Codex routing OFF → ON (reset activates the takeover).

**Triage** — quick check from DB:
```sql
SELECT proxy_enabled, enabled, live_takeover_active 
FROM proxy_config WHERE app_type = 'codex';
```
Expected: three `1`s.

**Distinguishable from**:
- Real 401 (bad upstream key) — URL is the upstream API, not `api.openai.com`
- 404 model not found — model name wrong but routed to correct upstream
- 503 distributor — gateway/health issue

### Verification

After the fix:
1. Decide which priority to optimize for (API correctness vs model picker)
2. Apply the corresponding config format (flat or `model_provider = "custom"`)
3. Restart Codex terminal session
4. Send a test prompt
5. Check proxy request logs: `model = "deepseek-v4-flash"` with `status_code = 200`
6. Verify config.toml was not overwritten by CC Switch on next provider switch

### config.toml TOML Error → "Windows 安装未完成" + empty model picker

**This is a DIFFERENT root cause from the bugs above and the most common real cause of
the merged ChatGPT/Codex "完成 Windows 设置 → 安装未完成" loop. It is NOT bug #32149
(UAC never pops) — that is a red herring unless the app log shows a failed elevation.**

CC Switch live-config management rewrites `~/.codex/config.toml`. If any line is an
invalid TOML string (e.g. a `notify` path in double quotes whose `\U`/`\A`/`\c`
backslashes TOML reads as malformed unicode escapes), the WHOLE app config fails to
parse. The app log (`Packages\OpenAI.Codex_*\LocalCache\Local\Codex\Logs\codex-desktop-*.log`)
shows:
```
failed to load configuration: C:\Users\jams_\.codex\config.toml:11:17: too few unicode value digits, expected unicode hexadecimal value
Invalid TOML document: invalid unicode escape
```
Because config won't parse, `windowsSandbox/setupStart` (the "Windows setup" step)
fails → surfaces as "安装未完成". Symptom twin of bug #32149, different cause.

**Diagnose:**
```python
import tomllib
try:
    with open(r'C:\Users\jams_\.codex\config.toml','rb') as f: tomllib.load(f)
    print('TOML OK')
except Exception as e:
    print('TOML BROKEN:', e)   # the line:col points at the bad string
```

**Fix:** edit the offending line to a TOML literal string (single quotes → backslashes
NOT treated as escapes). Keep the CC Switch proxy routing (`base_url`, `model`) intact.
Then re-run the tomllib check — it must print OK. Re-open ChatGPT normally (Start menu).

**Empty "自定义模型" picker even after config is valid — read this carefully:**

There are TWO different causes; conflating them wastes cycles.

1. **Proxy takeover not active** (`proxy_config.live_takeover_active = 0` for codex).
   Symptom: ChatGPT won't even finish "Windows setup" / shows no proxy-routed models.
   Fix: set `live_takeover_active = 1` and restart CC Switch — see the 401 section.
   (In the 2026-07-12 session the "完成 Windows 设置 → 安装未完成" loop was actually a
   TOML syntax error in config.toml — see the next section — but live_takeover=0 also
   produces a related "Windows 授权/完成设置" re-prompt when CC Switch starts first.)

2. **Upstream model-gating (the REAL reason custom models are hidden in the merged
   ChatGPT/Codex desktop GUI).** CC Switch's official FAQ ("Can't See Custom Models in
   the Codex Desktop App?", v3.16.1+, Applies to v3.16.5) states this is **NOT a CC
   Switch bug** — it is the **upstream closed-source client's own model-gating**:
   the desktop model picker decides which models to show based on your **official
   login identity**. When it can't detect an official ChatGPT/Codex login state, it
   forces the picker back to the official default and **hides the custom models
   configured in config.toml**. Upstream marked "exposing custom-provider models in
   the desktop GUI" as **not planned**, so CC Switch cannot fix it at the GUI level.
   The CLI `codex /model` menu and request routing DO see the custom models — only
   the desktop GUI picker is gated.

   **Confirmed by code inspection**: `cc-switch-model-catalog.json` is referenced **0
   times** in the merged ChatGPT desktop app's installed JS. The merged app's model
   picker reads the server-side model list + built-in runtime marketplace, NOT that
   local catalog file. So adding `model` fields to the catalog (as was tried) does
   NOT make models appear in the merged-app GUI — the gating blocks them regardless.

   **Official mitigation (the only GUI-level fix):** keep the official login state so
   the gating passes your custom models through:
   - Log in once with an official ChatGPT/Codex account in Codex (Free is enough).
   - In CC Switch: **Settings → General → Codex App Enhancements → Keep official login
     when switching third-party providers** (OFF by default — turn it ON). This makes
     CC Switch preserve `~/.codex/auth.json` official login state when switching to a
     third-party provider (writes only the 3rd-party key to config.toml; the preserved
     official token is never sent to the 3rd party).
   - Enable local routing + route Codex through it for Chat-Completions providers
     (required for DeepSeek/Kimi/MiniMax).
   - Fully quit and restart ChatGPT/Codex.
   - Gotcha: the official login token EXPIRES after several days idle → picker goes
     empty again; re-login to the official account to restore.

   Note: `~/.codex/auth.json` showing only `OPENAI_API_KEY: "PROXY_MANAGED"` means the
   official token was overwritten by CC Switch takeover (happens when the "Keep official
   login" toggle is OFF) — that is exactly what triggers the gating/hidden models.

Full transcript + triage order: `references/session-2026-07-12-chatgpt-setup-incomplete-config-toml.md`.

### Prevention

When adding a new Codex provider:
- Use a **built-in preset** if available (DeepSeek, Kimi, agnes-ai) — these handle the trade-off correctly
- If using a custom provider, choose the format based on priority:
  - **Flat format**: API calls stable but model picker empty
  - **`model_provider` format**: model picker works but may have intermittent 404 (CC Switch bug #4143); the 400 `invalid tool_call_id` is a SEPARATE v3.16.5 regression (#4973) affecting Chat-Completions providers like SenseNova `deepseek-v4-flash` — switch provider or downgrade to v3.16.4 to avoid it.
- If CC Switch keeps regenerating the `model_provider` format, disable live config management via `meta.commonConfigEnabled = false`
- `modelCatalog` should only contain the actual upstream model(s), not auto-discovered extraneous models
- The `model_catalog_json` file must have BOTH a `slug` field AND a `model` field matching the `model` value in config.toml (CC Switch generates `slug` but omits `model` — add it manually)
- After setup, `~/.codex/config.toml` should show the real upstream model name, not `gpt-5.x`

Distinguishable from:
- Duplicate `custom_providers` YAML failures (no UI buttons) — see separate section above.
- 503 distributor errors (gateway channel unavailable) — see separate section above.
- Auth errors (401 / missing API key).

## 503 Distributor / No Available Channel Errors

When CC Switch returns:

  API Error: 503 No available channel for model `<model>` under group `<group>`

this indicates **CC Switch's own routing/gateway layer** has no active channel mapped for that model, not a Hermes config error.

Common causes:
- The model name is missing from the CC Switch channel mapping for the requested group.
- The target channel is down or rate-limited in CC Switch.
- The group `default` distributor has no healthy backends for that model.

Triage order:
1. If CC Switch UI shows the provider card but buttons are missing, treat as duplicate/corrupt YAML: run `sync_cc_switch_to_desktop.py` and restart Hermes.
2. If UI shows the provider and buttons, but requests return 503 distributor errors, the config is healthy; the failure is on the CC Switch side.
3. Check the CC Switch UI for model/channel mapping, group configuration, and service health.
4. If needed, restart the CC Switch gateway or re-login the provider.

Distinguishable from:
- duplicate `custom_providers` YAML failures (missing buttons)
- auth errors (401 / missing key)
- provider offline errors (connection refused)

## Incident Notes

- See `references/session-2026-06-14-duplicate-fix.md` for symptoms and recovery from the 2026-06-14 duplicate-key incident.
- See `references/session-2026-06-18-503-agnes-flash.md` for a 503 distributor-side failure on `agnes-ai` model `Agnes-2.0-Flash`.
- See `references/session-2026-07-10-codex-404-model-mapping.md` for Codex 404 model name mapping diagnosis and fix on sensenova.
- See `references/session-2026-07-11-codex-401-proxy-managed.md` for Codex 401 `PROXY_MA*AGED` error when `live_takeover_active = 0`.
- See `references/session-2026-07-12-codex-400-tool-call-id-regression.md` for the v3.16.5 `invalid tool_call_id` 400 regression (Issue #4973, provider-specific; switching provider or downgrading to v3.16.4 avoids it).
