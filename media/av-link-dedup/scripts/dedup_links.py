#!/usr/bin/env python3
# dedup_links.py — 把 ed2k/magnet 链接列表与「本地目录树 / 已有库」按番号比对去重，
# 并支持「同番号优先保留 4K 版」。
# 用法见 av-link-dedup SKILL.md「用法」一节。
import re
import argparse
import urllib.parse


def read_text(path):
    # 目录树多为 UTF-16 LE；链接列表多为 UTF-8。先试 utf-8，失败再 utf-16。
    for enc in ("utf-8", "utf-16"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def link_name(line):
    # ed2k: ed2k://|file|...@NAME.mp4|HASH|/
    m = re.search(r"@([^|]+?)\.(mp4|mkv|avi|m4v)", line, re.I)
    if m:
        return m.group(1)
    # magnet: dn= 参数
    m = re.search(r"dn=([^&]+)", line, re.I)
    if m:
        return urllib.parse.unquote(m.group(1))
    return line.strip()


def tree_name(line):
    # | | |-sdnm-442  /  -suwk-012_4Ks.mp4
    return line.strip().strip("|").strip().lstrip("-").strip()


def parse_file(path):
    """返回 (entries, is_link_file)。entries: list of (raw_line, display_name)。"""
    text = read_text(path)
    lines = [l for l in text.splitlines() if l.strip()]
    link_like = sum(1 for l in lines if l.strip().startswith(("ed2k://", "magnet:")))
    if link_like >= max(1, len(lines) // 2):
        return [(l, link_name(l)) for l in lines
                if l.strip().startswith(("ed2k://", "magnet:"))], True
    out = []
    for l in lines:
        n = tree_name(l)
        if n and "古東まりこ" not in n and not n.startswith("——") and n not in ("|", "-"):
            out.append((l, n))
    return out, False


def normalize(name):
    s = name.strip().lower()
    s = re.sub(r"\.[a-z0-9]+$", "", s)        # 扩展名
    s = s.lstrip("-")
    changed = True
    while changed:                              # 循环剥离末尾画质/分卷后缀
        changed = False
        for pat in [r"[-_]?(?:4|8)ks?$", r"_\d+$", r"part\d+$"]:
            ns = re.sub(pat, "", s, flags=re.I)
            if ns != s:
                s = ns
                changed = True
    m = re.match(r"^([a-z0-9]+(?:[-_][a-z0-9]+)*[-_]\d+)", s)
    return m.group(1) if m else s


def quality(name):
    s = name.lower()
    if "8k" in s:
        return 8
    if "4k" in s:
        return 4
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--links", required=True, help="待处理链接文件")
    ap.add_argument("--existing", help="目录树txt 或 另一个链接文件（已有库）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefer-4k", action="store_true", help="同番号只留 4K 版")
    args = ap.parse_args()

    links, _ = parse_file(args.links)

    if args.existing:
        existing, _ = parse_file(args.existing)
        ex_ids = {normalize(n) for _, n in existing}
        kept = [(ln, n) for ln, n in links if normalize(n) not in ex_ids]
    else:
        kept = list(links)

    if args.prefer_4k:
        groups = {}
        for ln, n in kept:
            groups.setdefault(normalize(n), []).append((ln, n))
        new = []
        for items in groups.values():
            if len(items) == 1:
                new.extend(items)
                continue
            k4 = [x for x in items if quality(x[1]) == 4]
            new.extend(k4 if k4 else items)        # 无4K则整组(含8K分卷)保留
        order = {ln: i for i, (ln, n) in enumerate(kept)}
        new.sort(key=lambda x: order[x[0]])
        kept = new

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(ln for ln, n in kept) + "\n")
    print(f"输入 {len(links)} 条 -> 输出 {len(kept)} 条 -> {args.out}")


if __name__ == "__main__":
    main()
