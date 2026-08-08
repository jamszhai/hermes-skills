#!/usr/bin/env python3
"""Diagnostic: check Hermes config.yaml for duplicate custom_providers keys."""

import os
import sys
import yaml

HERMES_CONFIG = os.path.expanduser(r"C:\Users\jams_\AppData\Local\hermes\config.yaml")


def check_duplicate_keys(filepath):
    """Detect duplicate top-level YAML keys by scanning raw lines."""
    with open(filepath, "r") as f:
        lines = f.readlines()
    results = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        if stripped.endswith(":") and not stripped.startswith("#"):
            key = stripped.rstrip(":").strip()
            results.append((key, i))
    # Find duplicates
    from collections import Counter
    counts = Counter(k for k, _ in results)
    dupes = {k: lines for k, lines in counts.items() if counts[k] > 1}
    return dupes


def main():
    config_path = HERMES_CONFIG
    if not os.path.exists(config_path):
        print(f"Config not found: {config_path}")
        return 1

    print(f"Checking: {config_path}")
    print("=" * 60)

    # Check for duplicate top-level keys
    dupes = check_duplicate_keys(config_path)
    if dupes:
        print(f"FOUND {len(dupes)} duplicate top-level key(s):")
        for key, lines in dupes.items():
            count = len(lines)
            print(f"  - '{key}' appears {count} times")
    else:
        print("No duplicate top-level keys found. Config is clean.")

    # Try to parse YAML
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        print("\nYAML parsing: SUCCESS")
        if data and "custom_providers" in data:
            providers = data["custom_providers"]
            print(f"custom_providers count: {len(providers)}")
        else:
            print("custom_providers: NOT FOUND in config")
    except yaml.YAMLError as e:
        print(f"\nYAML parsing: FAILED — {e}")

    print("\n" + "=" * 60)
    return 0 if not dupes else 1


if __name__ == "__main__":
    sys.exit(main())
