# Harness efficiency evaluation and SoL-Pi adoption boundary

## Decision

The harness does not directly adopt SoL-Pi in this change. The current repository is a model-neutral development harness composed of Markdown skills, Python validators, PowerShell helpers, and CI; it does not expose the Pi extension API or a compatible long-running agent runtime. Installing a Pi extension here would create an unrelated runtime dependency and would not provide evidence for this harness.

This change adds the evaluation protocol and a machine-checked activation matrix so a compatible adapter can be compared later without treating token reduction as success. The external candidate remains `unresolved` until the runtime and benchmark evidence are available.

## External candidate facts

The current SoL-Pi source is a standalone TypeScript extension for Pi. Its package declares Node.js `>=22.19.0`, tests against Pi `0.85.1`, exposes four independent configuration flags, and is released under MIT. It uses Pi's public extension APIs rather than patching or vendoring Pi.

The four mechanisms are:

| Mechanism | Boundary | Required evidence before adoption |
|---|---|---|
| Action Fusion | edit/write plus a follow-up validation action | safe-sequence policy, failure attribution, and no unsafe-action regression |
| ObservationPack | projected tool observations plus local archive/recall | exact range recall, source reconciliation, and fail-open preservation |
| Evidence-Preserving Reducer | long diagnostic tool results plus a reducer model | source/command hashes, quotation verification, privacy policy, and original-result fallback |
| Online Context Compact | plan boundary plus native context compaction/continuation | retained contracts/evidence, continuation completion, and no silent early termination |

The external project explicitly makes the mechanisms opt-in. Its all-enabled installation protocol also requires a pinned Pi release, a validated effective configuration, source checks, and a startup check without extension errors. Those requirements are prerequisites for an adapter evaluation, not evidence that this repository can run the candidate.

## Evaluation matrix

`tests/fixtures/harness-efficiency-evaluation.json` defines the smallest controlled comparison:

- an all-disabled baseline;
- one profile for each mechanism independently enabled; and
- an all-enabled composition evaluated only after the independent profiles.

The fixture is an activation and measurement contract, not a result set. `scripts/validate-efficiency-evaluation.py` rejects missing profiles, mixed feature definitions, missing hold-out/task identifiers, and incomplete metric/gate declarations.

Use a local smoke set first: small bug fix, multi-file change, test-failure diagnosis, long-log analysis, repository-wide search, code review, and documentation update. Keep at least one hold-out task per important behavior class. Use the public EdgeBench subset only when the operator can reproduce its official environment, time budget, stop hooks, hidden judge isolation, and model/provider configuration; a full long-horizon run can consume substantial external compute and API budget.

For every profile, retain raw traces and record task success/capability, critical failure classes, unsafe-action blocks, input/output tokens, observation bytes, model/tool calls, retry count, wall time, and estimated cost when available. Compare candidates against the frozen baseline with a predeclared capability floor, no critical safety regression, and a hold-out efficiency improvement threshold. If any required evidence is unavailable, report `unresolved` and keep the mechanism disabled.

## Security and licensing boundary

Do not put provider credentials, API keys, private logs, or secrets in this repository or in a candidate configuration. Remote diagnostic reduction requires explicit authorization and a data-sensitivity review. Preserve local archives and exact source hashes so a compact receipt never becomes the only evidence.

The external candidate is MIT-licensed, but its dependencies, Pi runtime terms, provider terms, and transmitted data still require separate review before adoption. This repository records the candidate revision and evaluation provenance; it does not copy or vendor the external implementation.

## Sources

- [SoL-Pi repository](https://github.com/NVlabs/SoL-Pi)
- [SoL-Pi package manifest](https://github.com/NVlabs/SoL-Pi/blob/main/package.json)
- [SoL-Pi configuration](https://github.com/NVlabs/SoL-Pi/blob/main/docs/configuration.md)
- [SoL-Pi agent installation protocol](https://github.com/NVlabs/SoL-Pi/blob/main/agents-install.md)
- [SoL-Pi license](https://github.com/NVlabs/SoL-Pi/blob/main/LICENSE)
- [SoL-Pi paper](https://arxiv.org/abs/2609.20519)
- [EdgeBench repository and evaluation harness](https://github.com/ByteDance-Seed/EdgeBench)
