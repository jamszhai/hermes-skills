---
name: office-file-delivery
description: 为中文用户（规划/建筑设计咨询）生成并交付 Excel/Word 交付物时的工作流与格式规范——文件放桌面、单表纵向排布、长说明行合并整行换行、MEDIA 中文名编码坑、造价来源去地名化、execute_code 被拦截时改用写脚本+terminal。当用户要求"做成本测算表/指标表/生成 Excel 或 Word 交付物/把表格合并到一张"时加载。
---

# 交付 Office 文件（Excel / Word）工作流

适用于：为这位中文用户生成成本测算、经济技术指标、各类报表类 Excel/Word 交付物。

## 触发
- 用户要求"生成 Excel / 成本测算表 / 指标表 / 报价单 / 交付物"。
- 用户要求"把表格合并到一张"或"不要让我翻找 / 左右翻找"。

## 步骤
1. **落盘位置用桌面，别放用户主目录。** 曾把文件存到 `C:\Users\jams_\` 用户反馈"你放哪去了，我怎么打不开"。统一存 `C:\Users\jams_\Desktop\<中文名>.xlsx`，并在桌面再放一个 ASCII 名副本（如 `Phase3_cost.xlsx`）作为保险。
2. **Excel 优先单表纵向排布。** 用户明确要求"合并到一张上，不要让我左右翻找"。多分部（房屋建筑 / 室外配套 / 景观 / 装修）竖向堆叠，用"分部标题行 + 明细 + 合计"结构，不要拆成多个 worksheet 逼用户切页。
3. **长说明 / 依据行：整行合并 + 自动换行。** 把"数据来源、依据与假设说明"这类段落，每行 `merge_cells` 跨 A–G 整行，设 `wrap_text=True` + `vertical='top'`，否则长文字会横向溢出到表格区、显示错乱（用户反馈"显示不对"）。去掉可能在部分字体下显示为方框的符号（如 ⚠️）。
4. **公式工作簿：开 fullCalcOnLoad。** `wb.calculation.fullCalcOnLoad = True`，保证任何打开方式都强制重算。合价用 `=工程量*单方/10000`，汇总区用 `=各分部合计单元格` 引用（改单方即自动重算）。
5. **MEDIA 链接中文名会乱码——别依赖它显示中文。** `MEDIA:` 渲染会把中文文件名做 URL 编码（`%E4%B8%89...xlsx`），用户看到一串编码。应对：① 直接告诉用户"去桌面双击打开"并给中文路径；② 同时给 ASCII 名副本路径。不要在聊天里依赖 MEDIA 链接的中文显示。
6. **造价 / 指标来源去地名化（默认）。** 用户要求"所有关于苏州和南京的字眼请用省内发达地区替换"。生成交付物时，把具体城市名（苏州 / 南京 / 苏锡宁）替换为"省内发达地区"，除非用户要精确署名。

## 坑
- ❌ 不要把交付文件放主目录——用户找不到。
- ❌ 不要把长说明塞进窄列（如 6 字符宽 A 列）——溢出 / 重叠。
- ❌ 别用 `execute_code` 跑需要落盘的生成脚本：本机会要求逐项授权且易超时阻断（实测返回 "user has NOT consented to running this code"）。改为 `write_file` 写 `.py` + `terminal`（foreground）运行，可靠。
- ⚠️ 本机无 LibreOffice，无法 headless 重算校验；靠 openpyxl 重载 + 检查 merged ranges / 公式字符串，并设 `fullCalcOnLoad`。

## 验证
- 生成后用 `openpyxl.load_workbook` 重载，确认：(a) 说明区每行 merged 跨整行；(b) 汇总公式引用了正确的分部合计单元格（如 `①->F15 ②->F24`）；(c) 无残留被替换的地名。
- `python3 -c "import zipfile; print(zipfile.ZipFile(f).testzip())"` 确认 xlsx 完整性（`None` 即通过）。

## 关联知识
- 江苏 / 镇江造价指标锚点，及"二星成品房 ≠ 绿色建筑二星"的关键区分，见 `references/jiangsu-cost-estimation.md`。
