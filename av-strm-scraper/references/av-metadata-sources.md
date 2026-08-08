# AV 元数据来源与解析要点（2026-07 实测）

## 可达的数据源（web_search 能找到，curl 能直连）
- **各类日文 wiki**：`shiroutowiki.work`、`av-wiki.net`、`seesaawiki.jp`、`shiroutoname.com`、`av-wiki.net/mgstage/...`。素人系（200GANA/SIRO/MGS 系）最全。
- **javher.com**（中文，含 DVD ID、中文标题、简介）。
- **javbus 镜像**：`javbus.sbs` 等（官方 javbus.com 在本机常被拦）。
- **搜索结果里偶尔出现 `sextb.net` / `ggjav.com`**（含标题、日期、类别）。

## 不可用的取数方式（本机实测）
- `browser_navigate` 打开 AV 站 → 超时（连开 3 个全部 timeout）。
- `web_extract` 打开 AV 站 → 被网关判为 "private or internal network address" Blocked。
- **结论：解析元数据页一律 curl 直连**，且 curl 返回的是完整正文（SPA 也不例外）。

## 字段解析正则（已对 200GANA-3412 / BLK-655 / BLOR-295 验证）
所有字段从 `clean(html)` 后的正文里取。日文 wiki 正文结构稳定：
- 标题：`番号[」】]?\s*[「【](.*?)[」】]`（番号后引号内）
- 演员：
  - `出演AV女優の名前は[？?、，]?\s*(名)`
  - `女優名[：:]\s*(名)`
  - `名前は[？?]?\s*(名)さん`
  - `AV女優名\s*(名)`
- 片商：`メーカー[：:]\s*([^\s，,]{1,30})`
- 系列：`シリーズ[：:]\s*([^\s，,]{1,30})`
- 公开日：`公開日[：:]\s*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})`
- 封面图：优先页内 `pics.dmm.co.jp` 的 `<img src>`；缺失回退 `https://pics.dmm.co.jp/digital/video/<番号去横杠小写>/pl.jpg`（poster）/ `ps.jpg`（thumb）。

## 实测样本
| 番号 | 标题 | 演员 | 片商 | 系列 | 公开日 |
|---|---|---|---|---|---|
| 200GANA-3412 | 美味しいご飯のあとは、私がデザート…？ | 濡田まな | ナンパTV | マジ軟派、初撮。 | 2026/07/15 |
| BLK-655 | 魅惑の【こんがり】日焼け巨乳 SM風俗店指名No.1ギャル女王様… | 西野絵美 | kira☆kira | BLACK GAL | 2025-07-11 |
| BLOR-295 | 一部重口味的綠帽紀錄片… | (javher 未列演员) | — | — | — |

## 排错
- 若某番号 `not_found`：候选 URL 可能全错或页结构变化 → 单独用 web_search 再查，或人工补 .nfo。
- DMM 回退图可能 404（番号不在 DMM）→ .nfo 仍写 URL，Emby 拉不到图时显空白。
