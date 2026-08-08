import sqlite3
import os

CC_SWITCH_DB = os.path.expanduser(r'~/.cc-switch/cc-switch.db')


def main():
    if not os.path.exists(CC_SWITCH_DB):
        print('CC Switch DB not found:', CC_SWITCH_DB)
        return
    conn = sqlite3.connect(CC_SWITCH_DB)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT provider_id, provider_name, app_type, model_used, status, success, http_status, latency_ms, error_message, tested_at
        FROM proxy_request_logs
        ORDER BY tested_at DESC
        LIMIT 50
        """
    )
    rows = cur.fetchall()
    print(f'proxy_request_logs rows: {len(rows)}')
    for row in rows:
        print(row)


if __name__ == '__main__':
    main()
