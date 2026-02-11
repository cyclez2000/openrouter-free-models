# OpenRouter Free Models Layer / OpenRouter 免费模型层

Last revised: `2026-02-11`

A public model-layer data source for OpenRouter free models.

一个面向应用侧的公开模型层数据源，聚合 OpenRouter 免费模型。

## What this project does / 项目功能

- Update free-model list daily.
- Use strict free detection: all fields in `pricing` must be `0`.
- Publish stable profile aliases in `model_layer.json`.
- Keep `model_layer.json` schema stable for app compatibility.
- Reorder profile candidates by capability ranking (single ranker call per run).
- Fall back to local heuristic order when capability ranking is unavailable.
- Keep historical snapshots in `daily_snapshots/YYYY-MM-DD.json`.

- 每日更新免费模型列表。
- 使用严格免费判定：`pricing` 所有字段都必须为 `0`。
- 在 `model_layer.json` 中发布稳定 profile 别名。
- 保持 `model_layer.json` 结构稳定，确保应用兼容。
- 每次运行使用一次能力排序模型，对 profile 候选模型重排。
- 当能力排序不可用时，自动回退到本地启发式排序。
- 在 `daily_snapshots/YYYY-MM-DD.json` 中保留历史快照。

## Usage / 使用说明

### 1) Get model layer file / 获取模型层文件

`https://raw.githubusercontent.com/<owner>/<repo>/main/model_layer.json`

### 2) Route by profile / 按 profile 路由

Use profile aliases instead of hard-coded model IDs.

应用请使用 profile 别名，不要写死具体模型 ID。

Built-in profiles:

内置 profile：

- `chat.default.free`
- `chat.reasoning.free`
- `chat.longctx.free`

Each profile has ordered `candidate_model_ids` for fallback.

每个 profile 都有有序 `candidate_model_ids` 用于降级。

### 3) Refresh strategy / 刷新策略

- Refresh once per day.
- Cache for 24 hours locally.
- Keep previous cache when fetch fails.

- 每天刷新一次。
- 本地缓存 24 小时。
- 拉取失败时继续使用上一版缓存。

## Model Layer Contract / 模型层约定

Top-level keys:

顶层字段：

- `schema_version`
- `updated_at`
- `stats`
- `profiles`
- `models`

Profile example:

profile 示例：

```json
{
  "chat.default.free": {
    "description": "General-purpose free chat profile.",
    "selection": "ordered-fallback",
    "candidate_model_ids": ["model-a:free", "model-b:free"]
  }
}
```

## Outputs / 输出文件

- `model_layer.json`: app-facing model layer.
- `known_free_models.json`: latest baseline.
- `daily_snapshots/YYYY-MM-DD.json`: daily snapshot history.
- `model_changes.json`: run-level change details.

- `model_layer.json`：应用侧使用的模型层文件。
- `known_free_models.json`：最新基线。
- `daily_snapshots/YYYY-MM-DD.json`：每日快照历史。
- `model_changes.json`：单次运行差异细节。

## Maintainer Notes / 维护者说明

```bash
pip install -r requirements.txt
python check_models.py
```

PowerShell (optional key):

```powershell
$env:OPENROUTER_API_KEY="your_key"
python check_models.py
```

Capability ranking behavior:

能力排序行为：

- The script calls one ranker model once per run to reorder profile candidates by capability.
- Default ranker: `openai/gpt-oss-120b:free`
- Override ranker via `OPENROUTER_CAPABILITY_RANKER_MODEL`
- Disable ranker via `OPENROUTER_CAPABILITY_RANKING=false` (fallback to local heuristic order)
- If `OPENROUTER_API_KEY` is missing, ranker call is skipped automatically (no failure).
- 脚本每次运行只调用一次排序模型，用于按能力重排候选模型。
- 默认排序模型：`openai/gpt-oss-120b:free`
- 可通过 `OPENROUTER_CAPABILITY_RANKER_MODEL` 覆盖排序模型。
- 可通过 `OPENROUTER_CAPABILITY_RANKING=false` 关闭能力排序（回退本地启发式顺序）。
- 如果未配置 `OPENROUTER_API_KEY`，会自动跳过排序请求，不影响主流程。

## Repository structure / 目录结构

```text
openrouter-free-models/
├── check_models.py
├── known_free_models.json
├── model_layer.json
├── daily_snapshots/
│   └── YYYY-MM-DD.json
├── requirements.txt
└── README.md
```

## License / 许可

MIT
