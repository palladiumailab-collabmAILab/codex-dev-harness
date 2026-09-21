from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_DECISIONS = {"abstraction-justified", "no-new-abstraction"}
REQUIRED_FIELDS = {
    "id",
    "prompt",
    "expected_decision",
    "architectural_pressure",
    "candidate_designs",
    "rejected_patterns",
    "evidence_to_collect",
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{path}: cannot read valid JSON: {error}"]

    if not isinstance(document, dict):
        return [f"{path}: top-level JSON value must be an object"]

    if document.get("schema_version") != 1:
        errors.append(f"{path}: schema_version must be 1")

    tasks = document.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return [f"{path}: tasks must be a non-empty list"]

    seen_ids: set[str] = set()
    decisions: set[str] = set()
    for index, task in enumerate(tasks):
        prefix = f"{path}: tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - task.keys())
        errors.extend(f"{prefix}: missing {field!r}" for field in missing)

        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(f"{prefix}: id must be a non-empty string")
        elif task_id in seen_ids:
            errors.append(f"{prefix}: duplicate id {task_id!r}")
        else:
            seen_ids.add(task_id)

        if not isinstance(task.get("prompt"), str) or not task["prompt"].strip():
            errors.append(f"{prefix}: prompt must be a non-empty string")

        decision = task.get("expected_decision")
        if decision not in EXPECTED_DECISIONS:
            errors.append(
                f"{prefix}: expected_decision must be one of {sorted(EXPECTED_DECISIONS)}"
            )
        else:
            decisions.add(decision)

        for field in (
            "architectural_pressure",
            "candidate_designs",
            "rejected_patterns",
            "evidence_to_collect",
        ):
            value = task.get(field)
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                errors.append(f"{prefix}: {field} must be a list of non-empty strings")

        pressure = task.get("architectural_pressure")
        candidates = task.get("candidate_designs")
        rejected = task.get("rejected_patterns")
        evidence = task.get("evidence_to_collect")
        if decision == "abstraction-justified":
            if isinstance(pressure, list) and not pressure:
                errors.append(f"{prefix}: justified abstraction needs architectural pressure")
            if isinstance(candidates, list) and not candidates:
                errors.append(f"{prefix}: justified abstraction needs a candidate design")
        if decision == "no-new-abstraction":
            if isinstance(rejected, list) and not rejected:
                errors.append(f"{prefix}: no-abstraction case must reject tempting patterns")
        if isinstance(evidence, list) and not evidence:
            errors.append(f"{prefix}: evaluation task needs evidence to collect")

    if "abstraction-justified" not in decisions:
        errors.append(f"{path}: needs an abstraction-justified representative task")
    if "no-new-abstraction" not in decisions:
        errors.append(f"{path}: needs a no-new-abstraction representative task")
    return errors


def main() -> int:
    default_path = "tests/fixtures/architecture-design-evals.json"
    path = Path(sys.argv[1] if len(sys.argv) > 1 else default_path)
    errors = validate(path)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated architecture-design evaluation tasks: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
