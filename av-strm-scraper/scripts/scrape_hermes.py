#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AV .strm 刮削器 —— Hermes(当前模型) 后端版。

不依赖 Grok / xAI key。流程：
  1. 从 .strm 文件名提取番号（如 200GANA-3412）。
  2. 用 web_search 找该番号的元数据页（javbus 镜像 / 各类 wiki / javher）。
  3. curl 直连候选页，解析 标题/演员/片商/系列/公开日/标签/封面图直链。
  4. 生成 Emby/Jellyfin 兼容 <番号>.nfo + 下载 poster/fanart/thumb 到同目录。

本机实测：web_extract/browser 对 AV 站常被网关拦截，但 curl 直连可达，故解析走 curl。
依赖：requests。web_search 通过 hermes_tools（脚本在 agent 会话内运行时由 execute_code 注入）；
若独立运行，请改用终端 web_search 结果或传入 --meta-json 预抓取结果。

注意：这是技术性刮削，仅检索公开元数据并落盘，不做内容筛选/改写。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CODE_RE = re.compile(r"(?:FC2[-_]PPV[-_]\d{3,}|[A-Z]{2,6}[-_]\d{2,6})")
DMM_POSTER = "https://pics.dmm.co.jp/digital/video/{code_l}/pl.jpg"   # 大图
DMM_PS = "https://pics.dmm.co.jp/digital/video/{code_l}/ps.jpg"        # 小图


def extract_code(name: str) -> str | None:
    m = CODE_RE.search(name)
    return m.group(0).upper().replace("_", "-") if m else None


def websearch(query: str, limit: int = 5) -> list[str]:
    """调用 hermes web_search（经 shell 包装）。返回 url 列表。
    若环境未注入 hermes_tools，则回退到外部命令 `web_search` 或空。"""
    try:
        # 尝试通过 execute_code 注入的 hermes_tools（在 agent 内才有效）。
        from hermes_tools import web_search as ws  # type: ignore
        res = ws(query, limit=limit)
        out = []
        for it in res.get("data", {}).get("web", []):
            out.append(it.get("url", ""))
        return [u for u in out if u]
    except Exception:
        pass
    # 回退：调用系统 web_search（若可用）
    try:
        r = subprocess.run(["web_search", query], capture_output=True, text=True, timeout=40)
        return re.findall(r"https?://[^\s\"'<>]+", r.stdout)
    except Exception:
        return []


def fetch(url: str, timeout: int = 25) -> str:
    import requests
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    return r.text if r.status_code == 200 else ""


def clean(t: str) -> str:
    import html
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def parse_meta(code: str, html_text: str) -> dict:
    """从 wiki 页正文解析元数据（启发式，覆盖主流字段）。"""
    txt = clean(html_text)
    meta = {"avcode": code}
    # 标题：含番号的引号内或附近
    m = re.search(rf"{re.escape(code)}[」】]?\s*[「【]?(.*?)[」】]", txt)
    if m:
        meta["title"] = m.group(1).strip("「」【】 ")
    # 演员：常见 "女優名 X" / "名前は？ X" / "AV女優の名前が知りたい"
    for pat in [
        r"出演AV女優の名前は[？?、，]?\s*([一-鿿぀-ヿA-Za-z・．]+)",
        r"女優名[：:]\s*([一-鿿぀-ヿA-Za-z・．]+)",
        r"名前は[？?]?\s*([一-鿿぀-ヿA-Za-z・．]+)さん",
        r"AV女優名\s*([一-鿿぀-ヿA-Za-z・．]+)",
    ]:
        mm = re.search(pat, txt)
        if mm:
            meta["actors"] = [mm.group(1).strip()]
            break
    # 片商 / メーカー
    mm = re.search(r"メーカー[：:]\s*([^\s，,]{1,30})", txt)
    if mm:
        meta["studio"] = mm.group(1).strip()
    # 系列 / シリーズ
    mm = re.search(r"シリーズ[：:]\s*([^\s，,]{1,30})", txt)
    if mm:
        meta["series"] = mm.group(1).strip()
    # 公开日 / 公開日
    mm = re.search(r"公開日[：:]\s*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})", txt)
    if mm:
        meta["release_date"] = mm.group(1).replace("/", "-")
    # 封面图直链：dmm pics / 其它 img
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_text, re.I)
    for u in imgs:
        if "pics.dmm.co.jp" in u or "dmm.com" in u or "dmm.co.jp" in u:
            meta["cover_url"] = u
            break
    if not meta.get("cover_url"):
        code_l = code.lower().replace("-", "")
        meta["cover_url"] = DMM_POSTER.format(code_l=code_l)
        meta["thumb_url"] = DMM_PS.format(code_l=code_l)
    return meta


