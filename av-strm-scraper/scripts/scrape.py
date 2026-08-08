#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AV .strm 刮削器（Grok / xAI 驱动）。

扫描目录中的 .strm 文件（文件名即番号），调用 xAI Responses API（带 web_search
联网工具）检索该番号的 AV 元数据，生成 Emby/Jellyfin 兼容的 .nfo、图片与原始 JSON。

依赖：openai, requests。key 读环境变量 XAI_API_KEY（不硬编码）。
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from openai import OpenAI

# 番号正则：FC2-PPV-数字 或 2~6字母-数字（已实测覆盖主流厂牌）
CODE_RE = re.compile(r"(?:FC2[-_]PPV[-_]\d{3,}|[A-Z]{2,6}[-_]\d{2,6})")

XAI_BASE = "https://api.x.ai/v1"
PROMPT = (
    "你是一个 AV 元数据刮削助手。给定番号，请使用联网搜索(web_search)查询其公开元数据，"
    "优先查 javbus / javlibrary / dmm / r18 等。只返回 JSON，不要任何解释文字。\n"
    "JSON 字段：\n"
    "  title: 作品标题（原文，含番号）\n"
    "  avcode: 番号（大写，连字符分隔，如 FC2-PPV-4940028）\n"
    "  studio: 发行商/片商\n"
    "  actors: [演员名列表]\n"
    "  tags: [标签/类别列表]\n"
    "  release_date: 发行日期 YYYY-MM-DD 或空\n"
    "  cover_url: 封面图直链（poster）或空\n"
    "  fanart_url: 背景大图直链或空\n"
    "  thumb_url: 缩略图直链或空\n"
    "  plot: 一句话简介或空\n"
    "若查不到，返回 {\"avcode\":\"<番号>\",\"error\":\"not_found\"}。\n"
    "番号：{code}"
)


def extract_code(filename: str) -> str | None:
    m = CODE_RE.search(filename)
    return m.group(0).upper().replace("_", "-") if m else None


def call_grok(client, code: str, model: str) -> dict:
    """调用 Responses API + web_search，返回解析后的 dict。"""
    resp = client.responses.create(
        model=model,
        input=[{"role": "user", "content": PROMPT.format(code=code)}],
        tools=[{"type": "web_search"}],
    )
    text = getattr(resp, "output_text", None) or ""
    # 兼容不同返回结构
    if not text and hasattr(resp, "output"):
        for o in resp.output:
            if getattr(o, "type", "") == "message":
                for c in getattr(o, "content", []):
                    if getattr(c, "type", "") == "output_text":
                        text = c.text
                        break
    text = text.strip()
    # 去掉可能的 ```json 围栏
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 退而求其次：在文本里找第一个 { 到最后一个 }
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            return json.loads(text[s : e + 1])
        return {"avcode": code, "error": "parse_failed", "raw": text[:500]}


