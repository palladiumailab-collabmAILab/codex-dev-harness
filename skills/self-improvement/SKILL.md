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
- deterministic metrics where possible;
- important failure categories and unacceptable regressions.

If a required criterion cannot be defined, record the evaluation as unresolved instead of claiming improvement.

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
   - run deterministic checks first;
   - evaluate on hold-out tasks not used to generate the candidate;
   - measure both the primary metric and failure-type regressions;
   - use model judges only for criteria that cannot be specified deterministically, and record judge/version/config.
5. **Select**
   - compare every candidate against immutable best-so-far;
   - reject candidates that regress required metrics, violate thresholds, or have unresolved required evaluation;
   - update best-so-far only after all acceptance gates pass.
6. **Record**
   - save candidate parent, bounded diff/change summary, data versions, metrics, failure categories, evaluator identity, and acceptance reason.

## Search strategy

Choose the lightest strategy that preserves alternatives:

- small problem: baseline + 2–3 candidates;
- medium problem: tournament or best-first over a bounded candidate pool;
- expensive evaluation: successive halving/early rejection using cheap deterministic checks before costly model-based evaluation.

Do not interpret more iterations as evidence of progress. Stop when improvement is below the defined threshold, the evaluation budget is exhausted, or no candidate beats best-so-far without regression.

## Anti-patterns

- repeatedly adding one prompt sentence for each failure;
- adding string replacements without testing unseen cases;
- evaluating on examples used to devise the change;
- replacing deterministic checks with an LLM judge;
- overwriting the best version before evaluation;
- optimizing a single aggregate score while silently worsening a critical failure class;
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
  "metrics": {"accuracy": 0.0},
  "failure_types": {},
  "decision": "accept | reject | unresolved",
  "reason": "..."
}
```

For cross-cutting contracts and acceptance rules, follow `docs/harness-architecture.md`.
