from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    ROOT / "profiles/astra/AGENTS.md",
    ROOT / "profiles/sol-luna/AGENTS.md",
    ROOT / "templates/task-prompts/astra.md",
    ROOT / "templates/task-prompts/sol-luna.md",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing model-specific harness file: {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors))
        return 1

    root_agents = read(ROOT / "AGENTS.md")
    required_routes = {
        "profiles/astra/AGENTS.md": "GPT-6 Astra route is missing from AGENTS.md",
        "profiles/sol-luna/AGENTS.md": "GPT-5.6 Sol/Luna route is missing from AGENTS.md",
    }
    for route, message in required_routes.items():
        if route not in root_agents:
            errors.append(message)

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
        text = read(skill_file).lower()
        if "gpt-5.6-sol" in text or "gpt-5.6-luna" in text or "gpt-6 astra" in text:
            relative = skill_file.relative_to(ROOT)
            errors.append(f"{relative} must stay model-neutral; move model routing to profiles/")

    if "## Done" not in read(ROOT / "profiles/astra/AGENTS.md"):
        errors.append("Astra profile must define Done")
    if "## Done when" not in read(ROOT / "templates/task-prompts/astra.md"):
        errors.append("Astra task prompt must define Done when")

    if errors:
        print("\n".join(errors))
        return 1

    print("Validated Astra and Sol/Luna profile separation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
