---
name: av-link-dedup
description: 按番号归一化比对，清理 ed2k/magnet 链接重复并优选4K版。
---

# AV 链接去重与本地库比对（番号归一化）

抓取得到的纯文本链接列表，常需与本地已有的「目录树 txt」或「另一个链接文件」做差集：把已下载过的番号去掉，再（可选）同番号只留 4K 版。难点全在**番号归一化**——同一作品在不同来源命名五花八门（`suwk-012`、`suwk-012_4Ks.mp4`、`SUWK-025.mp4`、`JUQ-955-4K.mkv`、`JUR-031_1-4K.mkv`、`JUVR-291.PART1_8K.mp4`），必须归一后才能正确匹配。

## 两种输入
- **链接文件**：多数行以 `ed2k://` 或 `magnet:` 开头。ed2k 取 `@` 与扩展名之间的名字；magnet 取 `dn=` 参数并 `urllib.parse.unquote`。
- **目录树 txt**（如 `2024.12.06..._目录树.txt`）：每行 `| | |-sdnm-442`。先 `line.strip().strip("|").strip().lstrip("-").strip()` 得 `sdnm-442`；跳过根目录名（如 `古東まりこ`）与日期分隔行（如 `|——2024.12.06`）。**目录树文件多为 UTF-16 LE（带 BOM）**：用 `encoding="utf-16"` 读，utf-8 会报 `Binary file - cannot display`。

## 归一化算法（顺序不能乱，封装见 `scripts/dedup_links.py`）
1. 取文件名本体（见上）。
2. 转小写。
3. 去扩展名：`re.sub(r"\.[a-z0-9]+$", "", s)`
4. 去前导 `-`（目录树 `|-` 分隔符残留）。
5. **循环剥离末尾画质/分卷后缀**（每层只剥一个，直到不再变化）：
   - `[-_]?(?:4|8)ks?$`  →  `_4k / -4k / _4Ks / _1-4K / _8k`
   - `_\d+$`            →  `_1 / _2`（多分卷编号）
   - `part\d+$`         →  `part1 / part2 / part3`
6. 取基番号：`re.match(r"^([a-z0-9]+(?:[-_][a-z0-9]+)*[-_]\d+)", s)`
   例：`jur-031_1-4k` → `jur-031`；`juvr-291.part1_8k` → `juvr-291`。

## 判定规则（prefer-4K）
- 按基番号分组。
- 组里只有 1 条 → 原样保留。
- 组里有 >1 条：
  - 有 4K 版（小写含 `4k` 且不含 `8k`）→ 只留 4K 版，丢弃同番号常规版。
  - 无 4K 版（如只有 8K 分卷）→ 整组保留（不同 PART 都是要下的文件）。

## 陷阱清单（手写必踩，脚本已封装，细节见 `references/dedup-and-prefer4k.md`）
1. **目录树是 UTF-16**：`open(path, encoding="utf-16")`；先试 utf-8 再试 utf-16 最稳。
2. **树条目带前导 `-`**：来自 `|-`，不剥会污染番号（`-suwk-012` 归不到 `suwk-012`）。
3. **贪婪后缀剥离会截短番号**：`re.sub(r"[_.-]?\d*-?(4|8)ks?", ...)`（无 `$` 锚定）会把 `sdnm-427-4k` 误截成 `sdnm`（吃掉 `-427`）。**必须锚定 `$` 且循环剥离**，先去后缀、最后才取基番号。
4. **8K 分卷 ≠ 4K 可替换**：`JUVR-291.PART1_8K` 是不同物理文件，prefer-4K 判定「组内有 4K 才只留 4K，否则整组(含8K分卷)全保留」。
5. **大小写**：`JUQ-955` vs `juq-955`，归一化必须全转小写再比对。

## 用法（脚本 `scripts/dedup_links.py`）
```bash
# 模式A：与本地目录树比对，去掉已存在的番号
python scripts/dedup_links.py --links 古東まりこ.txt \
    --existing 2024.12.06..._目录树.txt --out 去重.txt

# 模式B：在去重基础上，同番号只留 4K 版
python scripts/dedup_links.py --links 去重.txt --out 优选4K.txt --prefer-4k

# 也支持「另一个链接文件」当已有库（如历史下载清单）
python scripts/dedup_links.py --links new.txt --existing old.txt --out diff.txt
```
- `--links`：待处理 ed2k/magnet 链接文件（必填）。
- `--existing`：目录树 txt 或另一个链接文件（已有库）；不填则只做 prefer-4K。
- `--prefer-4k`：同番号只留 4K 版。
- 输出 UTF-8 纯文本，每条一行（仅筛选，不改写链接本身）。
- 脚本自动识别输入类型（链接 vs 树）、自动 UTF-8/UTF-16 嗅探。

## 实测案例（2026-07 会话）
- 输入 `古東まりこ.txt`：58 条 ed2k 链接。
- 目录树：18 个已存在条目 → 归一化 15 个唯一番号。
- 模式A 去重：去掉 17 条 → 保留 41 条。
- 模式B 优选4K：41 条里 12 个番号有「常规+4K」重复，丢弃 12 条常规版 → 最终 29 条。
