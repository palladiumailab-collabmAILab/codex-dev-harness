---
name: code-review
description: Review code changes and guide test-driven verification using evidence-first priorities. Use when reviewing pull requests, diffs, patches, AI-generated code, or changes that need disciplined regression-focused verification.
---

# Evidence-first code review

Review for evidence that a change is safe and maintainable, not for comment volume. Do not imitate a named reviewer or persona; encode and apply the review principles directly.

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

## Test-driven verification

When observable behavior changes and an executable test is practical, prefer a short feedback loop:

1. enumerate the behavior or test scenarios that matter;
2. select one concrete scenario;
3. write or identify an executable test and confirm that it fails for the intended reason when a failure is expected;
4. make the smallest implementation change that satisfies that scenario and preserves existing tests;
5. refactor only after the behavior is protected;
6. repeat for the next scenario, then run the proportionate regression suite.

For a bug fix, add or identify a reproducing test before the fix when practical. For a refactor with no intended behavior change, establish the relevant passing characterization/regression tests before restructuring.

Do not add tests that merely mirror implementation details. Prefer externally meaningful behavior, invariants, boundaries, and failure cases.

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

## Provenance

These principles are distilled from public material on TDD, automated testing, and AI-era software engineering, including:

- Takuto Wada, *AI時代のTDD / TDD in AI Era 202604 Edition*: https://speakerdeck.com/twada/tdd-in-ai-era-202604-edition
- Takuto Wada, *自動テスト実行結果の目的を整理する / Organizing objectives of automated test results*: https://speakerdeck.com/twada/organizing-objectives-of-automated-test-results
