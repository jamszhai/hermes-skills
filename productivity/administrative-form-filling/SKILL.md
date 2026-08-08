---
name: administrative-form-filling
description: "Fill structured administrative/tabular documents such as risk-assessment checklists, inspection forms, and Chinese government-style forms. Covers reading DOCX structure, identifying template fields vs. data tables, generating domain-specific content, and writing back while preserving formatting."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [DOCX, form-filling, tables, word, risk-assessment, admin-docs, chinese-forms]
    related_skills: [ocr-and-documents, powerpoint]
---

# Administrative Form Filling

Use when the user asks to fill a structured form, checklist, or administrative document — especially Chinese-style risk/廉政/inspection forms with tables, header fields, and template blanks.

## Step 1: Inspect the actual DOCX structure

`docx` files often mix **paragraphs** and **tables**. Headers, subtitles, and template fields can sit in paragraphs, not in tables.

```python
import docx

doc = docx.Document(path)
print(f"段落总数: {len(doc.paragraphs)}")
for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    if text:
        print(f"段落{i}: {repr(text)}")

print(f"\n表格总数: {len(doc.tables)}")
for t_idx, table in enumerate(doc.tables):
    print(f"\n=== 表格 {t_idx} ===")
    print(f"行数: {len(table.rows)}, 列数: {len(table.columns)}")
    for r_idx, row in enumerate(table.rows):
        print(f"行{r_idx}:" + " | ".join(cell.text.strip() for cell in row.cells))
```

> **Pitfall — `search_files` does not work on DOCX**: `.docx` is a ZIP archive; content searches may miss text stored in paragraphs, tables, or with unusual whitespace. Always inspect with `python-docx` above.

## Step 2: Identify form field locations

Typical DOCX form layouts include:
- **Title paragraph** at the top
- **Header line** with blanks (e.g. `部门：                  负责人：             日期：`) — usually a single paragraph
- **Table header row** containing column names
- **Empty table rows** intended for data

Map each field to the structure you found:
- Header fields → paragraph text replacement
- Cell values → table rows

## Step 3: Generate domain-specific content

For risk-assessment/廉政 checklists, derive content strictly from the org's actual operating environment and authority:

- **Map the org's real authority first**: independent legal entity? financial/HR autonomy? project types, revenue model, customer base. Use these to decide inclusion/exclusion, not generic lists.
- **Exclude categories the org cannot control** — e.g. a group subsidiary without independent finance/HR authority should not include independent budgeting, independent recruitment, or independent procurement risks; a design institute should not include product pricing or supply-chain risks unrelated to technical deliverables.
- **Include only operational/practical risks** — for a design institute, typical scope: bidding, design quality, confidentiality, collaboration/subcontractor selection, change orders, attendance/stamps/licenses, business-development ethics.
- **Cover labor/attendance when relevant** — if the org manages project teams and schedules directly, add a dedicated attendance/labor-discipline risk; omit if fully handled by group HR.
- **Balance risk levels** — roughly high:mid:low = 5:4:1 for comprehensive coverage.
- **Provide concrete 具体表现** — use numbered sub-items (①②③④) with specific scenarios the org actually encounters, not textbook definitions.
- **Link 防控措施** to each risk — each risk should have actionable controls tied to it, and controls should match actual authority (e.g. collective decision-making at 院班子 level if finance is centralized).

## Step 4: Write content back — avoid whitespace-pitfalls

**Option A: `patch()` with exact match** — works only when you know the exact string including whitespace.

**Option B: python-docx direct edit (preferred for safety)**

```python
import docx

doc = docx.Document(path)

# Fill header paragraph
for para in doc.paragraphs:
    if '部门：' in para.text:
        para.text = "部门：建筑设计院          负责人：翟陈明         日期：2026.07.06"
        break

# Fill table rows
for idx, item in enumerate(rows_data):
    row = table.rows[idx + 1]  # +1 to skip header
    cells = row.cells
    cells[0].text = item.get('序号', '')
    cells[1].text = item.get('风险环节', '')
    cells[2].text = item.get('风险点', '')
    cells[3].text = item.get('风险具体表现', '')
    cells[4].text = item.get('风险等级', '')
    cells[5].text = item.get('防控措施', '')

doc.save(output_path)
```

> **Pitfall — `patch()` whitespace failures**: Template blank lines in Chinese forms often contain full-width spaces (　) or em-spaces ( ). If `patch` fails twice on the same string, switch to python-docx direct edit. Do not loop on identical `patch` calls.
>
> **Pitfall — `para.text = new_text` clears runs**: Direct paragraph replacement removes rich formatting. If preserving bold/color/size in the original is important, use a more careful run-patching approach or accept plain-text replacement for form fields.

## Pitfalls

- **Authority-mismatched risk items**: For group subsidiaries without independent finance/HR, exclude finance, HR, procurement, and payroll risk items; see `references/architecture-design-institute-risk-scope.md` for a vetted authority-scoped baseline.
- **Attendance overinclusion**: `考勤管理与劳动纪律` belongs in unit-level risk lists when the unit directly manages daily project schedules/design output; omit if attendance is fully handled by group HR without unit-level influence.

## Step 5: Verify output before delivery

After writing, re-open the docx and confirm:
```python
doc = docx.Document(output_path)
# Check header
for para in doc.paragraphs:
    if '部门：' in para.text or '设计院' in para.text:
        print(f"头部: {para.text}")

# Check table data
table = doc.tables[0]
for r_idx, row in enumerate(table.rows[:3]):  # sample rows
    print(f"行{r_idx}:" + " | ".join(cell.text.strip()[:60] for cell in row.cells))
```

Save output under a new filename (`<name>_已填写.docx`) to preserve the original template.
