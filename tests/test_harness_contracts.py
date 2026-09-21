from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from harness_contracts import (
    ConvergenceAction,
    CriterionResult,
    CriterionStatus,
    Decision,
    EvaluationResult,
    EvaluatorIntegrity,
    MetricObservation,
    ProgressRecord,
    Provenance,
    StageOutcome,
    StageResult,
    TaskObjective,
    TraceabilityRecord,
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
            objective=TaskObjective("publish the verified artifact", ("artifact-integrity",)),
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
            progress=ProgressRecord(True, False, 0, ConvergenceAction.CONTINUE),
            evaluator_integrity=EvaluatorIntegrity(False, False),
            traceability=(
                TraceabilityRecord(
                    "artifact-integrity",
                    ("artifact generation",),
                    ("run/result.json#sha256",),
                ),
            ),
            confidence=0.95,
            tied=False,
            evaluator="deterministic-test-v1",
        )
        self.assertEqual(result.decision, Decision.ACCEPT)
        record = result.to_dict()
        self.assertEqual(record["decision"], "accept")
        self.assertEqual(record["objective"]["requested_outcome"], "publish the verified artifact")
        self.assertIn("traceability", record)

    def test_evaluation_refuses_missing_evidence_ties_and_low_confidence(self) -> None:
        missing_evidence = EvaluationResult.decide(
            objective=TaskObjective("meet the required criterion", ("required",)),
            criteria=(CriterionResult("required", True, CriterionStatus.MET),),
            progress=ProgressRecord(True, False, 0, ConvergenceAction.CONTINUE),
            evaluator_integrity=EvaluatorIntegrity(False, False),
            traceability=(TraceabilityRecord("required", ("implementation",), ("test",)),),
            confidence=1.0,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(missing_evidence.decision, Decision.UNRESOLVED)

        tied = EvaluationResult.decide(
            objective=TaskObjective("meet the required criterion", ("required",)),
            criteria=(CriterionResult("required", True, CriterionStatus.MET, ("test",)),),
            progress=ProgressRecord(True, False, 0, ConvergenceAction.CONTINUE),
            evaluator_integrity=EvaluatorIntegrity(False, False),
            traceability=(TraceabilityRecord("required", ("implementation",), ("test",)),),
            confidence=0.99,
            tied=True,
            evaluator="test",
        )
        self.assertEqual(tied.decision, Decision.UNRESOLVED)

        low_confidence = EvaluationResult.decide(
            objective=TaskObjective("meet the required criterion", ("required",)),
            criteria=(CriterionResult("required", True, CriterionStatus.MET, ("test",)),),
            progress=ProgressRecord(True, False, 0, ConvergenceAction.CONTINUE),
            evaluator_integrity=EvaluatorIntegrity(False, False),
            traceability=(TraceabilityRecord("required", ("implementation",), ("test",)),),
            confidence=0.5,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(low_confidence.decision, Decision.UNRESOLVED)

    def test_evaluation_rejects_required_regression_and_unmet_criterion(self) -> None:
        result = EvaluationResult.decide(
            objective=TaskObjective("meet the user goal", ("user-goal",)),
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
            progress=ProgressRecord(True, False, 0, ConvergenceAction.CONTINUE),
            evaluator_integrity=EvaluatorIntegrity(False, False),
            traceability=(TraceabilityRecord("user-goal", ("implementation",), ("test",)),),
            confidence=1.0,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(result.decision, Decision.REJECT)

    def test_completion_contract_records_ambiguity_and_non_progress(self) -> None:
        result = EvaluationResult.decide(
            objective=TaskObjective(
                "produce a high-quality result",
                ("user-goal",),
                ambiguous=True,
                clarification_requested=True,
            ),
            criteria=(CriterionResult("user-goal", True, CriterionStatus.MET, ("test",)),),
            progress=ProgressRecord(False, True, 3, ConvergenceAction.ASK_FOR_CRITERIA),
            evaluator_integrity=EvaluatorIntegrity(False, False),
            traceability=(TraceabilityRecord("user-goal", ("no material change",), ("test",)),),
            confidence=1.0,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(result.decision, Decision.UNRESOLVED)
        self.assertIn("objective clarification requested", result.reasons)
        self.assertIn("convergence guard", " ".join(result.reasons))

    def test_unauthorized_evaluator_change_rejects_completion(self) -> None:
        result = EvaluationResult.decide(
            objective=TaskObjective("meet the user goal", ("user-goal",)),
            criteria=(CriterionResult("user-goal", True, CriterionStatus.MET, ("test",)),),
            progress=ProgressRecord(True, False, 0, ConvergenceAction.CONTINUE),
            evaluator_integrity=EvaluatorIntegrity(True, False, "weakened the test"),
            traceability=(TraceabilityRecord("user-goal", ("implementation",), ("test",)),),
            confidence=1.0,
            tied=False,
            evaluator="test",
        )
        self.assertEqual(result.decision, Decision.REJECT)


if __name__ == "__main__":
    unittest.main()
