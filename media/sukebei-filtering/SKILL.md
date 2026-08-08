---
name: sukebei-filtering
description: "Sukebei 磁力后处理：去同人、去指定片商、同番号优选最高画质。触发：sukebei 后处理。"
---

# Sukebei 磁力后处理与去重

## 何时用
原始 `sukebei-magnet-scraper` 已成功抓取**全量**浅绿色链接后，进入本技能阶段。
本技能只做本地文本过滤，**不再发起网络请求**。

## 前置条件
1. 必须先有全量结果（不加 `--search` 限词，只用 `--since/--until + --pages 60+`）。
2. 原始输出为 `标题 + magnet:` 链接交替的 UTF-8 纯文本。

## 核心规则（踩坑经验，必读）

### 1. 全量抓取是后处理的前提
用户说"只要 X / 除 Y 外的全部"时，**绝对不能**在 `scrape.py` 里用 `--search` 预过滤服务端——这会把未命中的全系列（如 DVMM/WAAA/MIDE）直接漏掉。
正确做法：先抓全量，再本地筛。

### 2. 两阶段过滤顺序
1. **第一刀：同人/无番号排除**（标题含同人誌、CG集、DLsite、AI生成、Fate/SAO 等同人关键词 → 整块删除；标题无标准番号格式的素人站也整块删除）。
2. **第二刀：片商筛选**（保留/排除指定片商，按番号 `[A-Z]{2,10}[-_]\d{2,6}` 正则匹配）。

### 3. 同番号优选最高画质
当同一番号有多个版本（常规 / 4K / 8K / 分卷 PART.n）时：
- 同一番号内优先保留最高画质（8K > 4K > 常规）。
- 同一画质内的多个 PART（分卷）**全部保留**，不可只留一个。

### 4. 目录树交叉去重
如果用户有目录树文件（通常 UTF-16 LE 编码），需：
- 解码目录树条目
- 统一番号归一化（去前缀杂质、去连字符/补零、去画质后缀、去分卷后缀）
- 文件1 中番号命中目录树 → 整条删除

## 标准化番号归一化函数

```python
import re

def pre(s):
    s = s.lower()
    s = re.sub(r"\.(mp4|mkv)$", "", s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"part\.?\d+", "", s)
    s = re.sub(r"60fps", "", s)
    s = re.sub(r"hhb\d*", "", s)
    s = re.sub(r"\d*ks?", "", s)
    return s

def base_id(name):
    s = pre(name)
    s = re.sub(r"hhd800\.com@", "", s)
    s = re.sub(r"^0+", "", s)
    s = re.sub(r"^\d+(?=[a-z]{2,})", "", s)
    s = re.sub(r"^(h_?\d+)", "", s)
    m = re.search(r"([a-z]+)-?0*(\d+)", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m2 = re.search(r"([a-z0-9]*[a-z])-?0*(\d+)", s)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}"
    return re.sub(r"[^a-z0-9]", "", s)
```

## 常用过滤模板

```python
import re, urllib.parse

def get_title(block):
    for line in block.splitlines():
        if line.strip().lower().startswith("magnet:"):
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(line).query)
            return urllib.parse.unquote(q.get("dn", [""])[0])
    return block.splitlines()[0].strip()

EXCLUDE = re.compile(
    r"同人|同人誌|CG集|AI生成|イラスト|COMIC1\b|DLsite|"
    r"Fate.*stay|To LOVEる|フェイト|Sword Art Online|SAO|"
    r"ハイスクール|ゲーム|GAME|R18| \d{4}年\d{1,2}月|C\d{3}|DL版|オリジナル",
    re.I
)
HAS_ID = re.compile(r"(?:^|[\s\-])([A-Z]{2,10}[-_]\d{2,6})(?:[\s\.\,\!\-\:]|\$)", re.I)

blocks = open("源文件.txt", encoding="utf-8").read().split("\n\n")
out = [b for b in blocks
       if not EXCLUDE.search(get_title(b))
       and HAS_ID.search(get_title(b))]
```

## 输出约定
- 过滤后文件用 `_非FC2非同人.txt` / `_FC2.txt` / `_优选4K.txt` 等后缀
- 落盘路径：`C:\Users\jams_\Downloads\`
- 不用 MEDIA: 链接交付中文名文件（避免 URL 编码乱码），直接给完整路径
