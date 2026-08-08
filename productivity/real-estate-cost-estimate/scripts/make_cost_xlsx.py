#!/usr/bin/env python3
# 复用型：地产项目成本测算 Excel 生成器（公式驱动，单价可改自动重算）
# 用法：把下面的 items 数据改成你的项目，运行即可。
#   python3 make_cost_xlsx.py
# 依赖：openpyxl（缺失会自动 pip install）
import sys, subprocess
try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openpyxl', '-q'])
    import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PATH = r"./地产成本测算.xlsx"
TOTAL_AREA = 63150  # 总建面，用于汇总单方/占比分母

thin = Side(style='thin', color='B0B0B0')
border = Border(left=thin, right=thin, top=thin, bottom=thin)
hdr_fill = PatternFill('solid', fgColor='1F4E78')
tot_fill = PatternFill('solid', fgColor='FCE4D6')
hdr_font = Font(bold=True, color='FFFFFF', size=11)
title_font = Font(bold=True, size=14, color='1F4E78')
note_font = Font(italic=True, size=9, color='666666')
bold = Font(bold=True)
center = Alignment(horizontal='center', vertical='center', wrap_text=True)
left = Alignment(horizontal='left', vertical='center', wrap_text=True)
right = Alignment(horizontal='right', vertical='center')

