from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/harness-efficiency-evaluation.json"
MECHANISMS = (
    "action_fusion",
    "observation_pack",
    "evidence_preserving_reducer",
    "online_context_compact",
)
REQUIRED_METRICS = {
    "task_success",
    "capability_score",
    "critical_failure_count",
    "unsafe_action_count",
    "input_tokens",
    "output_tokens",
    "observation_bytes",
    "model_call_count",
    "tool_call_count",
    "retry_count",
    "wall_clock_ms",
    "estimated_cost",
}
REQUIRED_TASKS = {
    "small-bug-fix",
    "multi-file-change",
    "test-failure-diagnosis",
    "long-log-analysis",
    "repository-search",
    "code-review",
    "documentation-update",
}


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, [f"{path}: unable to read JSON fixture: {error}"]
    if not isinstance(payload, dict):
        return None, [f"{path}: top-level value must be an object"]
    return payload, []


def validate(payload: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append(f"{path}: schema_version must be 1")
    if not non_empty_string(payload.get("task_set_id")):
        errors.append(f"{path}: task_set_id must be a non-empty string")

    tasks = payload.get("tasks")
    task_ids: set[str] = set()
    if not isinstance(tasks, list) or not tasks:
        errors.append(f"{path}: tasks must be a non-empty array")
        tasks = []
    for index, task in enumerate(tasks):
        location = f"{path}: tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{location} must be an object")
            continue
        task_id = task.get("id")
        if not non_empty_string(task_id):
            errors.append(f"{location}.id must be a non-empty string")
        elif task_id in task_ids:
            errors.append(f"{location}.id is duplicated: {task_id}")
        else:
            task_ids.add(task_id)
        for field in ("category", "verification"):
            if not non_empty_string(task.get(field)):
                errors.append(f"{location}.{field} must be a non-empty string")

    missing_tasks = sorted(REQUIRED_TASKS - task_ids)
    if missing_tasks:
        errors.append(f"{path}: required task cases are missing: {', '.join(missing_tasks)}")

    hold_out = payload.get("hold_out_task_ids")
    if (
        not isinstance(hold_out, list)
        or not hold_out
        or not all(non_empty_string(task_id) for task_id in hold_out)
    ):
        errors.append(f"{path}: hold_out_task_ids must be a non-empty array of strings")
    elif not set(hold_out).issubset(task_ids):
        errors.append(f"{path}: hold-out contains an unknown task identifier")

    mechanisms = payload.get("mechanisms")
    if mechanisms != list(MECHANISMS):
        errors.append(f"{path}: mechanisms must list the four independent mechanisms in order")

    profiles = payload.get("profiles")
    profile_ids: set[str] = set()
    feature_sets: dict[str, tuple[str, ...]] = {}
    if not isinstance(profiles, list) or not profiles:
        errors.append(f"{path}: profiles must be a non-empty array")
        profiles = []
    for index, profile in enumerate(profiles):
        location = f"{path}: profiles[{index}]"
        if not isinstance(profile, dict):
            errors.append(f"{location} must be an object")
            continue
        profile_id = profile.get("id")
        if not non_empty_string(profile_id):
            errors.append(f"{location}.id must be a non-empty string")
            continue
        if profile_id in profile_ids:
            errors.append(f"{location}.id is duplicated: {profile_id}")
        profile_ids.add(profile_id)
        features = profile.get("features")
        if not isinstance(features, dict) or set(features) != set(MECHANISMS):
            errors.append(f"{location}.features must contain exactly the four mechanism flags")
            continue
        if not all(isinstance(value, bool) for value in features.values()):
            errors.append(f"{location}.features values must be boolean")
            continue
        feature_sets[profile_id] = tuple(name for name in MECHANISMS if features[name])

    if feature_sets.get("baseline") != ():
        errors.append(f"{path}: baseline must have every mechanism disabled")
    if feature_sets.get("all-enabled") != MECHANISMS:
        errors.append(f"{path}: all-enabled must have every mechanism enabled")
    for mechanism in MECHANISMS:
        profile_id = f"{mechanism.replace('_', '-')}-only"
        if feature_sets.get(profile_id) != (mechanism,):
            errors.append(f"{path}: {profile_id} must enable only {mechanism}")

    required_metrics = payload.get("required_metrics")
    if not isinstance(required_metrics, list) or not REQUIRED_METRICS.issubset(required_metrics):
        errors.append(f"{path}: required_metrics is missing one or more raw resource metrics")

    gates = payload.get("gates")
    if not isinstance(gates, dict):
        errors.append(f"{path}: gates must be an object")
    else:
        numeric_gates = (
            "capability_floor",
            "max_critical_failure_regression",
            "max_unsafe_action_regression",
            "min_hold_out_efficiency_improvement",
        )
        for gate in numeric_gates:
            if not isinstance(gates.get(gate), (int, float)) or isinstance(gates.get(gate), bool):
                errors.append(f"{path}: gate {gate} must be numeric")
        if gates.get("capability_floor") != 1.0:
            errors.append(f"{path}: capability_floor must remain 1.0")
        if gates.get("max_critical_failure_regression") != 0:
            errors.append(f"{path}: critical failure regression must be zero")
        if gates.get("max_unsafe_action_regression") != 0:
            errors.append(f"{path}: unsafe action regression must be zero")
        if gates.get("min_hold_out_efficiency_improvement", 0) <= 0:
            errors.append(f"{path}: hold-out efficiency improvement must be positive")
        for boolean_gate in ("require_raw_traces", "require_hold_out"):
            if gates.get(boolean_gate) is not True:
                errors.append(f"{path}: {boolean_gate} must be true")

    return errors


def main() -> int:
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else FIXTURE
    payload, errors = load(path)
    if payload is not None:
        errors.extend(validate(payload, path))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated harness efficiency evaluation matrix: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