def build_nfo(meta: dict) -> str:
    """生成 Emby/Jellyfin 兼容 movie .nfo（XML）。"""
    title = (meta.get("title") or meta.get("avcode") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    code = (meta.get("avcode") or "").replace("&", "&amp;")
    studio = (meta.get("studio") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    plot = (meta.get("plot") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    actors = "".join(
        f"  <actor>\n    <name>{a.replace('&','&amp;')}</name>\n  </actor>\n"
        for a in meta.get("actors", []) if a
    )
    tags = "".join(
        f"  <tag>{t.replace('&','&amp;')}</tag>\n" for t in meta.get("tags", []) if t
    )
    poster = (meta.get("cover_url") or meta.get("poster_url") or "").replace("&", "&amp;")
    thumb = (meta.get("thumb_url") or poster).replace("&", "&amp;")
    fanart = (meta.get("fanart_url") or "").replace("&", "&amp;")
    return (
        '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
        "<movie>\n"
        f"  <title>{title}</title>\n"
        f"  <uniqueid type=\"avcode\">{code}</uniqueid>\n"
        f"  <studio>{studio}</studio>\n"
        f"  <plot>{plot}</plot>\n"
        f"  <poster>{poster}</poster>\n"
        f"  <thumb>{thumb}</thumb>\n"
        f"  <fanart>{fanart}</fanart>\n"
        f"{actors}{tags}"
        "</movie>\n"
    )


def download(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r.status_code == 200 and r.content:
            dest.write_bytes(r.content)
            return True
    except Exception:
        pass
    return False


def gather_codes(args) -> list[tuple[str, Path | None]]:
    """返回 [(番号, 对应.strm文件路径|None)]。"""
    if args.codes:
        return [(c.strip().upper().replace("_", "-"), None) for c in args.codes.split(",") if c.strip()]
    out = []
    pattern = "**/*.strm" if args.recursive else "*.strm"
    for p in Path(args.input).glob(pattern):
        code = extract_code(p.stem)
        if code:
            out.append((code, p))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="AV .strm 刮削器 (Grok/xAI)")
    ap.add_argument("--input", default=".", help=".strm 所在目录")
    ap.add_argument("--recursive", action="store_true", help="递归子目录")
    ap.add_argument("--codes", default="", help="直接给番号列表，逗号分隔（跳过文件扫描）")
    ap.add_argument("--model", default="grok-4.5", help="xAI 模型名（默认 grok-4.5）")
    ap.add_argument("--no-images", action="store_true", help="不下载 poster/fanart/thumb")
    ap.add_argument("--dry-run", action="store_true", help="只演示番号提取与输出骨架，不调 API")
    ap.add_argument("--delay", type=float, default=1.2, help="每番号间隔秒数（限速）")
    args = ap.parse_args()

    entries = gather_codes(args)
    if not entries:
        raise SystemExit("[失败] 未找到任何番号（检查 --input 或 --codes）")
    # 去重
    seen, uniq = set(), []
    for code, p in entries:
        if code not in seen:
            seen.add(code)
            uniq.append((code, p))
    print(f"[信息] 共 {len(uniq)} 个唯一番号待处理", file=sys.stderr)

    if args.dry_run:
        for code, p in uniq:
            print(f"[dry-run] {code}  <- {p}")
        print(f"[dry-run] 将生成 {len(uniq)} 个 .nfo / .json（未调 API）", file=sys.stderr)
        return

    key = os.environ.get("XAI_API_KEY")
    if not key:
        raise SystemExit("[失败] 未设置 XAI_API_KEY 环境变量。请先 export XAI_API_KEY=***")
    client = OpenAI(api_key=key, base_url=XAI_BASE)

    ok = 0
    for i, (code, p) in enumerate(uniq, 1):
        print(f"[{i}/{len(uniq)}] 刮削 {code} ...", file=sys.stderr)
        try:
            meta = call_grok(client, code, args.model)
        except Exception as e:  # noqa: BLE001
            print(f"  [错误] {code}: {e!r}", file=sys.stderr)
            meta = {"avcode": code, "error": str(e)}
        # 输出目录：有 .strm 则同目录，否则当前目录
        out_dir = p.parent if p else Path(".")
        base = out_dir / code
        (base.with_suffix(".json")).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        if meta.get("error"):
            print(f"  [跳过nfo] {code}: {meta['error']}", file=sys.stderr)
        else:
            (base.with_suffix(".nfo")).write_text(build_nfo(meta), encoding="utf-8")
            ok += 1
            if not args.no_images:
                for kind, field in (("poster", "cover_url"), ("fanart", "fanart_url"), ("thumb", "thumb_url")):
                    url = meta.get(field) or meta.get(f"{kind}_url")
                    if url:
                        if download(url, out_dir / f"{code}-{kind}.jpg"):
                            print(f"  已下 {kind}.jpg", file=sys.stderr)
        if i < len(uniq):
            time.sleep(args.delay)

    print(f"[完成] 成功 {ok}/{len(uniq)} 个 .nfo 已生成", file=sys.stderr)


if __name__ == "__main__":
    main()
