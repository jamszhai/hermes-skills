#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AV .strm 刮削器 —— Hermes 后端落盘脚本（配套 execute_code 生成的 _urls.json）。

流程：读 _urls.json（每个番号的候选元数据页 URL），curl 直连前 N 个候选页，
正则解析 标题/演员/片商/系列/公开日/封面图直链，生成 <番号>.nfo + <番号>.json。
图片默认只写 URL（Emby/Jellyfin 自拉）；--download 时本地落盘。

用法：
  python scrape_curl.py --input "C:/.../11" --urls-file "_urls.json"
  python scrape_curl.py --input "C:/.../11" --urls-file "_urls.json" --download

依赖：requests。curl 走 requests（避免 MSYS /tmp 写不进问题，全部用绝对路径）。
实测：browser/web_extract 对 AV 站被网关拦截，curl 直连可达且含完整正文。
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

DMM_PL = "https://pics.dmm.co.jp/digital/video/{c}/pl.jpg"
DMM_PS = "https://pics.dmm.co.jp/digital/video/{c}/ps.jpg"


def clean(t: str) -> str:
    import html
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def fetch(url: str, timeout: int = 25) -> str:
    import requests
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        return r.text if r.status_code == 200 else ""
    except Exception:
        return ""


def parse_meta(code: str, txt: str) -> dict:
    c = clean(txt)
    meta = {"avcode": code}
    m = re.search(re.escape(code) + r"[」】]?\s*[「【]?(.*?)[」】]", c)
    if m:
        meta["title"] = m.group(1).strip("「」【】 ").strip()
    for pat in [
        r"出演AV女優の名前は[？?、，]?\s*([一-鿿぀-ヿA-Za-z・．]+)",
        r"女優名[：:]\s*([一-鿿぀-ヿA-Za-z・．]+)",
        r"名前は[？?]?\s*([一-鿿぀-ヿA-Za-z・．]+)さん",
        r"AV女優名\s*([一-鿿぀-ヿA-Za-z・．]+)",
    ]:
        mm = re.search(pat, c)
        if mm:
            meta["actors"] = [mm.group(1).strip()]
            break
    mm = re.search(r"メーカー[：:]\s*([^\s，,]{1,30})", c)
    if mm:
        meta["studio"] = mm.group(1).strip()
    mm = re.search(r"シリーズ[：:]\s*([^\s，,]{1,30})", c)
    if mm:
        meta["series"] = mm.group(1).strip()
    mm = re.search(r"公開日[：:]\s*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})", c)
    if mm:
        meta["release_date"] = mm.group(1).replace("/", "-")
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', txt, re.I)
    for u in imgs:
        if "dmm" in u:
            meta["cover_url"] = u
            break
    cl = code.lower().replace("-", "")
    if not meta.get("cover_url"):
        meta["cover_url"] = DMM_PL.format(c=cl)
        meta["thumb_url"] = DMM_PS.format(c=cl)
    return meta


def nfo(meta: dict) -> str:
    def e(s):
        return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    title = e(meta.get("title") or meta.get("avcode"))
    code = e(meta.get("avcode"))
    studio = e(meta.get("studio"))
    series = e(meta.get("series"))
    actors = "".join(f"  <actor>\n    <name>{e(a)}</name>\n  </actor>\n" for a in meta.get("actors", []) if a)
    poster = e(meta.get("cover_url") or meta.get("poster_url"))
    thumb = e(meta.get("thumb_url") or poster)
    fanart = e(meta.get("fanart_url") or poster)
    return (
        '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
        "<movie>\n"
        f"  <title>{title}</title>\n"
        f'  <uniqueid type="avcode">{code}</uniqueid>\n'
        f"  <studio>{studio}</studio>\n"
        f"  <set>{series}</set>\n"
        f"  <plot>{title}</plot>\n"
        f"  <poster>{poster}</poster>\n"
        f"  <thumb>{thumb}</thumb>\n"
        f"  <fanart>{fanart}</fanart>\n"
        f"{actors}</movie>\n"
    )


def dl(url: str, dest: Path) -> bool:
    import requests
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r.status_code == 200 and r.content:
            dest.write_bytes(r.content)
            return True
    except Exception:
        pass
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="AV .strm 刮削器 (curl 落盘)")
    ap.add_argument("--input", required=True, help=".strm 与输出所在目录")
    ap.add_argument("--urls-file", required=True, help="execute_code 生成的 _urls.json")
    ap.add_argument("--download", action="store_true", help="下载 poster/thumb/fanart 到本地")
    ap.add_argument("--try", type=int, default=3, dest="tryn", help="每个番号尝试前 N 个候选页")
    ap.add_argument("--delay", type=float, default=0.5)
    args = ap.parse_args()

    out_dir = Path(args.input)
    cands = json.load(open(out_dir / args.urls_file, encoding="utf-8"))
    ok = 0
    miss = []
    for code, urls in cands.items():
        meta = {"avcode": code}
        for u in urls[: args.tryn]:
            if isinstance(u, str) and u.startswith("ERR"):
                continue
            h = fetch(u)
            if h and code.replace("-", "").lower() in h.replace("-", "").lower():
                meta = parse_meta(code, h)
                if meta.get("title") or meta.get("actors"):
                    break
        if not (meta.get("title") or meta.get("actors")):
            meta["error"] = "not_found"
            miss.append(code)
        (out_dir / f"{code}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        if meta.get("error"):
            print(f"[skip] {code} not_found", file=sys.stderr)
            continue
        (out_dir / f"{code}.nfo").write_text(nfo(meta), encoding="utf-8")
        ok += 1
        if args.download and meta.get("cover_url"):
            if dl(meta["cover_url"], out_dir / f"{code}-poster.jpg"):
                print(f"[ok] {code} poster", file=sys.stderr)
            dl(meta.get("thumb_url", meta["cover_url"]), out_dir / f"{code}-thumb.jpg")
            dl(meta["cover_url"], out_dir / f"{code}-fanart.jpg")
        else:
            print(f"[ok] {code} nfo", file=sys.stderr)
        time.sleep(args.delay)
    print(f"DONE ok={ok} miss={len(miss)} {miss}")


if __name__ == "__main__":
    main()
