---
name: exam-paper-generator
description: "Use when the user asks you to generate, format, or adapt exam papers (出试卷). Covers math, physics, chemistry, Chinese, English, and other subjects with multiple question types and output formats."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [exam, paper, education, latex, markdown, chinese, 出卷, 试卷]
    related_skills: [plan]
---

# Exam Paper Generator (出试卷)

## Overview

Generate exam papers (试卷) of any subject, type, and difficulty level. This skill defines templates, question-type conventions, format standards (LaTeX, Markdown, plain text), and workflows for producing complete, printable exam papers.

## When to Use

- User asks "帮我出一份数学试卷" or "generate a physics exam"
- User needs a midterm/final/practice exam with specified scope
- User wants to convert an existing exam into another format
- User provides a list of knowledge points and wants a structured exam
- User needs an answer key / scoring rubric alongside the exam

**Don't use for:** Homework assignments (use a simpler task-specific workflow instead).

## Supported Subjects

| Subject | Chinese Name | Question-Type Emphasis |
|---------|-------------|----------------------|
| Mathematics (Math) | 数学 | Computation, proof, multiple-choice, fill-in-blank |
| Physics | 物理 | Calculation, conceptual, experimental design |
| Chemistry | 化学 | Equations, nomenclature, calculation, experiment |
| Chinese (语文) | 语文 | Reading comprehension, essay, classical Chinese, vocab |
| English | 英语 | Reading, grammar, cloze, writing, listening |
| Biology | 生物 | Multiple-choice, fill-in, short answer, diagrams |
| History | 历史 | Chronology, short answer, essay, multiple-choice |
| Geography | 地理 | Map reading, multiple-choice, short answer |
| Politics / Ethics | 政治/道法 | Short answer, essay, case analysis |
| General / Mixed | 综合 | Custom combination |

## Question Types

| Type | Code | Description |
|------|------|-------------|
| Multiple Choice | `mc` | 选择题 (单选题/多选题) |
| Fill in the Blank | `fb` | 填空题 |
| True / False | `tf` | 判断题 |
| Matching | `match` | 连线题 / 配对题 |
| Short Answer | `sa` | 简答题 |
| Calculation | `calc` | 计算题 (math/physics/chem) |
| Proof | `proof` | 证明题 (math) |
| Reading Comprehension | `reading` | 阅读理解 (语文/英语) |
| Cloze | `cloze` | 完形填空 (English) |
| Essay / Writing | `essay` | 作文题 |
| Classical Chinese | `classical` | 文言文阅读 (语文) |
| Experimental | `exp` | 实验题 (physics/chem/bio) |
| Diagram / Graph | `diagram` | 作图题 / 看图题 |

## Difficulty Levels

| Level | Code | Description |
|-------|------|-------------|
| Easy | `easy` | 基础题 (~30% of paper) |
| Medium | `medium` | 中等题 (~50% of paper) |
| Hard | `hard` | 难题 (~15% of paper) |
| Challenge | `challenge` | 压轴题 (~5% of paper) |

## Output Formats

### 1. LaTeX (`latex`)

Use when the user wants a printable, professionally formatted PDF-ready exam. LaTeX with `ctex` or `xeCJK` package for Chinese.

**Template:**

```latex
\documentclass[12pt,a4paper]{article}
\usepackage{ctex}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}
\usepackage{enumitem}
\usepackage{fancyhdr}
\pagestyle{fancy}
\lhead{学校名称}
\chead{2024-2025学年第一学期期中考试}
\rhead{数学}
\lfoot{第 \thepage 页 共 N 页}
\cfoot{}
\rfoot{}

\title{\textbf{2024-2025学年第一学期期中考试\\数学试卷}}
\author{考试时间：90分钟\quad 满分：100分}
\date{}

\begin{document}
\maketitle

\noindent\textbf{姓名：\_\_\_\_\_\_\_ \quad 班级：\_\_\_\_\_\_\_ \quad 考号：\_\_\_\_\_\_\_}

\vspace{0.5cm}

\noindent\textbf{注意事项：}
\begin{enumerate}[label=\arabic*.]
  \item 答题前请填写姓名、班级、考号。
  \item 请在答题卡上作答。
  \item 考试结束后，将试卷和答题卡一并交回。
\end{enumerate}

% === 一、选择题 ===
\section*{一、选择题（每小题3分，共30分）}

\begin{enumerate}[label=\textbf{\arabic*.}]
  \item 题目内容
  \begin{enumerate}[label=(\Alph*)]
    \item 选项A
    \item 选项B
    \item 选项C
    \item 选项D
  \end{enumerate}

  \item ...
\end{enumerate}

% === 二、填空题 ===
\section*{二、填空题（每小题3分，共15分）}
\begin{enumerate}[label=\textbf{\arabic*.}]
  \item 题目内容\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
\end{enumerate}

% === 三、解答题 ===
\section*{三、解答题（共55分）}
\begin{enumerate}[label=\textbf{\arabic*.}]
  \item （10分）题目内容
  \vspace{4cm}
  \item ...
\end{enumerate}

\end{document}
```

