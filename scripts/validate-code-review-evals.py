from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_OUTCOMES = {"finding", "verification-gap", "no-material-finding"}
REQUIRED_COVERAGE = {
    ("correctness", "finding"),
    ("tooling", "no-material-finding"),
    ("speculative", "no-material-finding"),
    ("redesign", "no-material-finding"),
    ("regression", "verification-gap"),
    ("clean", "no-material-finding"),
}
REQUIRED_FIELDS = {"id", "prompt", "review_focus", "expected_outcome", "must_not"}


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_fixture(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
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

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + [f"{path}: cases must be a non-empty array"]

    seen_ids: set[str] = set()
    coverage: set[tuple[str, str]] = set()
    for index, case in enumerate(cases):
        location = f"{path}: cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{location} must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - case.keys())
        if missing:
            errors.append(f"{location} missing fields: {', '.join(missing)}")
            continue

        case_id = case["id"]
        if not non_empty_string(case_id):
            errors.append(f"{location}.id must be a non-empty string")
        elif case_id in seen_ids:
            errors.append(f"{location}.id is duplicated: {case_id}")
        else:
            seen_ids.add(case_id)

        for field in ("prompt", "review_focus"):
            if not non_empty_string(case[field]):
                errors.append(f"{location}.{field} must be a non-empty string")

        outcome = case["expected_outcome"]
        if outcome not in ALLOWED_OUTCOMES:
            errors.append(
                f"{location}.expected_outcome must be one of: {', '.join(sorted(ALLOWED_OUTCOMES))}"
            )

        must_not = case["must_not"]
        if (
            not isinstance(must_not, list)
            or not must_not
            or not all(non_empty_string(item) for item in must_not)
        ):
            errors.append(f"{location}.must_not must be a non-empty array of strings")

        if non_empty_string(case["review_focus"]) and outcome in ALLOWED_OUTCOMES:
            coverage.add((case["review_focus"], outcome))

    missing_coverage = sorted(REQUIRED_COVERAGE - coverage)
    if missing_coverage:
        formatted = ", ".join(f"{focus}/{outcome}" for focus, outcome in missing_coverage)
        errors.append(f"{path}: required representative coverage is missing: {formatted}")
    return errors


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures/code-review-evals.json")
    payload, errors = load_fixture(path)
    if payload is not None:
        errors.extend(validate(payload, path))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated code-review evaluation coverage: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
