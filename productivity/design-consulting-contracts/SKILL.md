---
name: design-consulting-contracts
description: Draft design consulting contracts for urban renewal/engineering projects referencing the 江苏省工程勘察设计收费导则. Generate MD + DOCX, structure fee basis with full audit trail.
platforms: [windows]
---

# Design Consulting Contracts（设计咨询合同起草）

Use this skill when the user asks you to draft, modify, or complete a design consulting contract for Chinese urban renewal / engineering design projects.

## Workflow

### 1. Read the Fee Standard

The authoritative reference is `F:\Obsidian Vault\LLM Wiki\raw\assets\江苏省工程勘察设计收费标准导则2024版.md`.

Search for and read the specific table relevant to the user's work scope:

| Work Type | Table No. | Fee Method |
|-----------|-----------|------------|
| 前期基础调查（用地及房屋权属/地段评估） | 表3.2.3-1 | 总体方案费用的 10~20% |
| 项目开发策划 | 表3.2.3-2 | 按用地规模：60~100万元 |
| **功能业态策划** | **表3.2.3-3** | 按建设面积 元/m²，基价10万元 |
| 城市更新总体方案 | 表3.2.3-4 | 按用地面积 万元/公顷，基价60万元 |
| 重要节点概念方案 | 表3.2.3-6 | 15~30万元/个 |

### 2. Draft Fee Basis Section (3.1)

Structure **3.1 取费依据** in this EXACT order:

```
3.1  取费依据

本合同费用依据《江苏省工程勘察设计收费导则（2024版）》第3.2节（城市更新收费）相关规定，
按【表号+名称】计取，具体如下：

（1）收费基价/费率引用（附基价金额，大小写）；
（2）参考费用区间（如有）；
（3）经甲乙双方友好协商，乙方给予优惠，按【折扣率】折扣计取。
```

### 3. Draft Contract

Include all standard clauses:

| Clause | Content |
|--------|---------|
| 第一条 | 项目概况（名称、地点、范围、阶段） |
| 第二条 | 工作内容及成果要求（详述 scope + deliverables） |
| 第三条 | 合同金额及支付（fee basis → final price → payment） |
| 第四条 | 付款方式（阶段比例 + 天数） |
| 第五条 | 双方权利义务 |
| 第六条 | 工作期限（first draft 7日历天 → review → revise） |
| 第七条 | 知识产权与保密 |
| 第八条 | 违约责任（万分之五/日） |
| 第九条 | 不可抗力 |
| 第十条 | 争议解决（项目所在地法院） |
| 第十一条 | 其他约定 |
| 附件 | 工作范围示意图 + 成果清单 |

### 4. Generate Word Version

Use python-docx to produce a formatted `.docx`:

```python
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def set_run_font(run, name='宋体', size=12, bold=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.element.rPr.rFonts.set(qn('w:eastAsia'), name)

def add_body(text, bold=False, indent=True):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run(text)
    set_run_font(run, '宋体', 12, bold)
```

### 5. Save Locations

| File | Path |
|------|------|
| MD (source) | `F:\Obsidian Vault\LLM Wiki\{项目文件夹}\设计咨询合同（{项目简称}）.md` |
| DOCX (Word) | `F:\Obsidian Vault\LLM Wiki\{项目文件夹}\设计咨询合同（{项目简称}）.docx` |
| Desktop copy | `C:\Users\jams_\Desktop\设计咨询合同（{项目简称}）.docx` |

### 6. Payment Split Convention

| Payment | Timing | Percentage |
|---------|--------|------------|
| 第一次付款 | 合同签订生效后7个日历天内 | **50%** |
| 第二次付款（尾款） | 成果确认合格后7个日历天内 | **50%** |

## User Preferences

- 合同总金额：人民币大写+小写并写，如"玖万元整（¥90,000.00）"
- 项目文件夹名：`{甲方简称}{项目主题}咨询合同`，如"和润控股镇江文旅水街项目咨询合同"
- 费用显示必须完整链条：表号引用 → 基价 → 参考区间 → 折扣率 → 最终价格
- 工作期限写法：7个日历天提交第一稿 → 经甲方委托的策划单位审议修改 → 提交最终稿（修改时间不计入7天）
- 每次更新合同后，MD和DOCX两个版本**同步更新**
- 每次修改合同后告知用户核心变更点

## Pitfalls

- 不要擅自添加用户未提及的工作内容项（如之前误加"地段评估"被用户纠正）
- 取费标准只是测算依据，最终价格永远以友好协商为准——引用导则后必须写"经甲乙双方友好协商，乙方给予优惠"
- 用户说"发票信息暂时不填"时，收款账户信息全部留空
- 用户要的是"咨询合同"不是"设计合同"（咨询在策划阶段，设计在工程实施阶段）
- 文件命名中项目简称用中文关键词而非英文
- 如工作内容从A改为B，须同步更新：项目名称、1.1条、2.1工作内容、2.2成果名称、3.1取费依据、文件名