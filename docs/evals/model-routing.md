# GPT-5.6 routing evaluation

`tests/fixtures/model-routing-evals.json` records three representative task classes:

- ordinary implementation uses the default Sol route;
- bounded, independently checkable exploration may use the Luna worker route;
- cross-cutting debugging stays on Sol and does not repeat an unsuccessful cheap path.

The fixture also bounds the standalone Sol/Luna profile and task prompt size so that adding routing branches requires an explicit review. `scripts/validate-model-profiles.py` checks the policy text, profile separation, route fixture, and these size limits.

These checks are deterministic routing guardrails, not a claim about measured API token usage or model quality. The repository does not contain a model-runner or token accounting path, so live representative-task latency/usage evidence remains an external evaluation item.
