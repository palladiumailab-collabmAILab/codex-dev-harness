---
name: self-improvement
description: Evaluate and improve an agent workflow without blindly accumulating prompt patches. Use when iteratively optimizing prompts, tools, parsers, rules, or workflows against measurable outcomes.
---

# Self-improvement harness

Use this skill only when the user asks to improve an existing agent/workflow through repeated evaluation or optimization.

## Goal

Prevent local patch accumulation and regression. Treat improvement as controlled search over bounded candidates with explicit evaluation, not as repeated reflection.

## Required inputs

Before changing the current best state, identify:

- the business/task success criterion;
- the current baseline and best-so-far artifact;
- representative training/optimization examples;
- hold-out validation/test examples not used to propose the candidate;
- exact invariants that can be checked deterministically;
- semantic or trajectory criteria that require a model/hybrid grader;
- important failure categories and critical metrics that must not regress;
- predeclared `min_improvement`, `allowed_regression`, or equivalent acceptance thresholds.

If a required criterion cannot be defined or the available evaluation cannot distinguish the candidate from noise, record the evaluation as unresolved instead of claiming improvement.

## Workflow

1. **Collect traces**
   - retain successful and failed executions with compact inputs, outputs, tool calls, failure category, and relevant provenance;
   - generalize repeated failure patterns rather than copying one example into the prompt verbatim.
2. **Bound the edit**
   - declare `change_scope`: prompt, tool use, parser, rule, workflow, model/config, or another explicit component;
   - keep each candidate reviewable and avoid unrelated refactoring.
3. **Generate candidates**
   - do not produce only a single descendant of the current prompt when the failure suggests an architectural alternative;
   - preserve structurally different candidates when useful.
4. **Evaluate**
   - run deterministic checks first for exact invariants;
   - evaluate on hold-out tasks not used to generate the candidate;
   - measure both the primary metric and failure-type regressions;
   - use model graders for semantic or trajectory-level criteria when exact checks would lose the intended signal;
   - when a model grader materially controls acceptance, record its model/version/configuration and calibration evidence when available;
   - record the relevant experiment context: model, reasoning effort, tools, harness version, dataset version, evaluator identity, attempt/sample count, and token/time/cost metadata when available.
5. **Select**
   - compare every candidate against immutable best-so-far;
   - apply the predeclared `min_improvement`, `allowed_regression`, critical-metric, and other required gates;
   - do not reject or accept solely because of a tiny single-run score delta when the evaluation is stochastic;
   - reject candidates that violate critical gates; mark insufficient evidence as `unresolved`;
   - update best-so-far only after all acceptance gates pass.
6. **Record**
   - save candidate parent, bounded diff/change summary, data versions, experiment provenance, metrics, failure categories, evaluator identity/configuration, sample count, decision, and acceptance reason.

## Search strategy

Choose the lightest strategy that preserves alternatives:

- small problem: baseline + 2–3 candidates;
- medium problem: tournament or best-first over a bounded candidate pool;
- expensive evaluation: successive halving/early rejection using cheap deterministic checks before costly model-based evaluation.

Do not interpret more iterations as evidence of progress. Stop when improvement is below the defined threshold, the evaluation budget is exhausted, or no candidate beats best-so-far under the required gates.

## Model routing

Keep the normal Codex path simple:

- use `gpt-5.6-luna / max` for bounded exploration, candidate discovery, mechanical transformation, and independent read-only checks;
- use `gpt-5.6-sol / medium` for implementation, architecture, difficult debugging, evaluator design, final comparison, and integration;
- if Luna/max fails the acceptance criteria or needs broader judgment, escalate to Sol/medium with compact evidence instead of repeatedly retrying the same failure;
- use higher Sol reasoning effort or another model only when explicitly requested or when repo-local evaluation shows measurable improvement.

## Anti-patterns

- repeatedly adding one prompt sentence for each failure;
- adding string replacements without testing unseen cases;
- evaluating on examples used to devise the change;
- using an LLM judge for an exact invariant that can be checked deterministically;
- treating model grading as deterministic or leaving its model/configuration unrecorded;
- overwriting the best version before evaluation;
- optimizing a single aggregate score while silently worsening a critical failure class;
- accepting/rejecting on a tiny one-run delta without considering evaluation noise;
- reporting `improved` when acceptance criteria are ambiguous or incomplete.

## Minimal record

```json
{
  "candidate_id": "candidate-001",
  "parent_id": "best-000",
  "change_scope": ["prompt"],
  "change_summary": "Generalize amount-field extraction rule",
  "training_data_version": "train-v3",
  "validation_data_version": "holdout-v2",
  "experiment": {
    "model": "gpt-5.6-sol",
    "reasoning_effort": "medium",
    "harness_version": "...",
    "evaluator_version": "...",
    "samples": 3
  },
  "metrics": {"accuracy": 0.0},
  "failure_types": {},
  "thresholds": {
    "min_improvement": 0.0,
    "allowed_regression": {}
  },
  "decision": "accept | reject | unresolved",
  "reason": "..."
}
```

For cross-cutting contracts and acceptance rules, follow `docs/harness-architecture.md`. Executable schemas/validators/CI are tracked in Issue #7.
