---
name: gbox-xiaoya-storage
description: G-Box / alist-tvbox (小雅集成版) 自动存储加载与 /root/etc/xiaoya 目录配置
---

# G-Box / alist-tvbox 自动存储加载

G-Box（alist-tvbox）在 xiaoya profile 下会尝试自动加载 `/root/etc/xiaoya` 目录下的内容作为 AList storage。

## 典型目录结构
- `/root/etc/xiaoya` 是小雅数据主目录
- 常见子目录：`aliyundrive`、`config`、`data` 等

## 常见问题
- AList 启动后显示 `failed get storage: storage not found`
- G-Box 配置页显示 AList “运行中”，但首页仍报错
- 自动加载失败时，需要手动添加本地存储

## 推荐配置（当自动加载失败时）
在 AList 管理后台（通常 5678 端口）添加本地存储：

**主存储**
- 名称：`xiaoya`
- 驱动：本地
- 根文件夹路径：`/root/etc/xiaoya`
- 挂载路径：`/xiaoya`

**阿里云盘子目录（可选）**
- 名称：`ali`
- 驱动：本地
- 根文件夹路径：`/root/etc/xiaoya/aliyundrive`
- 挂载路径：`/ali`

添加后刷新首页即可生效。

## 调试步骤
1. 确认 G-Box 使用 xiaoya profile
2. 重启 AList（配置页按钮）
3. 检查 AList 日志中是否有 storage 加载记录
4. 若仍为 0 storage，手动添加上述本地存储

此技能优先使用自动加载，仅在失败时手动添加。