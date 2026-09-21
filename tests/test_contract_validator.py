from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-contracts.py"
SPEC = importlib.util.spec_from_file_location("validate_contracts", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load {SCRIPT}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


class ContractValidatorTests(unittest.TestCase):
    def test_schema_files_and_positive_fixtures_are_valid(self) -> None:
        schema_errors = VALIDATOR.validate_schema_files(ROOT / "schemas")
        fixture_errors = VALIDATOR.validate_fixture_directory(
            ROOT / "schemas",
            ROOT / "tests" / "fixtures" / "contracts" / "valid",
        )
        self.assertEqual(schema_errors, [])
        self.assertEqual(fixture_errors, [])

    def test_negative_fixtures_are_rejected(self) -> None:
        errors = VALIDATOR.validate_fixture_directory(
            ROOT / "schemas",
            ROOT / "tests" / "fixtures" / "contracts" / "invalid",
            expect_invalid=True,
        )
        self.assertEqual(errors, [])

    def test_required_unmet_criterion_cannot_be_accepted_for_proxy_gain(self) -> None:
        record = json.loads(
            (
                ROOT
                / "tests"
                / "fixtures"
                / "contracts"
                / "invalid"
                / "invalid-evaluation-result.json"
            ).read_text(encoding="utf-8")
        )
        errors = VALIDATOR.validate_record(record, "evaluation")
        self.assertTrue(any("accept is invalid" in error for error in errors))

    def test_unknown_fixture_name_is_actionable(self) -> None:
        with self.assertRaises(ValueError):
            VALIDATOR.infer_contract_type(Path("unknown.json"))


if __name__ == "__main__":
    unittest.main()
