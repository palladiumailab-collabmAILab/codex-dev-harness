---
name: code-review
description: Review pull requests, diffs, patches, commits, or AI-generated changes when the user explicitly requests review or review-focused regression analysis. Do not use for ordinary implementation work.
---

# Evidence-first code review

This is a review-only skill. Review for evidence that a change is safe and maintainable, not for comment volume. Do not imitate a named reviewer or persona; encode and apply the review principles directly.

Review does not itself authorize code mutation. During review-only work, inspect the change and report findings or verification gaps without editing production code, tests, or unrelated documentation. If the user separately requests implementation of an accepted finding, leave review mode and follow the repository's normal implementation workflow.

## Review priority

Review in this order and spend attention where the risk is highest:

1. specification or acceptance-criteria mismatch;
2. correctness, boundary conditions, error handling, and security-relevant behavior;
3. regression risk and missing or weak verification;
4. responsibility boundaries, coupling, and testability;
5. readability and clarity of intent;
6. local style concerns.

Do not duplicate formatter, linter, compiler, type-checker, or other deterministic diagnostics merely to increase review coverage. Mention them only when their result materially affects acceptance or when the automated gate itself is missing or misconfigured.

## Comment granularity

- One review comment addresses one concrete problem.
- Identify the affected behavior or location, explain the failure mode or maintenance cost, and state the property the fix should preserve.
- Distinguish correctness defects from preferences and optional improvements.
- Do not raise speculative future concerns without a credible execution path, requirement, or other evidence.
- Do not require unrelated refactoring or redesign as part of the current change.
- If a change is too large to review reliably, prefer reducing or splitting the change over producing many low-value micro-comments.
- Avoid repeating the same root cause on many lines; report the root cause once and note its scope.

## Test-driven verification during review

When observable behavior changes and an executable test is practical, prefer a short feedback loop:

1. enumerate the behavior or test scenarios that matter;
2. select one concrete scenario;
3. identify an executable test, run it when it already exists, and confirm that a reported failure has the intended reason;
4. report the smallest behavior-preserving implementation change needed to satisfy the scenario rather than making that change during review;
5. inspect the proportionate regression suite and report any remaining gap.

For a bug fix, identify a reproducing test before the fix when practical. For a refactor with no intended behavior change, inspect the relevant passing characterization/regression tests before restructuring. Do not add tests or refactor during review-only work unless the user has separately authorized implementation.

Do not add tests that merely mirror implementation details. Prefer externally meaningful behavior, invariants, boundaries, and failure cases.

## Architecture boundary

Code review reports concrete structural findings in the submitted change: misplaced responsibility, unnecessary coupling, an abstraction that obscures behavior, or a boundary that makes the stated requirement unsafe or untestable. It does not initiate a broad redesign because a different architecture might be interesting.

Use `architecture-design` when the task asks for a nontrivial new boundary, abstraction, or pattern decision. That skill evaluates direct implementation versus extraction and patterns such as Strategy, Adapter, Factory, Repository, or Event. Code review may point to evidence that such a decision is needed, but does not replace that design analysis or require it without a concrete requirement or execution path.

## AI-generated code

Treat AI-generated code as untrusted until the repository's evidence supports it. Prefer mechanisms that reveal mistakes over increasingly elaborate persona or obedience prompts:

- explicit specifications and acceptance criteria;
- executable tests;
- static types and constraints;
- linters and static analysis;
- small, reviewable change sets;
- CI and repository-specific validators.

If adequate verification cannot be constructed or executed, report the verification gap and its consequence instead of claiming confidence.

## Review result

Report findings in descending impact. For each finding, include only enough evidence to reproduce or understand it. If no material finding remains, state that explicitly and report the verification performed plus any unresolved verification gap.

The methodology rationale and public source references are recorded in `docs/history/code-review-methodology.md`; this runtime skill keeps only operating guidance.
