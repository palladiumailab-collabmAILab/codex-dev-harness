# Evaluation contract

Execution says what ran. Evaluation says what the observations justify. Keep raw measurements, acceptance thresholds, and the final decision in separate fields.

The reference implementation is in `harness_contracts.evaluation` and uses deterministic rules that are independent of a particular model provider. The versioned record shape is `schemas/evaluation-result.schema.json`; optimization candidates use `schemas/optimization-record.schema.json`.

## Criteria

Represent each user-facing acceptance criterion with a stable `criterion_id`, `required` flag, `status` (`met`, `unmet`, or `unresolved`), and evidence references. A required criterion with no evidence cannot support an accepted result, even when tests or proxy metrics are green.

## Objective and traceability

Every evaluation record carries the requested outcome and the acceptance-criterion IDs that define it. If the objective is materially ambiguous, record that fact and whether clarification was requested; the result remains `unresolved` until the objective is clear. `traceability` maps each required criterion to the implementation/change and the evidence that supports it, so “ran tests” is not a substitute for criterion-level completion.

## Progress and evaluator integrity

`progress` distinguishes a material change from a validation-only iteration and records the consecutive non-progress count plus the required convergence action. Repeating inspection or validation does not reset progress. After a bounded non-progress loop, the record must change strategy, surface a blocker, or ask for criteria.

`evaluator_integrity` records whether the evaluator was changed and whether that change was an explicit specification correction. An evaluator change without a written justification cannot support completion; a passing proxy metric does not authorize weakening a test, fixture, threshold, or acceptance criterion.

## Metrics and thresholds

`MetricObservation` retains the baseline and candidate values, direction (`higher` or `lower`), `min_improvement`, and `allowed_regression`. A metric that regresses beyond its allowance rejects a required or critical evaluation. A required metric that does not reach its declared improvement threshold remains unresolved rather than being called an improvement by repetition or a noisy score delta.

## Decision rules

`EvaluationResult.decide(...)` returns exactly one of:

- `accept`: every required criterion is met with evidence, thresholds pass, and confidence is sufficient;
- `reject`: a required criterion is unmet or a required/critical metric regressed beyond its allowance;
- `unresolved`: a required criterion lacks evidence or is unresolved, a required threshold is not distinguishable, the result is tied, confidence is below the declared minimum, the objective is ambiguous, traceability is incomplete, or the convergence guard has reached its non-progress bound.

Ties and low-confidence results cannot report `accept`. Deterministic checks can use confidence `1.0`; model or stochastic graders should record their evaluator and provenance and use a predeclared threshold.

## Example

```json
{
  "objective": {
    "requested_outcome": "complete the real device evaluation",
    "acceptance_criteria": ["real-device-e2e"],
    "ambiguous": false,
    "clarification_requested": false,
    "assumptions": []
  },
  "decision": "unresolved",
  "criteria": [
    {
      "criterion_id": "real-device-e2e",
      "required": true,
      "status": "unresolved",
      "evidence": [],
      "note": "device was not available"
    }
  ],
  "raw_metrics": [],
  "acceptance": {
    "confidence": null,
    "tied": false,
    "min_confidence": 0.8,
    "reasons": ["required criterion unresolved: real-device-e2e"]
  },
  "evaluator": "manual-gate-v1",
  "progress": {
    "material_change": false,
    "validation_only": true,
    "non_progress_count": 1,
    "convergence_action": "surface-blocker"
  },
  "evaluator_integrity": {
    "evaluator_modified": false,
    "spec_correction": false,
    "justification": null
  },
  "traceability": [
    {
      "criterion_id": "real-device-e2e",
      "changes": ["device acceptance remains unimplemented"],
      "evidence": ["no-device-available"]
    }
  ],
  "provenance": {"harness_revision": "..."}
}
```

The record distinguishes an observed failure from an unresolved measurement. Do not allow a passing lint/build check to override a separate unmet user criterion.

Validate repository fixtures with:

```powershell
python scripts/validate-contracts.py --fixture-root tests/fixtures/contracts/valid
python scripts/validate-contracts.py --fixture-root tests/fixtures/contracts/invalid --expect-invalid
```
