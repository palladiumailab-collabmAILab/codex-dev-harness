---
name: harness-efficiency-evaluation
description: Compare agent-harness efficiency mechanisms against a baseline with hold-out tasks, capability floors, safety gates, and traceable resource metrics. Use for mechanism adoption decisions, not one-off token tuning.
---

# Evidence-gated harness efficiency evaluation

Use this skill when a candidate changes how an agent executes actions, stores observations, compacts context, or delegates diagnostic reading. The output is an adoption decision supported by comparable traces; a lower token count alone is not an improvement.

This skill evaluates an external mechanism or a repository-local candidate. It does not authorize installing packages, changing the active agent runtime, sending logs to a remote model, or spending API/benchmark budget without an explicit request.

## Freeze the comparison

Record before any candidate run:

- exact baseline and candidate revisions;
- runtime, model/provider, configuration, feature flags, and dependency versions;
- task-set and hold-out identifiers, time budget, retry policy, and resource limits;
- the evaluator, raw trace locations, and the capability floor.

Start with every mechanism disabled. Enable one mechanism at a time, then evaluate the all-enabled composition only after the independent profiles pass. Keep the task order and external conditions fixed across profiles.

## Mechanism-specific checks

- **Action Fusion:** batch only a declared safe sequence. Keep destructive, external-side-effect, authorization, upload, payment, and irreversible actions outside automatic fusion unless the local policy gate and confirmation evidence allow them. Preserve intermediate failure attribution.
- **ObservationPack:** archive the complete observation locally, expose a stable handle and exact range retrieval, and verify that the projected summary can be reconciled with the source. A packing failure must preserve the original observation.
- **Evidence-Preserving Reducer:** record source hash, command identity, retained quotations, reducer configuration, and fallback behavior. Do not send sensitive logs remotely without explicit authorization. A reducer error or unverifiable receipt must return the original result and remain unresolved.
- **Online Context Compact:** compact only at a declared boundary with retained task contracts, progress, evidence, and recovery state. Verify that continuation does not silently terminate the task or lose required instructions.

## Gates

Report raw measurements before aggregation. At minimum collect task success/capability, critical failure and unsafe-action counts, input/output tokens, observation bytes, model/tool calls, retries, wall time, and estimated cost when available.

Adopt only when:

1. the capability floor is met on every required criterion;
2. critical failure classes and unsafe actions do not regress;
3. the candidate improves a predeclared efficiency metric by the required margin on the hold-out set; and
4. traces, evaluator identity, and configuration are sufficient to reproduce the decision.

Return `unresolved` when the runtime, credentials, task environment, sample count, or measurement quality cannot establish those gates. Do not convert an external blocker into a successful adoption claim.

The repository's evaluation matrix and current non-adoption boundary are documented in `docs/efficiency/harness-efficiency-evaluation.md`.