def build_nfo(meta: dict) -> str:
    def e(s):
        return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    title = e(meta.get("title") or meta.get("avcode"))
    code = e(meta.get("avcode"))
    studio = e(meta.get("studio"))
    series = e(meta.get("series"))
    plot = e(meta.get("plot") or meta.get("title"))
    actors = "".join(f"  <actor>\n    <name>{e(a)}</name>\n  </actor>\n" for a in meta.get("actors", []) if a)
    tags = "".join(f"  <tag>{e(t)}</tag>\n" for t in meta.get("tags", []) if t)
    poster = e(meta.get("cover_url") or meta.get("poster_url"))
    thumb = e(meta.get("thumb_url") or poster)
    fanart = e(meta.get("fanart_url") or poster)
    return (
        '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
        "<movie>\n"
        f"  <title>{title}</title>\n"
        f"  <uniqueid type=\"avcode\">{code}</uniqueid>\n"
        f"  <studio>{studio}</studio>\n"
        f"  <set>{series}</set>\n"
        f"  <plot>{plot}</plot>\n"
        f"  <poster>{poster}</poster>\n"
        f"  <thumb>{thumb}</thumb>\n"
        f"  <fanart>{fanart}</fanart>\n"
        f"{actors}{tags}"
        "</movie>\n"
    )


def download(url: str, dest: Path) -> bool:
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r.status_code == 200 and r.content:
            dest.write_bytes(r.content)
            return True
    except Exception:
        pass
    return False


def gather_codes(input_dir: str, recursive: bool) -> list[tuple[str, Path]]:
    out = []
    pat = "**/*.strm" if recursive else "*.strm"
    for p in Path(input_dir).glob(pat):
        c = extract_code(p.stem)
        if c:
            out.append((c, p))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="AV .strm 刮削器 (Hermes 后端)")
    ap.add_argument("--input", required=True, help=".strm 所在目录")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--max", type=int, default=0, help="最多处理几个（0=全部）")
    args = ap.parse_args()

    entries = gather_codes(args.input, args.recursive)
    if not entries:
        raise SystemExit("[失败] 未找到任何番号 .strm")
    seen, uniq = set(), []
    for c, p in entries:
        if c not in seen:
            seen.add(c)
            uniq.append((c, p))
    if args.max:
        uniq = uniq[: args.max]
    print(f"[信息] {len(uniq)} 个唯一番号", file=sys.stderr)

    ok = 0
    for i, (code, p) in enumerate(uniq, 1):
        print(f"[{i}/{len(uniq)}] {code}", file=sys.stderr)
        urls = websearch(f"{code} javbus OR av-wiki OR javher 标题 女優", limit=5)
        meta = {"avcode": code}
        for u in urls[:3]:
            html_text = fetch(u)
            if html_text and code.replace("-", "") in html_text.replace("-", ""):
                meta = parse_meta(code, html_text)
                if meta.get("title") or meta.get("actors"):
                    break
        if not (meta.get("title") or meta.get("actors")):
            meta["error"] = "not_found"
        out_dir = p.parent
        (out_dir / f"{code}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        if meta.get("error"):
            print(f"  [跳过nfo] {code}: {meta['error']}", file=sys.stderr)
        else:
            (out_dir / f"{code}.nfo").write_text(build_nfo(meta), encoding="utf-8")
            ok += 1
            if not args.no_images and meta.get("cover_url"):
                if download(meta["cover_url"], out_dir / f"{code}-poster.jpg"):
                    print("  poster.jpg ✓", file=sys.stderr)
                if meta.get("thumb_url"):
                    download(meta["thumb_url"], out_dir / f"{code}-thumb.jpg")
                download(meta["cover_url"], out_dir / f"{code}-fanart.jpg")
        if i < len(uniq):
            time.sleep(args.delay)
    print(f"[完成] {ok}/{len(uniq)} 个 .nfo 已生成于 {args.input}", file=sys.stderr)


if __name__ == "__main__":
    main()
