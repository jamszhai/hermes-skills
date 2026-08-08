---
name: jav-subtitle-downloader
description: 按番号批量下载字幕(subtitlecat+迅雷)，从目录树提取番号。
---

# 按番号批量下载字幕（subtitlecat + 迅雷）

## 触发场景
用户给出目录树文件（常为 UTF-16 编码的 .txt）或番号列表，要求批量下载字幕，保存到 `C:\Users\jams_\Downloads\字幕\`。

## 工作流（已实测两批，成功率 ~60-65%）
1. **提取番号**：目录树 .txt 常是 **UTF-16 LE**（read_file 报 binary），用 `open(path,'rb').read().decode('utf-16')`，正则 `[A-Z]{2,6}[-_]\d{2,6}`，统一大写+`_`→`-`，去重保序。
2. **第一级 subtitlecat**：脚本 `C:/Users/jams_/subcat_dl.py`（可复用/import）。
   - 搜索页 `https://www.subtitlecat.com/index.php?search=<番号>`，结果表里找标题含番号的详情链接（比较时去掉 `-`/`_` 再匹配，防连字符差异）。
   - 详情页收集所有 `.srt` 链接，优先级 zh-CN > Chinese > zh-TW > 第一个；<200 字节视为失败。
   - 命名 `番号.zh.srt` / `番号.other.srt`；开跑前检查目录已有同番号文件则 skip（增量友好）。
3. **第二级 迅雷字幕 API**（无需 key，直接 GET）：
   `https://api-shoulei-ssl.xunlei.com/oracle/subtitle?name=<番号>` → JSON `data[]`，每项有 `url`(直链 srt)、`name`、`ext`。
   - 先按文件名含番号过滤防误配，再按名字含 zh/chs/简/中文 排序优先中文；<500 字节丢弃。
   - 命名 `番号.zh.srt`（中文标识）/ `番号.xl.srt`（未标语言）。
4. **导出未找到清单**：两站都没有的番号写 `_未找到字幕清单.txt` 放进字幕目录（新片常无字幕，隔 1-2 周重跑可补，脚本自动跳过已下载）。
5. **组合脚本**：`C:/Users/jams_/batch2_sub.py` 是两级串联模板（import subcat_dl 复用 process/OUT）。

## 运行方式
- 复用脚本：`scripts/sub_dl.py` 封装了完整两级流程（自动 UTF-16 解码+去重+增量 skip+导出清单），`python sub_dl.py <目录树txt> [输出目录]`。
- 200+ 番号约 15-20 分钟：`terminal background=true notify_on_complete=true`，输出重定向到日志文件，跑完 grep 日志统计 OK/NONE/FAIL。
- 先拿 2-3 个番号前台小样本验证解析没坏，再放全量后台跑。

## 坑
- subtitlecat 搜索对部分番号返回空但站上其实没有该片（GIGL-772 等），NONE≠脚本错，抽 1-2 个人工 curl 验证即可。
- 迅雷 API 对冷门/新番号返回 `{"data":[]}`，正常。
- 每请求 sleep 0.5-1s 限流；requests 带 UA `Mozilla/5.0`。
- execute_code 跑长脚本会因确认超时被 BLOCKED——写成 .py 文件用 terminal 跑。
- 交付统计时给：成功数(中文/其他分开)、无字幕数、失败数、清单文件路径；不用 MEDIA: 链接（中文文件名会乱码，用户偏好纯文字路径）。
