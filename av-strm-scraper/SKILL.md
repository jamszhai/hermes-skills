---
name: av-strm-scraper
description: 遍历目录中的 .strm 文件（文件名即 AV 番号，如 FC2-PPV-4940028.strm / SIRO-5708.strm），刮削元数据并生成 Emby/Jellyfin 兼容的 .nfo 与 poster/fanart/thumb 图片。两种后端：(1) 默认无 key —— 用当前 Hermes 模型 + web_search + curl 直连刮削；(2) 可选 Grok/xAI API 后端。当用户提到 .strm 刮削、AV 元数据、番号整理、用 Grok 查番号时使用。
---

# AV .strm 刮削器

把"番号命名的 .strm 占位文件"批量刮削成媒体库可用的元数据 + 图片。

## 两种后端（任选）

1. **Hermes 后端（默认，无需 key）** —— 用本会话模型的 `web_search` 工具找元数据页，再用 `terminal` 里的 `curl` 直连解析。本机实测可用，是本技能的主路径。
2. **Grok 后端（可选）** —— 有 `XAI_API_KEY` 时，用 `scripts/scrape.py` 调 xAI Responses API（带 `web_search` 工具，模型 `grok-4.5`）。详见文末"Grok 后端"。

> 用户在 2026-07 实测确认：当前 Hermes 模型**能**直接刮削 AV 元数据（web_search 对这些站可达），不必依赖 Grok。优先走 Hermes 后端。

## ⚠ 关键陷阱（本机实测，务必遵守）
- **`browser_navigate` / `web_extract` 对 AV 镜像站不可用**：
  - `browser_navigate` 会超时（连开 3 个 AV 站全部 timeout，触发 loop 警告）。
  - `web_extract` 把 javbus 镜像 / av-wiki / javher 等判为"private or internal network address"直接 Blocked。
  - **因此解析元数据页一律用 `terminal` 里的 `curl` 直连**，不要用 browser/web_extract 抓 AV 站。
- `web_search` 工具（经 `execute_code` 的 `hermes_tools.web_search`）对 AV 站**可达**，用来拿候选 URL 列表。
- **MSYS 下 `curl -o /tmp/...` 写不进去**（`/tmp` 不存在）。一律写 `C:/Users/jams_/...` 绝对路径。
- 这些是 SPA 站，但 `curl` 直接 GET 返回的 HTML **含完整正文**（不是空壳），可直接正则解析。

## Hermes 后端 —— 标准流程（已实测跑通 28 个番号）
分两步，避免前台超时：

**步骤 1｜批量取候选 URL（execute_code，约 90s/28个）**
用 `execute_code` 调 `hermes_tools.web_search`，对每个番号搜 `"<番号> javbus av-wiki javher 标题 女優 メーカー"`，把 URL 列表存成 `<目录>/_urls.json`。
```python
from hermes_tools import web_search
import json
codes = ["200GANA-3412", "AUKG-655", ...]   # 从 .strm 文件名提取
out = {}
for c in codes:
    r = web_search(f"{c} javbus av-wiki javher 标题 女優 メーカー", limit=5)
    out[c] = [it.get("url","") for it in r.get("data",{}).get("web",[])]
json.dump(out, open(r"C:\Users\jams_\Downloads\mdcx\11\_urls.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
```
> 存文件名用 `_urls.json`，**不要**叫 `_candidates.json` 之类——后续步骤若 `rm *.json` 会误删。最稳是单独保留此文件不被清理脚本匹配。

**步骤 2｜curl 解析 + 落盘（terminal，后台跑）**
资料页抓取与 .nfo 生成交给 `scripts/scrape_curl.py`（读 `_urls.json`，curl 直连前 3 个候选页，正则解析，写 `<番号>.nfo` + `<番号>.json`）。
```bash
cd "C:/Users/jams_/Downloads/mdcx/11"
# 默认不下载图（只写 .nfo 含图片URL），快；>10个务必后台
python "<skill>/scripts/scrape_curl.py" --input "C:/Users/jams_/Downloads/mdcx/11" --urls-file "_urls.json"
# 需要本地图片时加 --download（会慢，建议后台）
python "<skill>/scripts/scrape_curl.py" --input "C:/Users/jams_/Downloads/mdcx/11" --urls-file "_urls.json" --download
```
> 数量 > ~10 且要下载图时，前台 300s 会超时 → 用 `terminal(background=true)` 跑，完成后回读 `_batch.log`。

## 输入约定
- `.strm` 文件名 = 纯番号，如 `FC2-PPV-4940028.strm`、`SIRO-5708.strm`、`HMN-864.strm`。
- 番号提取正则（已实测通用）：`(?:FC2[-_]PPV[-_]\d{3,}|[A-Z]{2,6}[-_]\d{2,6})`。

## 输出（每个番号，同目录）
- `<番号>.nfo`：Emby/Jellyfin 兼容 XML，含 `<title>`、`<uniqueid type="avcode">`、`<studio>`、`<set>`(系列)、`<plot>`、`<poster>`、`<thumb>`、`<fanart>`、`<actor><name>`。
- `<番号>.json`：原始解析结果（含 `error` 字段，便于排错）。
- 仅当 `--download`：`<番号>-poster.jpg` / `-thumb.jpg` / `-fanart.jpg`（DMM 直链）。

## 元数据解析启发式（references/av-metadata-sources.md 有细节）
- 标题：番号附近「」/【】内文本。
- 演员：日 wiki 模式 `出演AV女優の名前は…`、`女優名：`、`名前はXさん`、`AV女優名`。
- 片商：`メーカー：`。系列：`シリーズ：`。公开日：`公開日：YYYY/MM/DD`。
- 封面图：页内 `pics.dmm.co.jp` 的 img；缺失时回退 `https://pics.dmm.co.jp/digital/video/<番号去横杠小写>/pl.jpg`。

## Grok 后端（可选，有 XAI_API_KEY 时）
`scripts/scrape.py --input <dir> --model grok-4.5`。xAI 事实（已查 docs.x.ai）：
- OpenAI 兼容 `base_url="https://api.x.ai/v1"`，`Authorization: Bearer <XAI_API_KEY>`。
- 联网搜索用 **Responses API** `/v1/responses` + `tools=[{"type":"web_search"}]`；旧 Live Search API 已于 2026-01-12 弃用。
- 模型 `grok-4.5`/`grok-4`/`grok-3`。key 永不在脚本硬编码，读 `XAI_API_KEY` 环境变量。

## 注意
- 技术性刮削：仅检索公开元数据并落盘，不做内容筛选/改写。
- 番号去重；单条查不到记 `error` 不中断整体。
- `scrape_hermes.py` 是早期版本，其 `websearch()` 在纯 terminal 下会静默空跑（依赖 execute_code 注入的 hermes_tools）——**不要**在 terminal 直接跑它；用上面的两步流程或 `scrape_curl.py`。
- 改 web_search 用法/模型名前，先以真实 key 自测，确认没踩弃用 API。
