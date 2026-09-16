# Harness architecture

The harness separates always-on instructions, conditional task skills, cross-cutting contracts, and mechanical validation. This follows the broad OpenAI Harness Engineering principle of keeping the always-on instruction surface small and promoting stable invariants into repository-local checks.

## Layers

1. **Operating rules — `AGENTS.md`**
   - only invariants and routing that apply to ordinary work.
2. **Task skills — `skills/*/SKILL.md`**
   - detailed procedures loaded only when their trigger conditions apply.
3. **Cross-cutting contracts — this document / schemas**
   - execution provenance, evaluation decisions, design source-of-truth, optimization records.
4. **Mechanical enforcement — `scripts/`, `tests/`, CI**
   - checks stable invariants without relying on model judgment.

## Execution result

A long-running or multi-stage workflow should distinguish `complete`, `partial`, and `failed`, and retain enough input/output identity and provenance to reproduce or audit the result.

Typical provenance may include:

- input/output path, size, digest;
- tool/runtime/configuration;
- model and reasoning effort when applicable;
- harness/dataset version;
- attempt/sample count;
- token, time, and cost metadata when available;
- optional provider session/turn/artifact references.

A workflow must not report `complete` when required evaluation is unresolved or when verified inputs/outputs changed unexpectedly.

## Evaluation result

Evaluation is separate from execution. Record raw measurements before the acceptance decision.

The evaluation contract should capture:

- primary and secondary metrics;
- failure categories;
- predeclared thresholds such as `min_improvement` and `allowed_regression`;
- critical no-regression metrics/failure classes;
- sample count and uncertainty where relevant;
- evaluator type, version, and configuration;
- `accept`, `reject`, or `unresolved` decision.

Use deterministic checks for exact invariants. Use model/hybrid graders when semantic or trajectory quality would be lost by reducing the criterion to an exact check. A small stochastic score delta is not evidence of improvement by itself.

## Canonical design source

For schema-first work, keep one structured source of truth rather than independently editing diagrams, API types, DB schema, and UI models. Derived artifacts should identify the source version used to generate them.

## Optimization record

Self-improvement operates on bounded candidates rather than mutating best-so-far in place. Each candidate should retain:

- parent candidate/baseline identity;
- bounded change scope and summary/diff;
- optimization and hold-out data versions;
- evaluation result and experiment provenance;
- acceptance reason.

Best-so-far changes only after required gates pass. Rejected and unresolved candidates remain traceable when needed for reproducibility.

## Change gate

Before adopting an agent-generated improvement:

1. record baseline and best-so-far;
2. define the target failure mode, change scope, objective, and acceptance thresholds;
3. generate one or more reviewable candidates;
4. run deterministic checks first;
5. evaluate on data not used to propose the change;
6. apply predeclared regression and improvement gates;
7. return `unresolved` when evidence is insufficient;
8. update best-so-far only after all required gates pass;
9. preserve the evidence needed to reproduce the decision.

Iteration count is not evidence of improvement.

## Enforcement

Prose defines semantics; stable invariants should move into versioned schemas, validators, fixtures/tests, and CI. `AGENTS.md` should not duplicate those mechanics.
