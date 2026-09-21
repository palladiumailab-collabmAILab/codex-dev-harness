from __future__ import annotations

import re
import sys
from pathlib import Path

DEFAULT_SKILLS = (
    "repo-research",
    "github-operations",
    "code-review",
    "self-improvement",
    "long-running-work",
)
INSTALLER_PATTERN = re.compile(r"\$Name\s*=\s*@\((.*?)\)", re.DOTALL)
SINGLE_QUOTED_PATTERN = re.compile(r"'([^']+)'")
README_ITEM_PATTERN = re.compile(r"^-\s+`([^`]+)`\s*$", re.MULTILINE)


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"{path}: unable to read UTF-8 text: {error}")
        return ""


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    installer_path = root / "scripts" / "install-skills.ps1"
    installer = read_text(installer_path, errors)
    installer_match = INSTALLER_PATTERN.search(installer)
    if not installer_match:
        errors.append(f"{installer_path}: default $Name list was not found")
    else:
        installer_names = tuple(SINGLE_QUOTED_PATTERN.findall(installer_match.group(1)))
        if installer_names != DEFAULT_SKILLS:
            errors.append(
                f"{installer_path}: default skills {installer_names!r} do not match "
                f"{DEFAULT_SKILLS!r}"
            )

    readme_path = root / "README.md"
    readme = read_text(readme_path, errors)
    try:
        default_section = readme.split("既定導入:", 1)[1].split("特定skillだけ", 1)[0]
    except IndexError:
        errors.append(f"{readme_path}: the default installation section was not found")
        default_section = ""
    readme_names = tuple(README_ITEM_PATTERN.findall(default_section))
    if readme_names != DEFAULT_SKILLS:
        errors.append(
            f"{readme_path}: documented default skills {readme_names!r} do not match "
            f"{DEFAULT_SKILLS!r}"
        )

    agents_path = root / "AGENTS.md"
    agents = read_text(agents_path, errors)
    for skill_name in DEFAULT_SKILLS:
        skill_path = root / "skills" / skill_name / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"{skill_path}: default skill is missing")
        if f"`{skill_name}`:" not in agents:
            errors.append(f"{agents_path}: routing entry is missing for {skill_name}")
        if f"skills/{skill_name}/" not in readme:
            errors.append(f"{readme_path}: repository reference is missing for {skill_name}")

    code_review = root / "skills" / "code-review" / "SKILL.md"
    code_review_text = read_text(code_review, errors)
    required_markers = (
        "review-only",
        "does not itself authorize code mutation",
        "architecture-design",
    )
    for marker in required_markers:
        if marker not in code_review_text:
            errors.append(f"{code_review}: required boundary marker is missing: {marker}")

    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated default skill registration: {', '.join(DEFAULT_SKILLS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
