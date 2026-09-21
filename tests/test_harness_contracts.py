from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from harness_contracts import (
    CriterionResult,
    CriterionStatus,
    Decision,
    EvaluationResult,
    MetricObservation,
    Provenance,
    StageOutcome,
    StageResult,
    capture_input,
    create_run_root,
    describe_artifact,
    run_external,
    run_optional_stage,
    verify_artifact,
    verify_input,
)
from harness_contracts.execution import ContractViolation, OptionalCapabilityUnavailable


class HarnessContractTests(unittest.TestCase):
    def test_run_root_is_unique_and_artifact_mutation_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            first = create_run_root(parent)
            second = create_run_root(parent)
            self.assertNotEqual(first, second)

            artifact_path = first / "result.json"
            artifact_path.write_text("before", encoding="utf-8")
            record = describe_artifact(first, "result.json")
            artifact_path.write_text("after", encoding="utf-8")
            with self.assertRaises(ContractViolation):
                verify_artifact(record, first)

    def test_artifact_boundary_rejects_escape_symlink_and_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = create_run_root(Path(temporary))
            (root / "ok.txt").write_text("ok", encoding="utf-8")
            with self.assertRaises(ContractViolation):
                describe_artifact(root, "../outside.txt")

            outside = Path(temporary) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            try:
                (root / "link.txt").symlink_to(outside)
            except (OSError, NotImplementedError):
                pass
            else:
                with self.assertRaises(ContractViolation):
                    describe_artifact(root, "link.txt")

            hardlink = root / "hardlink.txt"
            try:
                os.link(root / "ok.txt", hardlink)
            except OSError:
                self.skipTest("hard links are not available in this environment")
            with self.assertRaises(ContractViolation):
                describe_artifact(root, "hardlink.txt")

    def test_input_snapshot_exposes_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.txt"
            path.write_text("before", encoding="utf-8")
            record = capture_input(path, label="input.txt")
            path.write_text("after", encoding="utf-8")
            checked = verify_input(record, path)
            self.assertFalse(checked.unchanged)
            with self.assertRaises(ContractViolation):
                StageResult(
                    stage="example",
                    outcome=StageOutcome.COMPLETE,
                    inputs=(checked,),
                ).validate()

            path.write_text("before", encoding="utf-8")
            verified = verify_input(record, path)
            StageResult(
                stage="example",
                outcome=StageOutcome.COMPLETE,
                inputs=(verified,),
                provenance=Provenance(tool="test", runtime="python"),
            ).validate()

    def test_external_command_is_bounded_and_captures_diagnostics(self) -> None:
        result = run_external(
            [sys.executable, "-c", "import time; time.sleep(0.2)"],
            timeout_seconds=0.02,
        )
        self.assertTrue(result.timed_out)
        self.assertFalse(result.succeeded)
        self.assertLess(result.duration_seconds, 1.0)

    def test_optional_capability_is_partial_not_global_failure(self) -> None:
        result = run_optional_stage(
            "decoder",
            False,
            lambda: self.fail("optional action must not run"),
            unavailable_reason="decoder dependency is not installed",
        )
        self.assertEqual(result.outcome, StageOutcome.PARTIAL)
        self.assertEqual(result.reason, "optional capability unavailable")

        raised = run_optional_stage(
            "renderer",
            True,
            lambda: (_ for _ in ()).throw(OptionalCapabilityUnavailable("GPU unavailable")),
            unavailable_reason="unused",
        )
        self.assertEqual(raised.outcome, StageOutcome.PARTIAL)

    def test_evaluation_accepts_only_evidenced_non_tied_results(self) -> None:
        result = EvaluationResult.decide(
            criteria=(
                CriterionResult(
                    "artifact-integrity",
                    required=True,
                    status=CriterionStatus.MET,
                    evidence=("run/result.json#sha256",),
                ),
            ),
            metrics=(
                MetricObservation(
                    "latency",
                    baseline=10.0,
                    candidate=8.0,
                    direction="lower",
                    min_improvement=1.0,
                ),
            ),
            confidence=0.95,
            tied=False,
            evaluator="deterministic-test-v1",
        )
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.to_dict()["decision"], "accept")

    def test_evaluation_refuses_missing_evidence_ties_and_low_confidence(self) -> None:
        missing_evidence = EvaluationResult.decide(
            criteria=(CriterionResult("required", True, CriterionStatus.MET),),
            confidence=1.0,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(missing_evidence.decision, Decision.UNRESOLVED)

        tied = EvaluationResult.decide(
            criteria=(CriterionResult("required", True, CriterionStatus.MET, ("test",)),),
            confidence=0.99,
            tied=True,
            evaluator="test",
        )
        self.assertEqual(tied.decision, Decision.UNRESOLVED)

        low_confidence = EvaluationResult.decide(
            criteria=(CriterionResult("required", True, CriterionStatus.MET, ("test",)),),
            confidence=0.5,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(low_confidence.decision, Decision.UNRESOLVED)

    def test_evaluation_rejects_required_regression_and_unmet_criterion(self) -> None:
        result = EvaluationResult.decide(
            criteria=(CriterionResult("user-goal", True, CriterionStatus.UNMET, ("test",)),),
            metrics=(
                MetricObservation(
                    "success-rate",
                    baseline=0.9,
                    candidate=0.8,
                    direction="higher",
                    allowed_regression=0.01,
                    critical=True,
                ),
            ),
            confidence=1.0,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(result.decision, Decision.REJECT)


if __name__ == "__main__":
    unittest.main()
