"""
cc-switch-hermes-sync.py
Background watcher: fixes CC Switch's duplicate custom_providers bug.
Monitors ~/.hermes/config.yaml, removes trailing duplicate blocks,
and syncs the cleaned config to the Hermes Desktop App config path.

Usage:
    python scripts/cc-switch-hermes-sync.py

Add to Windows Startup to run automatically after login.
"""
import time
import yaml
import os
from datetime import datetime

SRC = os.path.expanduser(r'~/.hermes/config.yaml')
DST = os.path.expandvars(r'%LOCALAPPDATA%/hermes/config.yaml')
INTERVAL = 1.0  # seconds
LOG_TAG = '[hermes-sync]'


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'{LOG_TAG} {ts} {msg}', flush=True)


def has_duplicate_cp(path):
    """Return True if file has more than 1 top-level 'custom_providers:' key."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        count = sum(
            1 for line in content.split('\n')
            if line.strip() == 'custom_providers:' and line and not line[0].isspace()
        )
        return count > 1
    except Exception:
        return False


def remove_duplicate_cp(path):
    """Keep only the first custom_providers block, discard trailing duplicates."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        first_idx = None
        second_idx = None
        for i, line in enumerate(lines):
            s = line.strip()
            if s == 'custom_providers:' and line and not line[0].isspace():
                if first_idx is None:
                    first_idx = i
                else:
                    second_idx = i
                    break

        if second_idx is None:
            return False

        # Keep everything before the second block, trim trailing blanks
        new_lines = lines[:second_idx]
        while new_lines and new_lines[-1].strip() == '':
            new_lines.pop()
        new_lines.append('\n')

        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        log(f'Removed duplicate custom_providers (line {second_idx + 1}) from {path}')
        return True
    except Exception as e:
        log(f'Error fixing {path}: {e}')
        return False


def sync_files():
    """Read SRC, fix duplicates, write cleaned result to DST."""
    if not os.path.exists(SRC):
        return False

    try:
        with open(SRC, 'r', encoding='utf-8') as f:
            src_data = yaml.safe_load(f)
    except Exception as e:
        log(f'Cannot parse SRC: {e}')
        return False

    if has_duplicate_cp(SRC):
        if remove_duplicate_cp(SRC):
            try:
                with open(SRC, 'r', encoding='utf-8') as f:
                    src_data = yaml.safe_load(f)
            except Exception:
                return False

    try:
        with open(DST, 'w', encoding='utf-8') as f:
            yaml.dump(src_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        log(f'Cannot write DST: {e}')
        return False


def main():
    log(f'Watching {SRC} -> {DST}')
    log('Press Ctrl+C to stop')
    if not os.path.exists(SRC):
        log(f'WARNING: {SRC} does not exist yet. Waiting for CC Switch to create it...')

    while True:
        try:
            sync_files()
        except Exception as e:
            log(f'Loop error: {e}')
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
