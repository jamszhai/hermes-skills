---
name: windows-appx-language
title: Windows AppX Application Language
description: 诊断和修复 Windows AppX/应用包显示非预期语言（例如日语代替简体中文）。
trigger:
  - AppX 应用界面语言与系统首选语言不一致
  - 系统为 zh-CN，但应用显示 ja-JP 或其他语言
  - 检查 AppX manifest 内声明的可用资源语言
---

# Windows AppX 语言排查与修复指南

## 已知表现
Anthropic 发布的版本 `Claude_1.13576.0.0_x64__pzs8sxrjxfjjc` 的 `AppxManifest.xml` 只包含以下资源语言：
`en-US`, `de-DE`, `es-ES`, `es-419`, `fr-FR`, `hi-IN`, `id-ID`, `it-IT`, `ja-JP`, `ko-KR`, `pt-BR`。
不含 `zh-CN`。这是因为开发商未打包中文资源，不是用户设置错误。

## 1. 确认 AppX 信息与安装路径
```powershell
Get-AppxPackage -Name '*Claude*'
```

## 2. 查看 manifest 中的资源语言列表
```powershell
Get-Content 'C:\Program Files\WindowsApps\Claude_1.13576.0.0_x64__pzs8sxrjxfjjc\AppxManifest.xml' -TotalCount 260
```

## 3. 优先使用更稳定的查询方式
如果 PowerShell 的 AppX cmdlet 不可用或返回不完整，可直接读取 `AppxManifest.xml` 检查 `<Resources>` 节点是否 `Language` 属性包含你的首选语言。

## 4. 区分两类故障
- 应用未声明所需语言：需安装对应语言包或更换支持本地语种的应用版本；manifest 不含时无法“只改系统区域”解决。
- 系统语言回退链生效（Fallback）导致显示次级语言：通常是应用声明了系统语言，但资源缺少时被回退到系统语言支持的其他资源。

## 5. Windows 上的命令行文化与显示限制
- PowerShell 中文输出使用 `Write-Output` 时有时再被其他层转码成乱码；只用于定位问题，不用于检索关键信息。
- 使用 `Get-AppxPackage *claude*` 的精确包名更可靠。

## 6. Hermes 项目特殊说明
Claude（Anthropic 的桌面应用）会在 `C:\Users\<user>\AppData\Local\Packages\Claude_<...>\...` 留下运行数据，与本项目无关。 unrelated.