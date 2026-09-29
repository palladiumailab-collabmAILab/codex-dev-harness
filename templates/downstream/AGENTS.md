# Codex Software Development Harness

Shared rules are managed from `palladiumailab-collabmAILab/codex-dev-harness`; the pinned revision is recorded in `docs/harness-upstream.md`. Keep project-specific rules in `AGENTS.project.md` or explicitly project-specific skills/docs, and read `AGENTS.project.md` when present.

## Authority

- OpenAI-maintained Codex, skills, security, action, and runtime behavior is authoritative.
- Shared local harness rules may extend only non-conflicting gaps.
- Never pin model names, model roles, or a default model in downstream harness instructions; follow the current official Codex behavior.
- If an official rule and a local rule conflict, the official rule wins.

## Common invariants

- Preserve the requested outcome, explicit constraints, and acceptance criteria.
- Before changing durable product/system behavior, read the relevant `docs/specs/` or existing canonical requirement source; surface conflicts instead of silently choosing one side.
- Treat tests, lint, builds, CI, evaluations, and inspections as evidence. Do not rewrite an existing oracle to follow the implementation; use `docs/testing-governance.md` for test changes.
- Keep changes minimal and preserve unrelated work. Do not default to destructive reset/clean/checkout or force push.
- Never expose or commit secrets, private keys, tokens, or unnecessary personal data. Do not deploy, incur charges, delete data, change permissions, or write to external services unless explicitly authorized.
- Read only the nearest instructions and the specifications, code, tests, and configuration needed for the task. Avoid purposeless repository-wide scans and large log dumps.

## Read only when relevant

- OpenAI precedence/integration: `docs/openai-official-harness.md`
- Docker / GitHub Actions / Python-Ruff / shared specification layout: `docs/project-baseline.md`
- task contracts / evaluation / optimization semantics: `docs/harness-architecture.md`
- test failures and oracle changes: `docs/testing-governance.md`
- explicit GitHub remote operations: `skills/github-operations/SKILL.md`
- unfamiliar cross-module repository investigation: `skills/repo-research/SKILL.md`
- evaluated iterative agent/workflow optimization: `skills/self-improvement/SKILL.md`
- harness-efficiency comparison: `skills/harness-efficiency-evaluation/SKILL.md`
- Computer Use decision-backend comparison: `skills/computer-use-backend-evaluation/SKILL.md`
- substantial multi-stage or multi-session handoff: `skills/long-running-work/SKILL.md`

Shared files listed in `docs/harness-upstream.md` remain upstream-managed; change common rules in the canonical harness first.
