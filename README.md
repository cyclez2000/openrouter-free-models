# OpenRouter Free Models Tracker / OpenRouter 免费模型追踪器

Track OpenRouter free models every day with GitHub Actions, open issues on changes, and keep a daily snapshot history in the repo.

通过 GitHub Actions 每日检测 OpenRouter 免费模型；当列表变化时自动创建 Issue，并将每日快照记录到仓库中。

## What this project does / 项目功能

- Daily check at `00:00 UTC` (`08:00` China Standard Time).
- Strict free-model detection (all pricing fields must be `0`).
- Auto issue creation when free-model list changes.
- Daily snapshot persisted to `daily_snapshots/YYYY-MM-DD.json`.

- 每天 `UTC 00:00`（北京时间 `08:00`）自动检测。
- 严格免费判定（`pricing` 中所有价格字段必须是 `0`）。
- 免费模型有变动时自动创建 Issue。
- 每日快照保存到 `daily_snapshots/YYYY-MM-DD.json`。

## Accuracy notes / 准确性说明

The old logic used a threshold (`<= 0.0001`) and incorrectly marked many low-price models as free.

旧逻辑使用阈值（`<= 0.0001`），会把大量低价模型误判为免费。

Current logic checks:

当前逻辑：

1. `pricing.prompt == 0`
2. `pricing.completion == 0`
3. Every other pricing field in `pricing` is also `0`

This avoids false positives from very cheap but paid models.

这样可避免“价格很低但非免费”的误判。

## Repository structure / 目录结构

```text
openrouter-free-models/
├── .github/workflows/check-free-models.yml
├── check_models.py
├── known_free_models.json
├── daily_snapshots/
│   └── YYYY-MM-DD.json
├── requirements.txt
└── README.md
```

## Setup / 配置步骤

### 1) Create your repo / 创建你的仓库

Fork this project or push it to your own GitHub repo.

Fork 本项目，或推送到你自己的 GitHub 仓库。

### 2) Optional API key / 可选 API Key

OpenRouter models endpoint is public, but setting a key is recommended for higher limits.

OpenRouter 模型接口可匿名访问，但建议配置 Key 以获得更高请求限额。

- Go to <https://openrouter.ai/keys>
- In GitHub repo: `Settings -> Secrets and variables -> Actions`
- Add secret `OPENROUTER_API_KEY`

### 3) Enable workflow / 启用工作流

- Open repo `Actions`
- Enable `Check OpenRouter Free Models`
- You can click `Run workflow` for a manual run

- 进入仓库 `Actions`
- 启用 `Check OpenRouter Free Models`
- 可手动点击 `Run workflow` 触发一次

## Local run / 本地运行

```bash
pip install -r requirements.txt
python check_models.py
```

PowerShell (optional key):

```powershell
$env:OPENROUTER_API_KEY="your_key"
python check_models.py
```

## Outputs / 输出文件

- `known_free_models.json`: latest baseline of free models.
- `daily_snapshots/YYYY-MM-DD.json`: daily recorded result.
- `model_changes.json`: run-level diff details (local/action temp artifact).

- `known_free_models.json`：当前免费模型基线。
- `daily_snapshots/YYYY-MM-DD.json`：按天记录的检测结果。
- `model_changes.json`：本次运行的差异细节（本地/Action 临时产物）。

## GitHub Action behavior / Action 行为

- Runs daily and on manual dispatch.
- Creates an issue only when free-model set changed.
- Commits `known_free_models.json` and `daily_snapshots/*` when needed.

- 每日和手动触发都会运行。
- 仅在免费模型集合变化时创建 Issue。
- 在需要时提交 `known_free_models.json` 和 `daily_snapshots/*`。

## License / 许可

MIT
