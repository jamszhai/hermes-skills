# CC Switch v3.16.5 + Codex Desktop — Verified Reference Notes

## Official FAQ: "Can't See Custom Models in the Codex Desktop App?" (ccswitch.io, applies v3.16.1+)
- Symptom: switch Codex to a third-party/custom model (DeepSeek, Kimi, GLM, MiniMax, aggregator) → the **desktop picker** shows only the official default; the **CLI `codex /model`** works fine.
- Quote: *"This is not a CC Switch local-config problem and not a CC Switch bug — it is the Codex desktop app's (the upstream closed-source client's) own model-gating behavior."*
- Mechanism: the desktop picker decides allowed models from the **current login identity**. No detected official login → forces official default + hides custom models from `config.toml`. Upstream marked GUI exposure of custom-provider models as *not planned*.
- Mitigation: enable **Settings → General → Codex App Enhancements → Keep official login when switching third-party providers** (off by default; persisted as `preserveCodexOfficialAuthOnSwitch` in `~/.cc-switch/settings.json`). CC Switch then keeps `~/.codex/auth.json` official token, writes third-party key into `config.toml`, GUI gating lets custom models through. Preserved token is never sent to the third party.
- Caveats: official login token **expires** after days of non-use → picker empties again; re-login to restore. CLI diagnosis: `codex debug models`.

## v3.16.5 changelog (2026-07-01) highlights
- Centerpiece: native-Responses direct-connect adapted for domestic (Chinese) model providers — generates Codex model catalogs (`~/.codex/cc-switch-model-catalog.json`) so the desktop app can display custom models + their tools, and auto-disables `web_search` for gateways that reject it.
- "Can't see custom models?" rework: when a Codex provider connects via native Responses (`openai_responses`), CC Switch generates the catalog. **Re-save a previously configured native provider once** to regenerate.
- Provider form: **上游格式 (Upstream Format)** selector — `Responses（直连，不转换格式）` vs `Chat Completions（需开启路由接管才能转换为 Chat Completions）`. Chat-Completions providers MUST enable local routing takeover.

## GitHub issue #4973 — v3.16.5 regression: invalid tool_call_id (HTTP 400)
- Setup: CC Switch v3.16.5 (fresh; **v3.16.4 worked**), Codex 26.623.x, provider SenseNova, 上游格式 = Chat Completions (需开启路由), base URL `https://token.sensenova.cn/v1`, models glm-5.2 / deepseek-v4-flash / sensnova-6.7-flash-lite.
- Repro: launch a turn on `deepseek-v4-flash`; after the **first tool call** the turn errors. Same config on `gpt-5.4-mini` (via miniMax) **works**.
- Error: `CC Switch local proxy failed while handling Codex endpoint /responses. Provider: SenseNova; model: deepseek-v4-flash; upstream_status: HTTP 400; cause: invalid tool_call_id` (type invalid_request_error, code 3).
- Root cause (per log): request body reaches `http://127.0.0.1:15721/v1/responses` with real OpenAI Responses payload (`tool_calls[].id` in `call_xxx` format); the **Responses→Chat-Completions translator mangles tool_call_id**, upstream rejects.
- Workarounds: (a) use a model/provider not affected (e.g. miniMax `gpt-5.4-mini`); (b) roll back CC Switch to v3.16.4; (c) wait for upstream patch.
- NOT a user-config error — do not edit config.toml to "fix" it.

## Provider facts verified this session
- SenseNova real endpoint: `https://token.sensenova.cn/v1` (API key format `sk-...`). Direct call returns 401 when key invalid/expired; 502 via CC Switch proxy when the upstream rejects. Localhost `127.0.0.1:15721` in config.toml is CC Switch's proxy — by design.
- CC Switch DB (`~/.cc-switch/cc-switch.db`): `proxy_config` table has `app_type`, `enabled`, `live_takeover_active`, `proxy_enabled`, `listen_address`, `listen_port`; `providers` table has `settings_config` (JSON: auth/config/modelCatalog) and `meta` (JSON: apiFormat, commonConfigEnabled). `settings.json` key `currentProviderCodex` holds the active provider UUID.
