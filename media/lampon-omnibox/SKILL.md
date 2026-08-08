---
name: lampon-omnibox
description: lampon/omnibox 影视站配置、资源导入与维护（Synology NAS 专用流程）
category: media
---

# lampon/omnibox 影视站配置与维护

管理 `lampon/omnibox`（或 `lampon/omnibox:latest`）在 Synology NAS 上的部署、影视站资源导入与维护。

## 触发条件
- 用户提到 omnibox、7023 端口、lampon/omnibox、影视站资源导入失败、URL导入失败
- 需要测试影视 API 可用性或清理无效源

## 标准部署配置（docker-compose.yml）

```yaml
services:
  omnibox:
    image: lampon/omnibox:latest
    container_name: omnibox
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - NODE_ENV=production
    ports:
      - "7023:7023"
    volumes:
      - ./data:/app/data
```

数据持久化路径（Synology 典型位置）：
- `/volume2/docker/omnibox/data/data.sqlite`

## 影视站资源导入（关键规则）

**永远不要使用「URL导入」**，NAS 通常无公网出站或受防火墙限制，会导致「URL导入失败，请检查URL地址和网络连接」。

**正确做法**：
1. 进入「影视站资源」→ 「导入/导出」
2. **直接完整粘贴 JSON** 到文本框
3. 点击导入/保存

## API 连通性测试方法

对任意源的 `api` 地址，测试以下端点是否返回有效 JSON：
- `?ac=list&pg=1`
- `?ac=videolist&ids=1`

返回结构包含 `list` 或 `data` 且无明显错误即为可用。

## 推荐操作流程
1. 更新 compose 文件 → 重启容器
2. 进入 Web 管理后台导出当前 sites
3. 使用外部工具测试每个 API
4. 生成仅保留可用源的新 JSON
5. 用户重新导入

## 常见问题
- 首页空白 → 尚未导入任何影视站资源
- URL导入失败 → 改用直接粘贴 JSON
- 部分源无法播放 → 该源 API 已失效或需要代理

参考文件：
- `references/reliable-sources.json`（经过测试的可用源集合，可定期更新）
