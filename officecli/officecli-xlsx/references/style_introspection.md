# 样式读取与复刻范式（openpyxl）

编辑已有 xlsx 前，先跑这一段把原版配色/字体/合并/宽高读出来，直接 echo 得到的 rgb 字符串用于复刻。不要凭记忆或审美另选色。

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

src = '甲方原文件.xlsx'
wb = openpyxl.load_workbook(src)
ws = wb.active

def fillinfo(cell):
    f = cell.fill
    return (f.patternType, f.fgColor.rgb) if (f and f.patternType) else None

def fontinfo(cell):
    ft = cell.font
    return dict(bold=ft.bold, color=(ft.color.rgb if ft.color else None),
                size=ft.size, name=ft.name)

# 逐类关键行读样式（表头/单价行/合计行/分区标题行）
for r in [3, 4, 15, 19, 21, 22, 35]:   # 按实际文件调整行号
    print('row', r, 'fill', fillinfo(ws.cell(r, 1)), 'font', fontinfo(ws.cell(r, 1)))

# 合并单元格 / 列宽 / 行高
print('MERGES:', [str(m) for m in ws.merged_cells.ranges])
print('WIDTHS:', {c: d.width for c, d in ws.column_dimensions.items()})
print('RHEIGHTS:', {r: d.height for r, d in ws.row_dimensions.items() if d.height})

# 数字格式
print('D5 numfmt', ws['D5'].number_format, '| C5', ws['C5'].number_format)
```

## 复刻时的标准样板（固化原版颜色变量）
```python
NAVY  = PatternFill('solid', fgColor='FF44546A')   # 表头行
YELLOW= PatternFill('solid', fgColor='FFFFF2CC')   # 单价行（黄）
ORANGE= PatternFill('solid', fgColor='FFFCE4D6')   # 合计行（浅橙）
LBLUE = PatternFill('solid', fgColor='FFD6DCE5')   # 分区标题行（浅蓝灰）

TITLE = Font(name='微软雅黑', bold=True, size=13)
SEC   = Font(name='微软雅黑', bold=True, size=10)
HDRF  = Font(name='微软雅黑', bold=True, size=9, color='FFFFFFFF')
YELF  = Font(name='宋体', bold=True, size=9)
DATA  = Font(name='宋体', size=11)
TOTL  = Font(name='微软雅黑', bold=True, size=10)   # 合计行 A 列标签
TOTR  = Font(name='宋体', bold=True, size=11)        # 合计行 数值
SUMRED= Font(name='宋体', bold=True, size=11, color='FFC00000')  # 两项合计

ACEN  = Alignment(horizontal='center', vertical='center', wrap_text=True)
ALEFT = Alignment(horizontal='left', vertical='center', wrap_text=True)
ARIGHT= Alignment(horizontal='right', vertical='center')
thin  = Side(style='thin', color='FFBFBFBF')
BORDER= Border(left=thin, right=thin, top=thin, bottom=thin)

N='#,##0'; N2='#,##0.00'; N1='#,##0.0'
```

## 真实验证口诀（本会话踩坑）
- 重算后必须 `wb.save()` 成功、再重新 `load_workbook` 回读关键单元格的 `fill.fgColor.rgb` 与 `value`，确认颜色一致且合计正确。
- 删除低价行（如电房/通道）后，建筑单方会"被抬高"（分母变小），属正常，在底部注记里说明口径变化即可。
- 永远另存为新文件名（后缀 `_商办楼` 等），不动甲方原文件。
