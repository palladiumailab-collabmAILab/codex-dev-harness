# Harness architecture

This repository separates always-on operating rules from task-specific skills and reusable cross-cutting contracts.

## Layers

1. **Operating rules** — `AGENTS.md`
   - defines invariants, scope control, validation discipline, model/tool use, and safety boundaries.
2. **Task skills** — `skills/*/SKILL.md`
   - loaded only when their trigger conditions apply.
3. **Cross-cutting contracts** — reusable conventions that multiple skills/workflows share.
   - execution result/provenance contract
   - evaluation/acceptance contract
   - canonical design source-of-truth contract
   - candidate/change/evaluation records for optimization
4. **Validation** — `scripts/`, `tests/`, CI
   - validates structure and deterministic invariants before model-based judgment.

The architecture follows the same broad principle described in OpenAI's Harness Engineering guidance: keep the always-on instruction surface small, keep repository knowledge versioned and discoverable, and promote important invariants from prose into mechanical checks when they are stable enough to enforce.

## Core contracts

### Execution result

Every long-running or multi-stage workflow SHOULD be able to report:

```json
{
  "status": "complete | partial | failed",
  "inputs": [{"path": "...", "size": 0, "sha256": "..."}],
  "outputs": [{"path": "...", "size": 0, "sha256": "..."}],
  "provenance": {
    "tool": "...",
    "runtime": "...",
    "config": "...",
    "model": null,
    "reasoning_effort": null,
    "harness_version": "...",
    "dataset_version": null,
    "attempt": null,
    "token_budget": null,
    "token_usage": null,
    "wall_time_ms": null,
    "cost": null,
    "provider_refs": {
      "session_id": null,
      "turn_id": null,
      "artifact_id": null
    }
  },
  "observations": [],
  "errors": []
}
```

Fields that do not apply to a workflow may remain absent/null. Provider-specific references are optional extension points, not a dependency on one runtime.

A workflow MUST NOT report `complete` if required evaluation is unresolved or if verified inputs/outputs changed unexpectedly during execution.

### Evaluation result

Evaluation is separate from execution and records raw measurements before an acceptance decision:

```json
{
  "metrics": {"primary": 0.0},
  "failure_types": {},
  "thresholds": {
    "min_improvement": 0.0,
    "allowed_regression": {},
    "critical_metrics": []
  },
  "samples": 1,
  "decision": "accept | reject | unresolved",
  "confidence": null,
  "evaluator": {
    "type": "deterministic | model | hybrid",
    "version": "...",
    "config": {}
  }
}
```

Evaluator choice follows the property being measured:

- use deterministic checks for exact invariants that can be specified mechanically;
- use model graders for semantic quality or trajectory-level criteria that cannot be reduced to exact checks without losing the intended signal;
- when a model grader materially controls acceptance, record its model/version/configuration and calibration evidence when available;
- do not treat a single small stochastic score delta as evidence of improvement. Use predeclared thresholds and enough samples to distinguish the candidate from noise; otherwise return `unresolved`.

A regression is rejected when it exceeds a predeclared `allowed_regression`, violates a critical no-regression metric/failure class, or otherwise fails an explicit gate. Non-critical trade-offs may be accepted when the declared objective and thresholds permit them.

### Canonical design source

For schema-first work, use one structured source of truth rather than independently edited diagrams, API types, DB schema, and UI models. Derived artifacts should identify the canonical source version used to generate them.

### Optimization record

Self-improvement operates on bounded candidates rather than mutating the current best state in place:

```json
{
  "candidate_id": "...",
  "parent_id": "...",
  "change_scope": ["prompt"],
  "change_summary": "...",
  "training_data_version": "...",
  "validation_data_version": "...",
  "evaluation": {},
  "accepted": false
}
```

Rules:

- training/optimization data and hold-out evaluation data are separated;
- one iteration has an explicit edit budget/scope;
- multiple structurally different candidates may coexist;
- best-so-far is immutable until a candidate passes acceptance gates;
- acceptance uses predeclared thresholds instead of assuming every measured delta is meaningful;
- unresolved evaluation does not replace best-so-far;
- acceptance reasons and rejected alternatives remain traceable.

## Model routing

Keep the default routing deliberately small:

- `gpt-5.6-luna / max`: bounded exploration, candidate discovery, mechanical transformation, independent read-only checks;
- `gpt-5.6-sol / medium`: parent agent, implementation, architecture, debugging, review, final integration and judgment.

If Luna/max fails the acceptance criteria or the task expands beyond bounded exploration, escalate to Sol/medium with compact evidence instead of repeatedly retrying the same failure. Higher Sol reasoning effort or another model is added only when explicitly requested or when repo-local evaluation shows a measurable benefit. Avoid adding an intermediate static routing tier without evidence that it improves the performance/token trade-off.

## Issue integration

- **#1 token-efficient asset extraction**: bulk discovery is mechanical; semantic/model inspection is limited to shortlisted candidates. Inventory and shortlist become traceable execution artifacts.
- **#2 provenance-aware execution**: supplies the execution and evaluation contracts used by other workflows.
- **#3 AGENTS.md optimization**: keeps always-on instructions minimal; detailed mechanisms live in skills/contracts.
- **#4 schema-first design**: canonical structured data becomes the design SSOT, with derived diagrams/API/types/UI validated against it.
- **#5 self-improvement harness**: training data, optimizer, search strategy, and evaluation are represented as bounded candidate generation plus hold-out acceptance gates. It remains open until executable support is sufficient for its acceptance criteria.
- **#7 executable contracts**: turns the documented Execution/Evaluation/Optimization contracts into JSON Schema, validators, fixtures/tests, and CI enforcement.

## Change gate

Before adopting an agent-generated improvement:

1. record the baseline and immutable best-so-far;
2. state the intended failure mode, bounded change scope, primary objective, and acceptance thresholds;
3. generate one or more candidates, including alternatives that differ structurally when appropriate;
4. run deterministic checks first;
5. evaluate on data not used to propose the change;
6. compare primary metrics and failure-type regressions with the baseline using the predeclared gates;
7. if stochastic or model-based evaluation cannot distinguish the candidate from noise, mark the result `unresolved` instead of accepting it;
8. accept only if all required gates pass; otherwise retain the previous best;
9. persist the candidate diff, experiment provenance, metrics, evaluator version/configuration, sample count, and acceptance reason.

Iteration count is not evidence of improvement. Acceptance is determined by reproducible evaluation.

## Enforcement roadmap

This document defines the contracts, but prose is not the final enforcement mechanism. Issue #7 tracks the next step: versioned JSON Schemas, deterministic validators, fixtures/tests, and CI integration. Stable invariants should move into machine-checkable rules while `AGENTS.md` remains a compact map of behavior and routing.
