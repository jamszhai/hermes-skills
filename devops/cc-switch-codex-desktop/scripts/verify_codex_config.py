#!/usr/bin/env python3
"""Verify the merged ChatGPT/Codex desktop app's CC Switch routing + config state.
Reads ~/.codex/config.toml, ~/.codex/cc-switch-model-catalog.json, and
~/.cc-switch/cc-switch.db. Reports Rust-TOML-risk lines, catalog model fields,
and proxy takeover state. Pure read-only; no writes.

Run: python verify_codex_config.py
"""
import json, os, sqlite3, re

HOME = os.path.expanduser("~")
CONFIG = os.path.join(HOME, ".codex", "config.toml")
CATALOG = os.path.join(HOME, ".codex", "cc-switch-model-catalog.json")
DB = os.path.join(HOME, ".cc-switch", "cc-switch.db")

print("=== config.toml ===")
try:
    raw = open(CONFIG, encoding="utf-8", errors="replace").read()
    # Rust TOML is strict: double-quoted strings with bare backslash + letter
    # (e.g. \U \A \c) are illegal unicode escapes. Flag them.
    risky = re.findall(r'"[^"]*\\[UAac][^"]*"', raw)
    if risky:
        print("  [RISK] Rust-TOML illegal escape in double-quoted strings:")
        for r in risky[:5]:
            print("    ", r)
    else:
        print("  no obvious backslash-escape risk in double quotes")
    # light parse attempt (python is lenient; just shows top-level intent)
    m = re.search(r'model\s*=\s*"([^"]+)"', raw)
    mp = re.search(r'model_provider\s*=\s*"([^"]+)"', raw)
    bu = re.search(r'base_url\s*=\s*"([^"]+)"', raw)
    print(f"  model={m.group(1) if m else None}  model_provider={mp.group(1) if mp else None}")
    print(f"  base_url={bu.group(1) if bu else None}  (127.0.0.1:15721 = CC Switch proxy, by design)")
except FileNotFoundError:
    print("  not found")

print("\n=== cc-switch-model-catalog.json ===")
try:
    d = json.load(open(CATALOG, encoding="utf-8"))
    for mod in d.get("models", []):
        slug = mod.get("slug"); model = mod.get("model")
        flag = "OK" if model else "MISSING model field (GUI may show blank)"
        print(f"  slug={slug}  model={model}  -> {flag}")
except FileNotFoundError:
    print("  not found")

print("\n=== proxy DB (codex takeover state) ===")
try:
    c = sqlite3.connect(DB); cur = c.cursor()
    cur.execute("SELECT app_type,enabled,live_takeover_active,proxy_enabled,listen_address,listen_port FROM proxy_config WHERE app_type='codex'")
    r = cur.fetchone()
    if r:
        print(f"  codex: enabled={r[1]} live_takeover={r[2]} proxy_enabled={r[3]} addr={r[4]}:{r[5]}")
    else:
        print("  no codex row in proxy_config")
    cur.execute("SELECT key,value FROM settings WHERE key='currentProviderCodex' OR key='preserveCodexOfficialAuthOnSwitch' OR key='enableLocalProxy'")
    for k, v in cur.fetchall():
        print(f"  settings.{k} = {v}")
except FileNotFoundError:
    print("  not found")
