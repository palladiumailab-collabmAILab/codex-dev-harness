# Project baseline

This document defines the reusable project-level defaults that sit between the global harness rules and project-specific architecture.

The baseline is intentionally small. It standardizes reproducibility, Python quality gates, and the location of durable specifications without forcing one Web framework, repository layout, database, or service topology.

## Canonical specifications

When a project has durable product or system requirements, keep the current specification set under `docs/specs/`.

Use that directory as the canonical source for **what the system is required to do**. Before changing observable behavior, data contracts, external interfaces, or other requirement-sensitive behavior, read the relevant specification first.

Keep responsibilities separate:

- `docs/specs/`: current requirements and externally meaningful behavior;
- architecture/design documents: how the system is structured to satisfy those requirements;
- issues/tasks/progress files: the current unit of work;
- `docs/history/` or equivalent: superseded decisions, audits, and historical records.

If implementation and the current specification disagree, surface the conflict. Do not silently redefine the specification to match the code or change the code merely to match a stale document without resolving which source is current.

Use `templates/project-specs/README.md` as a starting index when a repository does not already have an equivalent canonical specification location. Existing project conventions may be retained when they already provide a clear single source of truth; do not create two competing specification roots.

## Docker baseline

Executable software projects must provide a Docker-based path that reproduces the environment needed to develop and verify the software.

The baseline requires:

- dependencies needed by the canonical verification path can be installed in the containerized environment;
- required lint, format-check, test, and build steps can be run from that environment when they apply;
- the application or primary executable path can be run in Docker when runtime execution is part of the project;
- host execution may be used as a faster developer path, but host-only success is not the canonical reproducibility guarantee.

Do not require Docker Compose for a single-container project. Use Compose or another orchestration layer only when multiple services need coordinated startup.

Do not infer a microservice architecture from the Docker requirement. A monolith, full-stack framework, worker, CLI, API service, or multi-service application can all satisfy the baseline.

## Python baseline: Ruff

Every repository containing maintained Python code uses Ruff as the standard lint and format gate, including existing repositories.

At minimum, the canonical validation path runs:

```text
ruff check ...
ruff format --check ...
```

Configuration belongs in the target repository, normally in `pyproject.toml`. The target Python version, line length, selected lint families, exclusions, and generated-code handling remain project-local decisions.

When an existing project uses overlapping tools, converge their overlapping responsibilities on Ruff instead of retaining duplicate permanent gates without a reason. Typical overlap includes Flake8, isort, pyupgrade, and Black.

Ruff does not replace orthogonal checks. Keep tools such as pytest, mypy, pyright, security scanners, or domain-specific validators when the project needs them.

Migration of an existing project should be reviewable. Do not combine a broad whole-repository reformat with an unrelated feature change unless that migration is itself the requested task.

## Architecture remains project-specific

This baseline does not require physical separation such as:

```text
frontend/
backend/
```

A separate frontend/backend service layout, a full-stack framework, a monorepo, a single service, or another architecture may all be appropriate.

The harness still expects responsibilities and trust boundaries to be understandable, but their physical layout is a project design decision. Framework, database, transport, deployment topology, state management, and inference placement are not universal defaults unless a separate project rule says otherwise.

## Instruction hierarchy

Apply guidance by scope rather than accumulating every rule into one always-on prompt:

1. root `AGENTS.md`: durable cross-project invariants and routing;
2. scoped `AGENTS.md` / task skills: subsystem- or task-specific operating guidance;
3. `docs/specs/`: current required behavior;
4. architecture/configuration: project-specific implementation choices;
5. tests, linters, validators, and CI: mechanically enforceable constraints.

More specific repository-local instructions may refine the baseline, but should not silently weaken explicit user requirements or safety constraints.
