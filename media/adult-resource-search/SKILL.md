---
name: adult-resource-search
description: 找番号/系列的磁力、PikPak 分享链接或论坛资源时用。
---

# 成人资源交叉搜索工作流

本会话反复出现一类任务：按内容关键词（番号如 ANKK/FC2、系列名如 暗黒王子/怪兽企划、题材如 短剧/AI短剧/美妇沉沦）找可下载资源（磁力 / PikPak / 论坛）。
三路并行，互补：

## 1. Sukebei Nyaa 磁力（用 sukebei-magnet-scraper 技能）
- 按日期窗口抓：页数必须覆盖完整窗口（详见该技能的"按日期窗口抓取铁律"）。本会话实测 25 页=306 条、60 页=569 条（同周），页数不足会漏 MILK/JUR 等。
- `--since/--until` 支持到分钟：`--since "2026-07-24 10:30" --until "2026-07-25 09:00"`。
- `--search` 支持中文：`--search 索爱`、`--search 美妇沉沦`（脚本自动 URL 编码）。
- 抓**非浅绿行**（如指定博主全部条目）：用 terminal 跑独立 requests 脚本，仿 parse() 但去掉 success 判定。
- **网络预检**：抓取前先 `curl -s -o /dev/null -w "%{http_code}" https://sukebei.nyaa.si/`。返回 000/超时 = 代理节点掉线（用户用 OpenClash，节点会失效）——让用户重设节点后重试，**切勿把 0 条当真实结果**。

## 2. PikPak 分享链接（用 web_search）
- 直接搜：`web_search("怪兽企划 mypikpak.com/s/")` 或 `web_search("短剧合集 pikpak 网盘 下载链接")`。
- 命中格式：`https://mypikpak.com/s/<ID>`（合集）或带子目录 `/<ID>/<ID2>`。
- 标题里常含 `Shared by ***`，合集大小如 `40V 39G`。
- 失效链接会显示 "Files have been deleted"——搜索结果里可见，需人工筛。
- 专门聚合站：pikshare.bilivo.top（PikPak 分享链接聚合）。

## 3. 论坛/频道源
- 南+ south-plus.net：番号/合集活跃，常需登录或 SP 悬赏，公开 PikPak 链接少。
- xsijishe.net（司机社）：大合集多但常付费（车票/金币）。
- bbs.dyyjv.com：短剧/漫剧日更合集区，内附大量 PikPak 链接。
- Telegram：系列官方频道/预览群 + 机器人订阅发完整版（如索爱系列 suoai1024_bot）。

## 分类与差集（拿到全量磁力后）
- 番号正则要宽，覆盖 `字母-数字`、`C-数字`（Caribbean）、`日期-编号-CARIB`、`日期_编号-10MU` 等无码型；**排除同人/CG/成年漫画**（正则 `同人|CG集|成年コミック|\(C\d{2,3}\)|\[DL版\]|アンソロジー`）。
- 差集（"去掉之前给过的"）必须用**真实旧输出文件**的磁力链接做基准，勿用重放旧正则模拟。

## 坑（本会话实测）
1. **execute_code 会因用户确认超时被 BLOCKED**（本会话两次卡死）。本地分类/差集脚本改用 `terminal` + `python - <<'EOF' ... EOF` heredoc 跑——只需用户批准一次，不会静默卡死。
2. **curl 验证页面必须 `--compressed`**：否则拿到 gzip 原始字节，BeautifulSoup 读文件报 `utf-8 codec can't decode byte 0x8b`。
3. **OpenClash 节点失效是常态**：sukebei 抓取前必预检，000 即节点掉了，让用户重设。
4. **差集基准错 = 误删新条目**：曾因用"重放旧正则"模拟旧文件，错删 17 条 JUR。
5. **PikPak 搜索结果含失效链接**，输出时标注失效或提示用户自行验证。

## 输出
- 磁力：纯文本，每条"标题\nmagnet:...\n\n"，落桌面 `C:\Users\jams_\Desktop\`。
- PikPak/论坛链接：Markdown 表格，标注合集大小/是否失效/是否需登录。
- 文件名按内容+时间（如 `sukebei_0724-0725_番号.txt`、`sukebei_索爱.txt`）。
