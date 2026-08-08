#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xAI/Grok 接入确定性自检：验证 key 有效、列出可用模型、可选跑一次 web_search 探针。

用于 av-strm-scraper 改模型名 / web_search 用法前的自测，确认未踩弃用 API。

用法:
  XAI_API_KEY=*** python scripts/probe.py
  XAI_API_KEY=*** python scripts/probe.py --model grok-4.5 --code FC2-PPV-4940028
"""
import argparse
import os
import sys
from openai import OpenAI


def main() -> None:
    ap = argparse.ArgumentParser(description="xAI/Grok 接入自检")
    ap.add_argument("--model", default="grok-4.5")
    ap.add_argument("--code", default="", help="给定番号则跑一次 web_search 探针")
    ap.add_argument("--base", default="https://api.x.ai/v1")
    args = ap.parse_args()

    key = os.environ.get("XAI_API_KEY")
    if not key:
        print("FAIL: 未设置 XAI_API_KEY 环境变量"); sys.exit(1)

    client = OpenAI(api_key=key, base_url=args.base)

    # 1) 列模型，确认 key 有效 + 目标模型存在
    try:
        models = client.models.list()
        ids = [m.id for m in models.data]
        print(f"可用模型数: {len(ids)}")
        print("grok* 模型:", [i for i in ids if i.startswith("grok")])
        print(f"目标模型 {args.model} 存在: {args.model in ids}")
    except Exception as e:  # noqa: BLE001
        print("列模型失败:", repr(e)); sys.exit(2)

    # 2) 可选：web_search 探针（验证联网搜索可用 + 解析路径）
    if args.code:
        try:
            resp = client.responses.create(
                model=args.model,
                input=[{"role": "user",
                        "content": f"用联网搜索查番号 {args.code} 的发行商，只回一句话。"}],
                tools=[{"type": "web_search"}],
            )
            text = getattr(resp, "output_text", "") or ""
            print("探针返回:", text[:300])
        except Exception as e:  # noqa: BLE001
            print("web_search 探针失败:", repr(e)); sys.exit(3)

    print("OK")


if __name__ == "__main__":
    main()
