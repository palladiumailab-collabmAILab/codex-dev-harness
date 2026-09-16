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

## Core contracts

### Execution result

Every long-running or multi-stage workflow SHOULD be able to report:

```json
{
  "status": "complete | partial | failed",
  "inputs": [{"path": "...", "size": 0, "sha256": "..."}],
  "outputs": [{"path": "...", "size": 0, "sha256": "..."}],
  "provenance": {"tool": "...", "runtime": "...", "config": "..."},
  "observations": [],
  "errors": []
}
```

A workflow MUST NOT report `complete` if required evaluation is unresolved or if verified inputs/outputs changed unexpectedly during execution.

### Evaluation result

Evaluation is separate from execution and records raw measurements before an acceptance decision:

```json
{
  "metrics": {"primary": 0.0},
  "failure_types": {},
  "thresholds": {"primary": 0.0},
  "decision": "accept | reject | unresolved",
  "confidence": null,
  "evaluator": "deterministic | model | hybrid"
}
```

Prefer deterministic evaluators where possible. Model judgment is supplementary when the target cannot be fully specified mechanically.

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
- a regression or unresolved evaluation rejects the candidate;
- acceptance reasons and rejected alternatives remain traceable.

## Issue integration

- **#1 token-efficient asset extraction**: bulk discovery is mechanical; semantic/model inspection is limited to shortlisted candidates. Inventory and shortlist become traceable execution artifacts.
- **#2 provenance-aware execution**: supplies the execution and evaluation contracts used by other workflows.
- **#3 AGENTS.md optimization**: keeps always-on instructions minimal; detailed mechanisms live in skills/contracts.
- **#4 schema-first design**: canonical structured data becomes the design SSOT, with derived diagrams/API/types/UI validated against it.
- **#5 self-improvement harness**: training data, optimizer, search strategy, and evaluation are implemented as bounded candidate generation plus hold-out acceptance gates.

## Change gate

Before adopting an agent-generated improvement:

1. record the baseline and immutable best-so-far;
2. state the intended failure mode and bounded change scope;
3. generate one or more candidates, including alternatives that differ structurally when appropriate;
4. run deterministic checks first;
5. evaluate on data not used to propose the change;
6. compare primary metric and failure-type regressions with the baseline;
7. accept only if all required gates pass; otherwise retain the previous best;
8. persist the candidate diff, metrics, evaluator version, and acceptance reason.

Iteration count is not evidence of improvement. Acceptance is determined by reproducible evaluation.
