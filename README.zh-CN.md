# OpenRouter 免费模型层

[English](./README.md)

这是一个轻量的数据流水线，用来追踪 OpenRouter 免费模型，并生成一个适合应用侧直接消费的稳定文件 `model_layer.json`。

这个仓库的重点不是“列出当前有哪些免费模型”，而是提供一个更稳定的接入层：上层应用可以依赖固定的 profile 别名，而不必把容易变化的 OpenRouter 模型 ID 写死在代码里。仓库同时保留每日快照，便于回溯模型增减变化。

## 仓库产物

- `model_layer.json`：主要交付物，包含稳定 profile 别名和归一化后的模型元数据。
- `known_free_models.json`：当前检测到的免费模型完整基线。
- `daily_snapshots/YYYY-MM-DD.json`：每日快照，可用于历史对比。
- `model_changes.json`：单次运行生成的差异文件，适合本地排查或调试。

## 这个项目解决什么问题

- 免费模型判断足够严格：`pricing` 中所有字段都必须为 `0`。
- 应用侧可以通过稳定 profile 路由，而不是依赖具体模型 ID。
- 每个 profile 都会生成有序候选列表，便于自动降级。
- 每日快照可以帮助你追踪模型上下线。
- 如果配置了 OpenRouter API Key，还可以用能力排序优化候选顺序。

## 内置 Profiles

当前生成的模型层内置三个 profile：

- `chat.default.free`：通用聊天。
- `chat.reasoning.free`：偏推理能力。
- `chat.longctx.free`：偏长上下文能力。

每个 profile 都使用 `selection: "ordered-fallback"`，并带有按优先级排序的 `candidate_model_ids`。

## 快速使用

### 直接消费仓库中的模型层文件

可直接读取 GitHub Raw 文件：

```text
https://raw.githubusercontent.com/cyclez2000/openrouter-free-models/main/model_layer.json
```

建议应用侧这样接入：

- 每天拉取一次。
- 本地缓存 24 小时。
- 拉取失败时继续使用上一版缓存。
- 优先按 profile 别名路由，再按 `candidate_model_ids` 顺序回退。

### 本地运行

```bash
pip install -r requirements.txt
python check_models.py
```

PowerShell 示例：

```powershell
$env:OPENROUTER_API_KEY="your_key"
python check_models.py
```

## 环境变量

- `OPENROUTER_API_KEY`：模型列表请求可不填，但建议配置，以支持能力排序。
- `OPENROUTER_CAPABILITY_RANKING`：设为 `false` 可关闭基于 LLM 的候选重排。
- `OPENROUTER_CAPABILITY_RANKER_MODEL`：覆盖默认的排序模型。

默认排序模型：

```text
openai/gpt-oss-120b:free
```

如果没有配置 API Key，或主动关闭能力排序，脚本会自动回退到本地启发式排序，不会影响主流程完成。

## 数据约定

`model_layer.json` 顶层字段如下：

- `schema_version`
- `updated_at`
- `source`
- `stats`
- `profiles`
- `models`

Profile 示例：

```json
{
  "chat.default.free": {
    "description": "General-purpose free chat profile.",
    "selection": "ordered-fallback",
    "candidate_model_ids": [
      "model-a:free",
      "model-b:free"
    ]
  }
}
```

模型条目示例：

```json
{
  "id": "google/gemma-3-27b-it:free",
  "name": "Google: Gemma 3 27B (free)",
  "context_length": 131072,
  "input_modalities": ["image", "text"],
  "output_modalities": ["text"],
  "is_moderated": false,
  "tags": ["long_context", "reasoning", "text", "vision"]
}
```

## 更新流程

当前 GitHub Actions 会在以下场景运行：

- 每日定时
- 手动触发
- `check_models.py` 或工作流文件发生变更时

单次运行会执行这些步骤：

1. 拉取 OpenRouter 当前模型列表。
2. 按严格规则筛选免费模型。
3. 写出最新基线、每日快照和模型层文件。
4. 当检测到新增或移除模型时，自动创建 GitHub Issue。
5. 将受跟踪的产物提交回 `main` 分支。

## 仓库结构

```text
openrouter-free-models/
|-- .github/workflows/check-free-models.yml
|-- check_models.py
|-- daily_snapshots/
|   `-- YYYY-MM-DD.json
|-- known_free_models.json
|-- model_changes.json
|-- model_layer.json
|-- README.md
|-- README.zh-CN.md
`-- requirements.txt
```

## 说明

- `model_layer.json` 是最适合应用直接接入的稳定文件。
- `known_free_models.json` 保留了更多 OpenRouter 原始元数据。
- `model_changes.json` 会由脚本生成，但当前工作流不会把它作为长期产物自动提交。

## 许可

当前 README 按 MIT 许可来描述仓库用途，但仓库里还没有单独的 `LICENSE` 文件。如果你希望许可条款在仓库内明确可见，建议补上一份正式的 `LICENSE`。
