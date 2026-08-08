# 2026-06-18: agnes-ai 503 Distributor Error

## Symptom
- User invoked CC Switch provider "agnes-ai" model `Agnes-2.0-Flash`
- Error: `503 No available channel for model Agnes-2.0-Flash under group default (distributor)`
- Gateway URL observed in error: `127.0.0.1:15721`

## Diagnostic Findings
- `claude auth status --text` showed Anthropic API token, confirming Hermes→proxy auth is configured.
- This is not a Hermes config/auth issue because:
  - the Hermes `config.yaml` contains `custom_providers` for `agnes-ai` with valid `base_url` and `api_key`
  - model-level auth inside Hermes is not involved; the failure came before reaching the provider's API
- Root cause is CC Switch gateway/router distributor unable to route `Agnes-2.0-Flash` to any channel under the default group.

## Resolution Path
1. Confirm CC Switch provider card for `agnes-ai` has channels configured for `Agnes-2.0-Flash`.
2. Check the default group membership in CC Switch.
3. If the model was recently renamed or reclassifed, re-add/update the channel mapping.
4. If the provider gateway is started but has no healthy backend, restart CC Switch or re-login the provider.

## Cross-Reference
- Related 2026-06-14 incident about duplicate `custom_providers` keys: missing buttons, YAML parse failures, rebuild via `sync_cc_switch_to_desktop.py`.
