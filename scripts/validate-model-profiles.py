from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTING_FIXTURE = ROOT / "tests/fixtures/model-routing-evals.json"

REQUIRED = (
    ROOT / "profiles/astra/AGENTS.md",
    ROOT / "profiles/sol-luna/AGENTS.md",
    ROOT / "templates/task-prompts/astra.md",
    ROOT / "templates/task-prompts/sol-luna.md",
)

MODEL_NAME_PATTERN = re.compile(
    r"\b(?:gpt-5\.6(?:-sol|-luna)?|gpt-6(?:[- ]astra)?|sol|luna|astra)\b",
    re.IGNORECASE,
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_routing_fixture(errors: list[str], sol_profile: str) -> None:
    if not ROUTING_FIXTURE.is_file():
        errors.append(
            f"missing model-routing evaluation fixture: {ROUTING_FIXTURE.relative_to(ROOT)}"
        )
        return

    try:
        document = json.loads(read(ROUTING_FIXTURE))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"invalid model-routing evaluation fixture: {error}")
        return

    if not isinstance(document, dict):
        errors.append("model-routing evaluation fixture must be a JSON object")
        return
    if document.get("schema_version") != 1:
        errors.append("model-routing evaluation fixture schema_version must be 1")

    policy = document.get("policy")
    if not isinstance(policy, dict):
        errors.append("model-routing evaluation fixture policy must be an object")
        return

    expected_policy = {
        "default_route": "gpt-5.6-sol / medium",
        "bounded_worker_route": "gpt-5.6-luna / max",
        "escalation_target": "gpt-5.6-sol / medium",
    }
    for key, expected in expected_policy.items():
        if policy.get(key) != expected:
            errors.append(f"model-routing policy {key!r} must be {expected!r}")

    for key in ("profile", "task_prompt"):
        relative_path = policy.get(key)
        if not isinstance(relative_path, str) or not (ROOT / relative_path).is_file():
            errors.append(f"model-routing policy {key!r} must name an existing file")

    for path_key, max_key in (
        ("profile", "max_profile_chars"),
        ("task_prompt", "max_task_prompt_chars"),
    ):
        relative_path = policy.get(path_key)
        max_chars = policy.get(max_key)
        if not isinstance(relative_path, str) or not isinstance(max_chars, int):
            continue
        target = ROOT / relative_path
        if target.is_file() and len(read(target)) > max_chars:
            errors.append(
                f"{relative_path} exceeds routing fixture limit of {max_chars} characters"
            )

    required_markers = (
        "gpt-5.6-sol / medium",
        "gpt-5.6-luna / max",
        "Luna が受け入れ条件を満たさない",
        "追加の routing 分岐は",
    )
    for marker in required_markers:
        if marker not in sol_profile:
            errors.append(f"Sol/Luna profile is missing routing marker: {marker}")

    tasks = document.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("model-routing evaluation fixture tasks must be a non-empty list")
        return

    seen_ids: set[str] = set()
    routes: set[str] = set()
    for index, task in enumerate(tasks):
        prefix = f"model-routing evaluation task[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(f"{prefix} id must be a non-empty string")
        elif task_id in seen_ids:
            errors.append(f"{prefix} id is duplicated: {task_id}")
        else:
            seen_ids.add(task_id)
        if task.get("expected_route") not in {"sol", "luna"}:
            errors.append(f"{prefix} expected_route must be sol or luna")
        else:
            routes.add(task["expected_route"])
        if task.get("required_profile") != "sol-luna":
            errors.append(f"{prefix} must require only the sol-luna profile")
        if task.get("additional_profiles") != []:
            errors.append(f"{prefix} must not add another model profile")
        if not isinstance(task.get("reason"), str) or not task["reason"].strip():
            errors.append(f"{prefix} reason must be a non-empty string")

    if routes != {"sol", "luna"}:
        errors.append("model-routing evaluation fixture must cover both Sol and Luna routes")


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing model-specific harness file: {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors))
        return 1

    root_agents = read(ROOT / "AGENTS.md")
    readme = read(ROOT / "README.md")
    required_routes = {
        "profiles/astra/AGENTS.md": "GPT-6 Astra route is missing from AGENTS.md",
        "profiles/sol-luna/AGENTS.md": "GPT-5.6 Sol/Luna route is missing from AGENTS.md",
    }
    for route, message in required_routes.items():
        if route not in root_agents:
            errors.append(message)
    if "not a prerequisite" not in root_agents:
        errors.append("AGENTS.md must state that Astra is not a prerequisite for Sol/Luna")
    if "not a prerequisite" not in readme:
        errors.append("README.md must state that Astra is not a prerequisite for Sol/Luna")

    astra_files = (
        ROOT / "profiles/astra/AGENTS.md",
        ROOT / "templates/task-prompts/astra.md",
    )
    for path in astra_files:
        text = read(path).lower()
        if "gpt-5.6" in text:
            errors.append(f"{path.relative_to(ROOT)} must not contain GPT-5.6 guidance")

    sol_luna_files = (
        ROOT / "profiles/sol-luna/AGENTS.md",
        ROOT / "templates/task-prompts/sol-luna.md",
    )
    for path in sol_luna_files:
        text = read(path).lower()
        if "gpt-6 astra" in text or "gpt-6-astra" in text:
            errors.append(f"{path.relative_to(ROOT)} must not contain GPT-6 Astra guidance")

    for skill_file in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = read(skill_file)
        match = MODEL_NAME_PATTERN.search(text)
        if match:
            relative = skill_file.relative_to(ROOT)
            errors.append(
                f"{relative} must stay model-neutral; found model name {match.group(0)!r}"
            )

    if "## Done" not in read(ROOT / "profiles/astra/AGENTS.md"):
        errors.append("Astra profile must define Done")
    if "## Done when" not in read(ROOT / "templates/task-prompts/astra.md"):
        errors.append("Astra task prompt must define Done when")

    validate_routing_fixture(errors, read(ROOT / "profiles/sol-luna/AGENTS.md"))

    if errors:
        print("\n".join(errors))
        return 1

    print("Validated Astra and Sol/Luna profile separation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
