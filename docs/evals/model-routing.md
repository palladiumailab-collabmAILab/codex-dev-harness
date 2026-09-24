# GPT-5.6 routing evaluation

`tests/fixtures/model-routing-evals.json` records representative task classes for the Sol/Luna split:

- bounded implementation and deterministic test execution route to Luna;
- bounded independently checkable exploration may route to Luna;
- protected test-oracle changes route to Sol and are review/PR work, not opportunistic implementation edits;
- cross-cutting debugging and repeated failure analysis route to Sol.

The fixture also records the canonical implementation/test-execution routes, protected-test owner, and `pr_only` protected-test change mode. `scripts/validate-model-profiles.py` checks those semantics, the standalone profile/task-prompt size limits, and that downstream harness templates reference `docs/testing-governance.md`.

These checks are deterministic routing guardrails, not a claim about measured API token usage or model quality. Live latency, cost, and task-quality comparisons remain separate evaluation work.
