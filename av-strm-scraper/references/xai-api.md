# xAI / Grok API 接入事实（已查证 docs.x.ai，2026-07）

## Endpoint & 鉴权
- OpenAI 兼容：`base_url="https://api.x.ai/v1"`
- 鉴权：`Authorization: Bearer <XAI_API_KEY>`（读环境变量，**绝不硬编码**）
- Python SDK：`pip install openai`，`from openai import OpenAI`

## 联网搜索（web_search）
- 走 **Responses API**：`POST /v1/responses`，body 挂 `tools=[{"type":"web_search"}]`。
- 官方明确支持的形态（docs.x.ai/developers/tools/web-search）。**不要**用旧 "Live Search API"——已于 **2026-01-12 弃用**，迁移到 Responses/Chat Completions + web_search 工具。
- 返回含 `output_text` 与 `citations`（来源引用，利于可追溯）。
- 注意：web_search 官方示例均为 Responses API 形态；Chat Completions 下未确认支持，优先用 Responses API。

## 模型名（文本/视觉/联网搜索）
- `grok-4.5`：最强推理，官方示例默认（本 skill 默认模型）
- `grok-4`、`grok-3`：可用
- 改模型名前用 `scripts/probe.py` 列 `/v1/models` 确认存在（避免 404）。

## 官方最小示例（OpenAI SDK）
```python
from openai import OpenAI
client = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1")
r = client.responses.create(
    model="grok-4.5",
    input=[{"role": "user", "content": "..."}],
    tools=[{"type": "web_search"}],
)
print(r.output_text)
```

## AV 元数据刮削提示
- 让模型优先查 javbus / javlibrary / dmm / r18 等公开源。
- 要求只回 JSON，字段含 title / avcode / studio / actors / tags / cover_url / fanart_url / thumb_url。
- 解析时先去 ```json 围栏；失败再截取首个 `{` 到末个 `}` 做 json.loads 兜底。
- 本 skill 的 `call_grok()` 已按此实现；改 prompt 时保留"只回 JSON + 用 web_search"约束。
