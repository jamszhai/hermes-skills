---
name: chrome-bookmarks
description: "Clean, deduplicate, and categorize Chrome bookmarks. Detects exact-URL duplicates, removes unwanted/adult/spam entries, and reshapes bookmark_bar into domain-based folder categories."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [chrome, bookmarks, cleanup, dedup, categorization]
    related_skills: [administrative-form-filling, ocr-and-documents]
---

# Chrome Bookmarks Cleanup and Categorization

Use when the user asks to clean up Chrome bookmarks, remove duplicates, categorize bookmarks, or organize the bookmark bar.

## Prerequisites

- Chrome must be closed, or at minimum, the `Bookmarks` file will be overwritten and Chrome must be restarted to see changes.
- The file path on Windows is typically:
  `C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Default\Bookmarks`

## Step 1: Read and inspect the Bookmarks JSON

Chrome stores bookmarks as a JSON file, not a simple HTML export.

```python
import json
from urllib.parse import urlparse

path = r'C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Default\Bookmarks'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

bar_children = data['roots']['bookmark_bar']['children']
urls = [n for n in bar_children if n['type'] == 'url']
print(f"Total bookmarks: {len(urls)}")
```

Also inspect `other`, `synced`, and `mobile` roots if the user mentions sync or other folders.

## Step 2: Stage the cleanup plan for user review (optional)

For large bookmark sets (>100), summarize:

- Total counts
- Exact-URL duplicate groups or near-duplicate counts
- Unwanted domains to remove (spam redirectors, adult sites, expired affiliate redirectors)
- Proposed category folders and counts

Ask user to confirm destructive operations, especially when removing entries.

## Step 3: Deduplicate

```python
from collections import defaultdict

url_count = defaultdict(list)
for i, bm in enumerate(urls):
    url_count[bm['url']].append(i)

for url, idxs in url_count.items():
    if len(idxs) > 1:
        # Keep first, remove others
        for idx in idxs[1:]:
            urls[idx]['_remove'] = True
```

After removal, reassign IDs sequentially from 1 to avoid Chrome checksum validation issues.

## Step 4: Remove unwanted entries

Common categories to exclude:

- **Affiliate redirector clusters**: `replace.favo.xpu93.com`, `new.favo.xpu93.com`, `77887777.com`, `66776688.com`
- **Adult content**: xnxx, pornhub, xvideos, t66y, sukebei, sis001, etc.
- **Expired/temp domains** and obvious spam links

Use a configurable keep/remove list rather than hardcoding every domain.

## Step 5: Categorize by domain

Build a domain-to-folder map. Common Windows/Chinese-user bookmark categories:

| Folder | Typical domains |
|---|---|
| 开发工具 | github.com, gitlab.com, github.io repos |
| 网络工具 | dnshe, cloudns, dynadot, 各种节点/分流工具 |
| 路由器 | right.com.cn, koolshare.cn, openclash |
| 智能家居 | hassbian.com, home assistant related |
| 安全研究 | zoomeye.org, vulnerability databases |
| 网络导航 | 2345, hao123, xiaoxiangbz, beidema |
| AI工具/办公 | notebooklm, biji, feishu, openrouter, dashscope |
| 影音资源 | nfmovies, dy2018, mp4ba, 字幕站s |
| 文档工具 | ilovepdf, caj2pdf, bigjpg |

```python
from collections import defaultdict

folder_children = defaultdict(list)
for bookmark in clean:
    host = urlparse(bookmark['url']).netloc.lower()
    folder = domain_map.get(host)
    folder_children[folder or '其他'].append({...})

# Build new bookmark_bar
new_bar = []
for name in preferred_order:
    items = folder_children.get(name, [])
    if items:
        new_bar.append({'type': 'folder', 'name': name, 'children': items})
```

## Step 6: Write back

Rewrite `data['roots']['bookmark_bar']` with `new_bar` and serialize. Preserve `checksum` if present; Chrome will recompute.

```python
data['roots']['bookmark_bar'] = {'children': new_bar}
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=3)
```

## Step 7: Verify and instruct user

After writing:

1. Re-open the file and confirm folder structure matches expectation.
2. Tell the user: **Chrome must be restarted to see changes.**

## Pitfalls

- **Chrome must be closed before writing**: If Chrome is running, it may hold the file handle or revert changes on restart. On Windows, explicitly close all Chrome windows first.
- **Checksum field**: Chrome stores `checksum` at the top level. Some versions validate this and repopulate it on startup, but others may show a blank bookmark bar if the checksum is missing. If that happens, delete the file and let Chrome rebuild from sync or from a backup.
- **Backup before rewrite**: Always copy the original `Bookmarks` file to `Bookmarks.backup` before writing.
- **ID collisions**: After removing duplicates, reassign sequential IDs (from 1) to avoid Chrome treating missing IDs as deleted bookmarks.
- **Folder depth**: Chrome supports nested folders, but many users prefer flat categories. Keep depth to 1 for maintainability.
- **Affiliate URL ambiguity**: Some bookmarks show different names but share one redirector domain. Removing them blindly can delete legitimate items; inspect names before bulk-removing redirector domains.
