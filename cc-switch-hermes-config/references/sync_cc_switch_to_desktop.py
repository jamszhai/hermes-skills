"""
Rebuild Hermes Desktop App config.yaml from CC Switch database.
Use this whenever CC Switch corrupts ~/.hermes/config.yaml with duplicate keys/fields.
"""
import os
import sqlite3
import json
import yaml

CC_SWITCH_DB = os.path.expanduser(r'~\.cc-switch\cc-switch.db')
DESKTOP_CONFIG = os.path.expandvars(r'%LOCALAPPDATA%\hermes\config.yaml')


def fetch_hermes_providers_from_db():
    providers = []
    if not os.path.exists(CC_SWITCH_DB):
        return providers
    conn = sqlite3.connect(CC_SWITCH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, settings_config FROM providers WHERE app_type = 'hermes'"
    )
    for row in cursor.fetchall():
        try:
            settings = json.loads(row[2])
            providers.append({
                'name': row[1],
                'base_url': settings.get('base_url', ''),
                'api_key': settings.get('api_key', ''),
            })
        except Exception:
            pass
    conn.close()
    return providers


def rebuild():
    if not os.path.exists(DESKTOP_CONFIG):
        raise FileNotFoundError(f'Hermes config not found: {DESKTOP_CONFIG}')

    with open(DESKTOP_CONFIG, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    config['custom_providers'] = fetch_hermes_providers_from_db()

    with open(DESKTOP_CONFIG, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return config


if __name__ == '__main__':
    config = rebuild()
    print(f'Rebuilt custom_providers: {len(config.get("custom_providers", []))}')
    for p in config.get('custom_providers', []):
        print(f'  - {p["name"]}')
