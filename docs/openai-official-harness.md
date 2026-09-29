# OpenAI official harness precedence

This repository treats OpenAI's official Codex harness components as upstream authority.

## Precedence rule

When an OpenAI-maintained harness component conflicts with a local rule, skill, workflow, profile, security procedure, or execution convention, **the OpenAI-maintained component wins**.

Local behavior may extend official behavior only when the extension does not contradict, weaken, shadow, or silently replace the official contract.

Priority:

1. OpenAI official harness / security / Codex behavior
2. Explicit project-specific requirements that do not conflict with (1)
3. Local codex-dev-harness conventions
4. Third-party harness conventions

A detected conflict MUST be resolved in favor of (1), rather than merged by compromise.

## Official upstream set

- https://github.com/openai/codex — Codex CLI / agent runtime and canonical behavior
- https://github.com/openai/codex-security — Codex Security scanning, validation, remediation workflows and TypeScript SDK
- https://github.com/openai/codex-action — official GitHub Action integration for Codex
- https://github.com/openai/codex-universal — official universal Codex environment/container support
- https://github.com/openai/skills — official OpenAI skill examples/definitions
- https://github.com/openai/role-specific-plugins — official role-specific plugin patterns
- https://github.com/openai/redcard — official OpenAI security/red-team tooling relevant to adversarial validation

## Integration policy

Do not vendor or fork official repositories merely to keep a stale local copy. Pin an upstream revision when reproducibility requires it and record provenance.

Before changing an overlapping local mechanism:

1. Check the corresponding official upstream implementation/documentation.
2. Identify semantic conflicts, not only filename conflicts.
3. Replace or subordinate the local mechanism when behavior overlaps.
4. Keep local extensions isolated and explicitly marked.
5. Add regression coverage proving that local extensions do not override official behavior.

For security scanning, `openai/codex-security` is the primary upstream. Existing local review/security skills are supplemental and MUST NOT redefine its findings, verification semantics, or remediation contract.

For GitHub automation, `openai/codex-action` is primary where its supported workflow overlaps local Actions.

For Codex execution/runtime behavior, `openai/codex` and `openai/codex-universal` are primary.

For reusable skills/plugins, prefer official `openai/skills` and `openai/role-specific-plugins`; retain local skills only for uncovered project-specific behavior.

## Review requirement

Any future sync/update that changes an official upstream integration must report:

- upstream repository and revision,
- local files affected,
- conflicts detected,
- which local behavior was removed/subordinated,
- validation performed,
- unresolved incompatibilities.
