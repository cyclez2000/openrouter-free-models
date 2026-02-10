#!/usr/bin/env python3
"""
Detect OpenRouter free models, track changes, and persist daily snapshots.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
KNOWN_MODELS_FILE = Path("known_free_models.json")
MODEL_CHANGES_FILE = Path("model_changes.json")
DAILY_SNAPSHOT_DIR = Path("daily_snapshots")
REQUEST_TIMEOUT = 30


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def parse_price(value: Any) -> Optional[Decimal]:
    if value is None:
        return None

    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return Decimal(text)
        except InvalidOperation:
            return None

    return None


def fetch_models() -> List[Dict[str, Any]]:
    headers: Dict[str, str] = {}
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.get(OPENROUTER_API_URL, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    models = data.get("data", [])
    if not isinstance(models, list):
        raise ValueError("Unexpected API response: data is not a list")

    return models


def is_free_model(model: Dict[str, Any]) -> bool:
    pricing = model.get("pricing") or {}
    if not isinstance(pricing, dict) or not pricing:
        return False

    prompt_price = parse_price(pricing.get("prompt"))
    completion_price = parse_price(pricing.get("completion"))

    if prompt_price is None or completion_price is None:
        return False

    if prompt_price != 0 or completion_price != 0:
        return False

    for value in pricing.values():
        parsed = parse_price(value)
        if parsed is None or parsed != 0:
            return False

    return True


def normalize_pricing(pricing: Any) -> Dict[str, Any]:
    if not isinstance(pricing, dict):
        return {}
    return {str(key): pricing[key] for key in sorted(pricing.keys())}


def extract_model_info(model: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": model.get("id"),
        "name": model.get("name"),
        "description": model.get("description", ""),
        "context_length": model.get("context_length"),
        "pricing": normalize_pricing(model.get("pricing")),
        "top_provider": model.get("top_provider", {}),
        "per_request_limits": model.get("per_request_limits"),
        "architecture": model.get("architecture", {}),
    }


def load_known_models() -> Dict[str, Any]:
    if not KNOWN_MODELS_FILE.exists():
        return {"models": {}, "last_updated": None}

    with KNOWN_MODELS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_known_models(models: Dict[str, Dict[str, Any]]) -> None:
    payload = {
        "last_updated": iso_utc(now_utc()),
        "model_count": len(models),
        "models": models,
    }
    with KNOWN_MODELS_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2, sort_keys=True)


def get_free_models() -> Dict[str, Dict[str, Any]]:
    free_models: Dict[str, Dict[str, Any]] = {}

    for model in fetch_models():
        model_id = model.get("id")
        if not model_id:
            continue
        if is_free_model(model):
            free_models[model_id] = extract_model_info(model)

    return {model_id: free_models[model_id] for model_id in sorted(free_models.keys())}


def compare_models(current: Dict[str, Dict[str, Any]], known: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    current_ids = set(current.keys())
    known_ids = set(known.keys())

    new_ids = sorted(current_ids - known_ids)
    removed_ids = sorted(known_ids - current_ids)
    unchanged_ids = sorted(current_ids & known_ids)

    return {
        "new": {model_id: current[model_id] for model_id in new_ids},
        "removed": {model_id: known[model_id] for model_id in removed_ids},
        "unchanged": unchanged_ids,
    }


def format_model_list(models: Dict[str, Dict[str, Any]]) -> str:
    if not models:
        return "None"

    lines: List[str] = []
    for model_id in sorted(models.keys()):
        info = models[model_id]
        name = info.get("name") or model_id
        context_length = info.get("context_length", "unknown")
        pricing = info.get("pricing", {})

        lines.append(f"- **{name}** (`{model_id}`)")
        if isinstance(context_length, int):
            lines.append(f"  - Context length: {context_length:,}")
        else:
            lines.append(f"  - Context length: {context_length}")
        lines.append(
            "  - Pricing: "
            + ", ".join(f"{k}={pricing[k]}" for k in sorted(pricing.keys()))
        )

    return "\n".join(lines)


def create_issue_content(diff: Dict[str, Any], current_models: Dict[str, Dict[str, Any]]) -> str:
    now = now_utc()

    content = [
        "# OpenRouter Free Models Update",
        "",
        f"Detection time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"- Current free models: **{len(current_models)}**",
        f"- Added: **{len(diff['new'])}**",
        f"- Removed: **{len(diff['removed'])}**",
        "",
    ]

    if diff["new"]:
        content.extend(["## Added", format_model_list(diff["new"]), ""])

    if diff["removed"]:
        content.extend(["## Removed", format_model_list(diff["removed"]), ""])

    content.extend(
        [
            "## Full Current Free Model List",
            "<details>",
            "<summary>Expand full list</summary>",
            "",
            format_model_list(current_models),
            "",
            "</details>",
        ]
    )

    return "\n".join(content)


def write_model_changes_file(diff: Dict[str, Any], current_models: Dict[str, Dict[str, Any]]) -> None:
    payload = {
        "checked_at": iso_utc(now_utc()),
        "totals": {
            "current": len(current_models),
            "added": len(diff["new"]),
            "removed": len(diff["removed"]),
        },
        "diff": {
            "new": diff["new"],
            "removed": diff["removed"],
        },
        "current_models": current_models,
    }

    with MODEL_CHANGES_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2, sort_keys=True)


def save_daily_snapshot(diff: Dict[str, Any], current_models: Dict[str, Dict[str, Any]]) -> Tuple[Path, bool]:
    date_utc = now_utc().strftime("%Y-%m-%d")
    DAILY_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_file = DAILY_SNAPSHOT_DIR / f"{date_utc}.json"

    snapshot = {
        "date_utc": date_utc,
        "total_free_models": len(current_models),
        "new_model_ids": sorted(diff["new"].keys()),
        "removed_model_ids": sorted(diff["removed"].keys()),
        "model_ids": sorted(current_models.keys()),
        "models": current_models,
    }

    if snapshot_file.exists():
        with snapshot_file.open("r", encoding="utf-8") as file:
            existing = json.load(file)
        if existing == snapshot:
            return snapshot_file, False

    with snapshot_file.open("w", encoding="utf-8") as file:
        json.dump(snapshot, file, ensure_ascii=False, indent=2, sort_keys=True)

    return snapshot_file, True


def set_github_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return

    with open(github_output, "a", encoding="utf-8") as file:
        if "\n" in value:
            file.write(f"{name}<<EOF\n{value}\nEOF\n")
        else:
            file.write(f"{name}={value}\n")


def main() -> int:
    print("Checking OpenRouter free models...")

    try:
        current_models = get_free_models()
    except Exception as exc:  # pragma: no cover - runtime integration path
        print(f"Failed to fetch model list: {exc}")
        raise

    print(f"Detected free models: {len(current_models)}")

    known_data = load_known_models()
    known_models = known_data.get("models", {})
    if not isinstance(known_models, dict):
        known_models = {}

    diff = compare_models(current_models, known_models)
    new_count = len(diff["new"])
    removed_count = len(diff["removed"])
    has_changes = new_count > 0 or removed_count > 0

    print(f"Changes - added: {new_count}, removed: {removed_count}")

    write_model_changes_file(diff, current_models)
    save_known_models(current_models)
    snapshot_path, snapshot_updated = save_daily_snapshot(diff, current_models)

    set_github_output("has_changes", str(has_changes).lower())
    set_github_output("new_count", str(new_count))
    set_github_output("removed_count", str(removed_count))
    set_github_output("total_count", str(len(current_models)))
    set_github_output("snapshot_path", str(snapshot_path))
    set_github_output("snapshot_updated", str(snapshot_updated).lower())

    if has_changes:
        issue_title = f"OpenRouter free model updates ({now_utc().strftime('%Y-%m-%d')})"
        issue_body = create_issue_content(diff, current_models)
        set_github_output("issue_title", issue_title)
        set_github_output("issue_body", issue_body)

    print(f"Daily snapshot: {snapshot_path} (updated={snapshot_updated})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
