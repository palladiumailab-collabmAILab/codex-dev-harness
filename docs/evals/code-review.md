# Code-review evaluation coverage

`tests/fixtures/code-review-evals.json` is a small representative coverage fixture for the `code-review` skill. It keeps the expected review boundary visible without pretending that a deterministic file validator proves model behavior.

The fixture covers:

- a correctness defect that should produce a concrete finding;
- formatter-only changes that should not receive duplicate human findings;
- unsupported speculative concerns that should not become findings;
- a large redesign that is not required by the submitted change;
- a missing regression test that should be reported as a verification gap; and
- a clean change where the reviewer should explicitly report no material finding.

Run the standard-library validator directly with:

```powershell
python scripts/validate-code-review-evals.py
```

The validator checks JSON shape, unique case identifiers, allowed outcomes, and the required focus/outcome pairs. Independent model or human evaluation is still required to establish whether the skill produces those outcomes on real reviews.