### 2. Markdown (`markdown`)

Use when the user wants quick preview or web-friendly format.

**Template:**

```markdown
# 2024-2025学年第一学期期中考试
## 数学试卷

**考试时间：90分钟 &emsp; 满分：100分**

姓名：\_\_\_\_\_\_\_ &emsp; 班级：\_\_\_\_\_\_\_ &emsp; 考号：\_\_\_\_\_\_\_

---

## 一、选择题（每小题3分，共30分）

1. 题目内容
   A. 选项A &emsp; B. 选项B &emsp; C. 选项C &emsp; D. 选项D

2. ...

---

## 二、填空题（每小题3分，共15分）

1. 题目内容\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

## 三、解答题（共55分）

1. （10分）题目内容

   **解：** （空白区域）
```

### 3. Plain Text (`txt`)

For simple/quick output, paste into Word or other editors.

## Common Exam Types

| Exam Type | Chinese | Typical Duration | Typical Full Marks |
|-----------|---------|-----------------|-------------------|
| Unit Test | 单元测试 | 45 min | 100 |
| Midterm | 期中考试 | 90-120 min | 100-150 |
| Final | 期末考试 | 90-120 min | 100-150 |
| Mock Exam | 模拟考试 | 120 min | 100-150 |
| Quiz | 随堂测验 | 15-20 min | 30-50 |
| Practice | 练习卷 | varies | varies |
| Comprehensive | 综合测试 | 120 min | 150 |

## Answer Key Format

Always produce an answer key (答案/参考答案) alongside the exam. Include:

### LaTeX Answer Key

```latex
\newpage
\section*{参考答案}

\subsection*{一、选择题}
\begin{enumerate}[label=\textbf{\arabic*.}]
  \item B \quad 2. C \quad 3. A \quad 4. D \quad ...
\end{enumerate}

\subsection*{二、填空题}
\begin{enumerate}[label=\textbf{\arabic*.}]
  \item \(x = 3\) \quad 2. \(y = 2x + 1\) \quad ...
\end{enumerate}

\subsection*{三、解答题}
\begin{enumerate}[label=\textbf{\arabic*.}]
  \item \textbf{解：} 详细过程...
\end{enumerate}
```

### Markdown Answer Key

```markdown
## 参考答案

### 一、选择题
1. B　2. C　3. A　4. D　...

### 二、填空题
1. x = 3　2. y = 2x + 1　...

### 三、解答题（评分要点）
1. **解：** 详细过程...（分步骤给分）
```

## Scoring Rubric Format

For subjective questions (essays, short answers, proofs), include a scoring rubric:

```
【评分标准】
- 写出正确公式或定理：2分
- 代入正确数值：2分
- 计算过程完整：3分
- 最终答案正确：3分
- 共：10分
```

## Workflow

