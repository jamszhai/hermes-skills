---
name: windows-appx-deploy
title: Windows AppX/MSIX 安装与首次注册失败排查
description: 诊断并修复 MSIX/AppX 桌面应用（ChatGPT、Codex、Claude 等）安装后首次运行卡在“完成 Windows 设置 / Windows 安装未完成 / 需要一次性权限”的问题。
trigger:
  - 商店安装的桌面应用首次打开卡在“完成 Windows 设置”或“Windows 安装未完成”
  - 应用弹“需要一次性权限才能在你的电脑上运行”后失败，点击重试无反应
  - MSIX 包带 fullTrust 能力，普通运行无法完成首次注册
  - 重装、重启、清残留都无效，症状每次都一样
---

# Windows AppX/MSIX 安装与首次注册失败排查

## 根因模型
现代桌面应用（OpenAI ChatGPT/Codex、Claude 等）以 MSIX 分发，manifest 常带 `fullTrust` 能力。
首次运行需在用户账户下完成包注册（`Add-AppxPackage -Register`），这一步需要**提升令牌**。
即使你是管理员，只要进程跑在 UAC 过滤后的“标准令牌”下，注册会被静默拒绝 → 系统回退显示
“Windows 安装未完成”，重试永远卡在同一个提权环节（无反应）。

典型症状链：
1. 商店下载完 → 首次打开“需要一次性权限才能运行”（fullTrust 注册要约提权）。
2. 当前进程是非提升令牌 → 提权被拒/没弹 UAC。
3. 回退“Windows 安装未完成”，重试无效。

## ★ 两个必须先知道的诊断陷阱（踩过坑）
1. **不要用 `WindowsPrincipal.IsInRole(Administrator)` 判断是不是管理员。**
   在非提升终端里它对“属于管理员组的用户”也返回 `False`（只看到过滤后的令牌）。
   可靠做法：`net localgroup administrators`（直接读组成员，能看见当前用户在不在列表里）。
2. **PowerShell 5.1 按系统 ANSI 编码（zh-CN 机器 = GBK）读取 .ps1 文件。**
   UTF-8 含中文的脚本会把字符串里的引号啃乱，报 `MissingArgument` / `字符串缺少终止符` /
   `Try 语句缺少自己的 Catch`。**写 .ps1 一律只用 ASCII/英文**，或保存为 UTF-8 BOM。
   之前那次报错不是用户操作错，是 UTF-8 中文被 GBK 误读。

## 诊断步骤（按顺序，全 ASCII 命令）
见 `references/diagnostic-recipe.md`，含精确命令与判读。要点：
- `Get-AppxPackage *ChatGPT*` 看当前用户是否已注册（空=没注册上）。
- `net localgroup administrators` 确认真实管理员身份（别用 IsInRole）。
- 查 `HKCU:\Software\Classes\Local Settings\...\AppModel\Repository\Packages` 是否只剩旧包残留。
- 查开始菜单快捷方式是否生成。
- 查 UAC：`Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System`
  `ConsentPromptBehaviorUser=3` 表示标准用户提权被自动拒绝（不弹框）。

## 修复
**核心：用真正的提升令牌完成注册。**
- 方式 A（推荐，省心）：自提升脚本 —— 检测非提升时自动 `Start-Process powershell -Verb RunAs`
  重新跑自己，强制弹 UAC，点“是”后即获得管理员令牌，再执行安装/注册。模板见
  `scripts/install-chatgpt-selfelevate.ps1`（可改成任意 Store 产品 ID）。
- 方式 B（手动）：以管理员身份打开 PowerShell，跑
  `Add-AppxPackage -Register "<InstallLocation>\AppxManifest.xml" -DisableDevelopmentMode`
  先 `Get-AppxPackage -AllUsers *<app>*` 拿到 InstallLocation。

## UAC / 账户提示
- 若机器上**没有任何启用的管理员账户**（仅标准用户 + 禁用的 Administrator），标准用户无法装
  fullTrust 应用是设计使然，需启用内置 Administrator（安全模式/离线）或找 IT 推送。
- 第三方杀软/组策略可能吞掉 UAC 弹窗，必要时临时退出实时防护。

## 事实速记：Codex 已内置进 ChatGPT 桌面端
OpenAI 自 2026 起把 Codex 合并进新的 ChatGPT 桌面端（Windows/macOS 一体，含 Chat、Work、Codex），
独立 Codex app 逐步退役。装“新 ChatGPT 桌面端”即自带 Codex，无需单独装。
ChatGPT 商店产品 ID：`9NT1M9S3F2QF`（winget: `winget install --id 9NT1M9S3F2QF -e`）。
