# Hermes 后端刮削经验（2026-07-18 会话）

## 核心发现
- **curl 直连 AV 站（av-wiki、javher、shiroutowiki 等）不可靠**：大量 403/超时/空响应，导致 13/28 个番号失败。
- **web_search 工具更稳**：能拿到片段（标题、女優、片商、发行日期），比 curl 可靠。
- **DMM 封面图直链模式**（已验证可用）：
  - Poster（大图）：`https://pics.dmm.co.jp/digital/video/{code小写无连字符}/pl.jpg`
  - Thumb（小图）：`https://pics.dmm.co.jp/digital/video/{code小写无连字符}/ps.jpg`
  - 例：`DDK-240` → `ddk00240/pl.jpg`

## 推荐流程（Hermes 后端）
1. 用 web_search 找 `番号 javbus OR av-wiki OR javher 标题 女優 メーカー`。
2. 取前 3 个结果，优先 av-wiki 具体作品页。
3. 解析标题、女優、片商、系列、日期。
4. 始终写入 DMM 封面图直链（即使解析失败也能保证图片可用）。
5. 生成 `.nfo`（Emby/Jellyfin 兼容）+ `.json` 原始数据。

## 已知坑
- 许多 AV 镜像站对服务器 IP 封锁，curl 批量容易失败。
- SPA 站 curl 拿到的 HTML 常含 JS 动态内容，解析需宽松正则。
- 番号去重必须在生成前做（文件名可能重复）。

## 后续改进方向
- 当 web_search 返回结果不足时，fallback 到 DMM 官方搜索页（需处理反爬）。
- 可选 `--download-images` 模式（当前默认只写 URL，由播放器拉取）。