1. **Clarify scope (if user hasn't specified):**
   - Subject / grade level
   - Exam type (unit test, midterm, final, mock)
   - Knowledge points to cover
   - Difficulty distribution (default: 30% easy, 50% medium, 15% hard, 5% challenge)
   - Number of questions per section
   - Output format (LaTeX / Markdown / Plain Text)
   - Want answer key? (default: yes)

2. **Build the paper structure:**
   - Header (title, school, date, duration, full marks)
   - Instructions / notices
   - Section 1: Multiple Choice
   - Section 2: Fill-in-the-blank
   - Section 3: ... (depends on exam type)
   - Footer (page numbering)
   - Answer key page (separate)

3. **Write questions:**
   - Distribute evenly across knowledge points
   - Follow difficulty distribution
   - Ensure no duplicate or overlapping content
   - Use realistic numbers/values
   - Include unit labels where applicable

4. **Generate output files:**
   - For LaTeX: write to `exam-<subject>-<type>-<date>.tex`
   - For Markdown: write to `exam-<subject>-<type>-<date>.md`
   - If answer key: either same file with separator, or `exam-<subject>-<type>-<date>-key.*`

5. **Verify:**
   - Check all questions have point values
   - Verify total points match full marks
   - Check answer key matches question numbers
   - For LaTeX: suggest compilation with `xelatex`

## Compiling LaTeX on Windows

```bash
# If MiKTeX or TeX Live is installed:
xelatex exam-math-midterm-2024.tex
# Or use pdflatex if no Chinese characters:
pdflatex exam-math-midterm-2024.tex
```

## Compiling LaTeX on Linux / macOS

```bash
xelatex exam-math-midterm-2024.tex
# Twice for cross-references if needed
xelatex exam-math-midterm-2024.tex
```

## Common Pitfalls

1. **Inconsistent point totals.** Always verify that the sum of all question points equals the stated full marks.
2. **Forgotten answer key.** Always generate a separate answer key or answer section.
3. **Unbalanced difficulty.** Default distribution should be ~30% easy, ~50% medium, ~15% hard, ~5% challenge. Adjust per user request.
4. **Overlapping knowledge points.** Each question should test distinct content unless explicitly reviewing the same topic.
5. **LaTeX without Chinese support.** Use `ctex` or `xeCJK` package; compile with `xelatex`, not `pdflatex`.
6. **Missing exam instructions.** Always include duration, full marks, and submission instructions.
7. **No page numbering.** Print-friendly exams need page numbers like "第 X 页 共 N 页".

## Verification Checklist

- [ ] Paper header includes: title, exam type, subject, duration, full marks, name/class/ID fields
- [ ] Instructions / notices section present
- [ ] Questions cover specified knowledge points with even distribution
- [ ] Difficulty distribution matches spec or defaults (30/50/15/5)
- [ ] Total points of all questions match the stated full marks
- [ ] All questions have allocated point values
- [ ] No duplicate or overlapping question content
- [ ] Answer key provided (separate or appended)
- [ ] Scoring rubric provided for subjective questions
- [ ] Output format matches user's request (LaTeX/Markdown/Plain)
- [ ] File saved with descriptive name: `exam-<subject>-<type>-<date>.<ext>`
- [ ] For LaTeX: document compiles cleanly with `xelatex`

## One-Shot Recipes

### Recipe 1: Quick Chinese Math Midterm (Markdown)

```
User: "帮我出一份初一数学期中考试卷，Markdown格式"
→ Generate a 100-mark, 90-min exam with:
   - 选择题 (10 × 3 = 30分)
   - 填空题 (5 × 3 = 15分)
   - 解答题 (5 × 11 = 55分)
   Topics: rational numbers, linear equations, geometry basics
→ Save as exam-math-grade7-midterm-<date>.md
→ Append answer key at the bottom
```

### Recipe 2: Physics Unit Test (LaTeX)

```
User: "帮我出一份高中物理单元测试卷，LaTeX格式"
→ Generate a 100-mark, 45-min unit test on kinematics with:
   - 选择题 (8 × 4 = 32分)
   - 填空题 (4 × 4 = 16分)
   - 计算题 (4 × 13 = 52分)
→ Save as exam-physics-kinematics-<date>.tex
→ Separate answer key file
```

### Recipe 3: English Comprehensive Exam

```
User: "高三英语模拟卷"
→ Generate a 150-mark, 120-min mock exam with:
   - 阅读理解 (4 passages, 20 × 2 = 40分)
   - 完形填空 (15 × 1.5 = 22.5分)
   - 语法填空 (10 × 1.5 = 15分)
   - 短文改错 (10 × 1 = 10分)
   - 书面表达 (1 × 25 = 25分)
   - 听力 (20 × 1.5 = 30分)
→ Markdown format
```

### Recipe 4: Math Problem-Solving Paper (LaTeX)

```
User: "帮我出一份初中数学培优卷，侧重几何证明"
→ 90-min, 100-mark advanced paper with:
   - 填空题 (6 × 4 = 24分)
   - 证明题 (3 × 12 = 36分)
   - 综合压轴题 (2 × 20 = 40分)
→ LaTeX, compile-ready
→ Detailed scoring rubric for each proof
```