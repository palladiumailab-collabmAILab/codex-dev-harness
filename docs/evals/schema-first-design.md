# Schema-first design evaluation

The fixtures under `tests/fixtures/schema-first/` exercise the minimum canonical model contract:

- `valid-model.json` renders an ER diagram, checkout flow, and screen/entity map from one source;
- `invalid-model.json` contains a missing identifier, invalid cardinality, and dangling entity/screen/flow/API references and must be rejected before implementation.

The validator's `--check-generated` mode renders twice, checks deterministic output, and verifies that each generated view carries `schema_version` and the canonical source SHA-256. It does not claim that a rendered diagram is a complete product specification; domain decisions still require review against the repository's requirements.

Run the checks with:

```powershell
python scripts/validate-schema-first.py --input tests/fixtures/schema-first/valid-model.json --check-generated
python scripts/validate-schema-first.py --input tests/fixtures/schema-first/invalid-model.json --expect-invalid
```