def setw(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

def header_row(ws, row, headers):
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.alignment = center; cell.border = border

def detail_sheet(name, title, headers, rows, note):
    ws = wb.create_sheet(name)
    ws.cell(row=1, column=1, value=title).font = title_font
    ws.cell(row=2, column=1, value=note).font = note_font
    hrow = 4
    header_row(ws, hrow, headers)
    r = hrow + 1
    first = r
    for idx, item, qty, unit, price, why in rows:
        ws.cell(row=r, column=1, value=idx).alignment = center
        ws.cell(row=r, column=2, value=item).alignment = left
        ws.cell(row=r, column=3, value=qty).alignment = right
        ws.cell(row=r, column=4, value=unit).alignment = center
        pc = ws.cell(row=r, column=5, value=price); pc.alignment = right; pc.number_format = '#,##0'
        fc = ws.cell(row=r, column=6, value=f"=C{r}*E{r}/10000"); fc.alignment = right; fc.number_format = '#,##0.0'
        ws.cell(row=r, column=7, value=why).alignment = left
        for c in range(1, 8):
            ws.cell(row=r, column=c).border = border
        r += 1
    last = r - 1
    ws.cell(row=r, column=2, value="合计").font = bold
    tc = ws.cell(row=r, column=6, value=f"=SUM(F{first}:F{last})"); tc.font = bold; tc.alignment = right; tc.number_format = '#,##0.0'
    for c in range(1, 8):
        ws.cell(row=r, column=c).border = border
    ws.cell(row=r, column=6).fill = tot_fill
    setw(ws, [6, 34, 12, 8, 12, 14, 46])
    return f"'{name}'!F{r}"

wb = openpyxl.Workbook()

# ===== 数据区：按项目修改 =====
ref1 = detail_sheet(
    "1-房屋建筑", "① 房屋建筑（毛坯建安，不含装修）",
    ["序号", "分项", "工程量", "单位", "单方(元/m²)", "合价(万元)", "依据/说明"],
    [
        (1, "高层住宅（15F 剪力墙）", 31160, "m²", 3700, "苏州7–17层毛坯中值3,160–3,980，镇江下浮"),
        (2, "商业（裙房）", 3180, "m²", 3100, "框架结构，公区/消防标准"),
        (3, "酒店（15F）", 13930, "m²", 4200, "机电/消防/公区标准高于住宅"),
        (4, "配套（物业+消控+公厕）", 260 + 50 + 50, "m²", 3300, "260+50+50，基本装修"),
        (5, "地下室（含车库，非人防为主）", 14520, "m²", 3500, "苏州非人防中值3,200–4,100，镇江下浮"),
        (6, "桩基", 63150, "m²", 150, "管桩，以总建面为基数"),
        (7, "基坑围护", 63150, "m²", 120, "1–2道围护，以总建面为基数"),
        (8, "土方", 63150, "m²", 120, "余土外运+回填，以总建面为基数"),
    ],
    "注：毛坯建安（含基本公区简装、基本机电消防），不含户内装修。装修见专项单列项，避免重复。")

ref2 = detail_sheet(
    "2-室外配套", "② 室外配套（市政附属）",
    ["序号", "分项", "工程量", "单位", "单方(元)", "合价(万元)", "依据/说明"],
    [
        (1, "道路及场地硬化", 12490, "m²", 250, "约250元/m²"),
        (2, "室外管网（给排水/强弱电/燃气/消防外网）", 20400, "m²", 400, "按用地面积；参照招标市政配套上限"),
        (3, "围墙/大门/门卫", 1, "项", 1800000, "估算"),
        (4, "路灯/智能化/标识/环卫", 1, "项", 2000000, "估算"),
        (5, "生化池/隔油池等", 1, "项", 710000, "估算"),
    ],
    "注：综合约 250 元/m²（按总建面）。")

ref3 = detail_sheet(
    "3-室外景观", "③ 室外高档景观",
    ["序号", "分项", "工程量", "单位", "单方(元/m²)", "合价(万元)", "依据/说明"],
    [(1, "集中景观+绿地+宅间+入口+水景", 11000, "m²", 500, "高档 300–600元/m² 取中值")],
    "注：按景观面积计（非绿地面积）。")

ref4 = detail_sheet(
    "4-专项装修", "④ 住宅二星成品房装修（单列）",
    ["序号", "分项", "工程量", "单位", "单方(元/m²)", "合价(万元)", "依据/说明"],
    [(1, "住宅全装修（二星成品房标准）", 31160, "m²", 1500, "《江苏省成品住房装修技术标准》舒适型；镇江取1,200–1,800中值")],
    "注：二星成品房≠绿色建筑二星。仅住宅计，与毛坯建安不重复。")

# ===== 汇总 =====
ws = wb.active
ws.title = "测算汇总"
ws.cell(row=1, column=1, value="项目成本测算汇总").font = title_font
ws.cell(row=2, column=1, value=f"单位：万元 | 总建面 {TOTAL_AREA:,} m² | 房屋建筑=毛坯建安，装修已单列").font = note_font
header_row(ws, 4, ["序号", "成本部分", "合价(万元)", "单方(元/m²·总建面)", "占比"])
data = [
    ("①", "房屋建筑（毛坯建安）", ref1),
    ("②", "室外配套（市政附属）", ref2),
    ("③", "室外高档景观", ref3),
    ("④", "专项装修（单列）", ref4),
]
r = 5
first = r
total_row = r + len(data)
for lab, name, ref in data:
    ws.cell(row=r, column=1, value=lab).alignment = center
    ws.cell(row=r, column=2, value=name).alignment = left
    vc = ws.cell(row=r, column=3, value=f"={ref}"); vc.alignment = right; vc.number_format = '#,##0.0'
    uc = ws.cell(row=r, column=4, value=f"=C{r}*10000/{TOTAL_AREA}"); uc.alignment = right; uc.number_format = '#,##0'
    pc = ws.cell(row=r, column=5, value=f"=C{r}/$C${total_row}"); pc.alignment = right; pc.number_format = '0.0%'
    for c in range(1, 6):
        ws.cell(row=r, column=c).border = border
    r += 1
last = r - 1
ws.cell(row=r, column=2, value="合计").font = bold
tc = ws.cell(row=r, column=3, value=f"=SUM(C{first}:C{last})"); tc.font = bold; tc.alignment = right; tc.number_format = '#,##0.0'; tc.fill = tot_fill
uc = ws.cell(row=r, column=4, value=f"=C{r}*10000/{TOTAL_AREA}"); uc.font = bold; uc.alignment = right; uc.number_format = '#,##0'; uc.fill = tot_fill
ws.cell(row=r, column=5, value=1.0).alignment = right
for c in range(1, 6):
    cell = ws.cell(row=r, column=c); cell.border = border
    if c in (3, 4): cell.fill = tot_fill
setw(ws, [6, 34, 14, 20, 10])

wb.calculation.fullCalcOnLoad = True  # 打开即强制重算
wb.save(PATH)
print("SAVED:", PATH)
print("Sheets:", wb.sheetnames)
