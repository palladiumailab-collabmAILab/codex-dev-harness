# Architecture-design evaluation tasks

The fixture at `tests/fixtures/architecture-design-evals.json` keeps two representative decisions available for review and future behavioral evaluation:

- `provider-boundary` has concrete external-provider, replaceability, and testability pressure. An adapter or port is justified, while a repository or event bus is not automatically justified.
- `single-health-check` has one local stable behavior and a clear existing convention. The expected decision is no new abstraction; a direct route handler is sufficient.

These are decision fixtures, not proof that a model followed the skill. A future behavioral evaluation should give the task prompt and the relevant repository evidence to an independent agent, then check the decision record for evidence, alternatives, gained property, and proportionate validation. The fixture validator only protects the coverage and structure of the representative cases.

Validate them with:

```powershell
python scripts/validate-architecture-evals.py
```
