from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

EVALUATION_SCHEMA_VERSION = 1


class Decision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    UNRESOLVED = "unresolved"


class CriterionStatus(StrEnum):
    MET = "met"
    UNMET = "unmet"
    UNRESOLVED = "unresolved"


class ConvergenceAction(StrEnum):
    CONTINUE = "continue"
    CHANGE_STRATEGY = "change-strategy"
    SURFACE_BLOCKER = "surface-blocker"
    ASK_FOR_CRITERIA = "ask-for-criteria"


@dataclass(frozen=True)
class TaskObjective:
    requested_outcome: str
    acceptance_criteria: tuple[str, ...]
    ambiguous: bool = False
    clarification_requested: bool = False
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.requested_outcome.strip():
            raise ValueError("requested_outcome must not be empty")
        if not self.acceptance_criteria or any(
            not criterion.strip() for criterion in self.acceptance_criteria
        ):
            raise ValueError("acceptance criteria IDs must be a non-empty sequence")
        if len(set(self.acceptance_criteria)) != len(self.acceptance_criteria):
            raise ValueError("acceptance criteria IDs must be unique")
        if any(not assumption.strip() for assumption in self.assumptions):
            raise ValueError("objective assumptions must not be empty")
        if self.clarification_requested and not self.ambiguous:
            raise ValueError("clarification_requested requires an ambiguous objective")

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_outcome": self.requested_outcome,
            "acceptance_criteria": list(self.acceptance_criteria),
            "ambiguous": self.ambiguous,
            "clarification_requested": self.clarification_requested,
            "assumptions": list(self.assumptions),
        }


@dataclass(frozen=True)
class ProgressRecord:
    material_change: bool
    validation_only: bool
    non_progress_count: int
    convergence_action: ConvergenceAction

    def __post_init__(self) -> None:
        if self.validation_only and self.material_change:
            raise ValueError("validation-only progress cannot also claim a material change")
        if self.non_progress_count < 0:
            raise ValueError("non_progress_count must be non-negative")
        if not isinstance(self.convergence_action, ConvergenceAction):
            raise ValueError("convergence_action must be a ConvergenceAction")
        if self.non_progress_count >= 3 and self.convergence_action is ConvergenceAction.CONTINUE:
            raise ValueError("repeated non-progress requires a convergence action")

    def to_dict(self) -> dict[str, object]:
        return {
            "material_change": self.material_change,
            "validation_only": self.validation_only,
            "non_progress_count": self.non_progress_count,
            "convergence_action": self.convergence_action.value,
        }


@dataclass(frozen=True)
class EvaluatorIntegrity:
    evaluator_modified: bool
    spec_correction: bool
    justification: str | None = None

    def __post_init__(self) -> None:
        if (self.evaluator_modified or self.spec_correction) and not (
            self.justification and self.justification.strip()
        ):
            raise ValueError("evaluator or spec changes require an explicit justification")

    def to_dict(self) -> dict[str, object]:
        return {
            "evaluator_modified": self.evaluator_modified,
            "spec_correction": self.spec_correction,
            "justification": self.justification,
        }


@dataclass(frozen=True)
class TraceabilityRecord:
    criterion_id: str
    changes: tuple[str, ...]
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.criterion_id.strip():
            raise ValueError("traceability criterion_id must not be empty")
        if any(not value.strip() for value in self.changes):
            raise ValueError("traceability changes must not be empty")
        if any(not value.strip() for value in self.evidence):
            raise ValueError("traceability evidence must not be empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "criterion_id": self.criterion_id,
            "changes": list(self.changes),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class CriterionResult:
    criterion_id: str
    required: bool
    status: CriterionStatus
    evidence: tuple[str, ...] = ()
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.criterion_id.strip():
            raise ValueError("criterion_id must not be empty")
        if any(not reference.strip() for reference in self.evidence):
            raise ValueError(
                f"criterion evidence references must not be empty: {self.criterion_id}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "criterion_id": self.criterion_id,
            "required": self.required,
            "status": self.status.value,
            "evidence": list(self.evidence),
            "note": self.note,
        }


@dataclass(frozen=True)
class MetricObservation:
    name: str
    baseline: float
    candidate: float
    direction: str = "higher"
    min_improvement: float = 0.0
    allowed_regression: float = 0.0
    required: bool = True
    critical: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name must not be empty")
        if self.direction not in {"higher", "lower"}:
            raise ValueError(f"unsupported metric direction: {self.direction!r}")
        if not math.isfinite(self.baseline) or not math.isfinite(self.candidate):
            raise ValueError(f"metric values must be finite: {self.name}")
        if self.min_improvement < 0 or self.allowed_regression < 0:
            raise ValueError(f"metric thresholds must be non-negative: {self.name}")

    @property
    def improvement(self) -> float:
        if self.direction == "higher":
            return self.candidate - self.baseline
        return self.baseline - self.candidate

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "baseline": self.baseline,
            "candidate": self.candidate,
            "direction": self.direction,
            "improvement": self.improvement,
            "min_improvement": self.min_improvement,
            "allowed_regression": self.allowed_regression,
            "required": self.required,
            "critical": self.critical,
        }


@dataclass(frozen=True)
class EvaluationResult:
    objective: TaskObjective
    decision: Decision
    criteria: tuple[CriterionResult, ...]
    metrics: tuple[MetricObservation, ...]
    confidence: float | None
    tied: bool
    min_confidence: float
    evaluator: str
    progress: ProgressRecord
    evaluator_integrity: EvaluatorIntegrity
    traceability: tuple[TraceabilityRecord, ...]
    provenance: Mapping[str, object] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()

    @classmethod
    def decide(
        cls,
        *,
        objective: TaskObjective,
        criteria: Sequence[CriterionResult],
        progress: ProgressRecord,
        evaluator_integrity: EvaluatorIntegrity,
        traceability: Sequence[TraceabilityRecord],
        metrics: Sequence[MetricObservation] = (),
        confidence: float | None,
        tied: bool,
        evaluator: str,
        min_confidence: float = 0.8,
        provenance: Mapping[str, object] | None = None,
    ) -> EvaluationResult:
        if not evaluator.strip():
            raise ValueError("evaluator must not be empty")
        if not 0 <= min_confidence <= 1:
            raise ValueError("min_confidence must be between 0 and 1")
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

        criterion_results = tuple(criteria)
        metric_results = tuple(metrics)
        traceability_results = tuple(traceability)
        reasons: list[str] = []
        decision = Decision.ACCEPT
        criterion_ids = [criterion.criterion_id for criterion in criterion_results]
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("criterion IDs must be unique")
        traceability_ids = [record.criterion_id for record in traceability_results]
        if len(set(traceability_ids)) != len(traceability_ids):
            raise ValueError("traceability criterion IDs must be unique")
        criterion_id_set = set(criterion_ids)
        if any(
            criterion_id not in criterion_id_set for criterion_id in objective.acceptance_criteria
        ):
            raise ValueError("objective acceptance criteria must reference known criteria")
        if any(record.criterion_id not in criterion_id_set for record in traceability_results):
            raise ValueError("traceability criterion IDs must reference known criteria")

        for criterion in criterion_results:
            if not criterion.required:
                continue
            if criterion.status is CriterionStatus.UNMET:
                reasons.append(f"required criterion unmet: {criterion.criterion_id}")
                decision = Decision.REJECT
            elif criterion.status is CriterionStatus.UNRESOLVED:
                reasons.append(f"required criterion unresolved: {criterion.criterion_id}")
                if decision is Decision.ACCEPT:
                    decision = Decision.UNRESOLVED
            elif not criterion.evidence:
                reasons.append(f"required criterion lacks evidence: {criterion.criterion_id}")
                if decision is Decision.ACCEPT:
                    decision = Decision.UNRESOLVED

        required_criteria = {
            criterion.criterion_id for criterion in criterion_results if criterion.required
        }
        missing_objective_criteria = required_criteria - set(objective.acceptance_criteria)
        if missing_objective_criteria:
            reasons.append(
                "required criteria are missing from the objective: "
                + ", ".join(sorted(missing_objective_criteria))
            )
            if decision is Decision.ACCEPT:
                decision = Decision.UNRESOLVED
        traceability_by_id = {record.criterion_id: record for record in traceability_results}
        missing_traceability = required_criteria - traceability_by_id.keys()
        if missing_traceability:
            reasons.append(
                "required criteria lack change/evidence traceability: "
                + ", ".join(sorted(missing_traceability))
            )
            if decision is Decision.ACCEPT:
                decision = Decision.UNRESOLVED
        for criterion_id in required_criteria & traceability_by_id.keys():
            record = traceability_by_id[criterion_id]
            if not record.changes or not record.evidence:
                reasons.append(f"criterion traceability is incomplete: {criterion_id}")
                if decision is Decision.ACCEPT:
                    decision = Decision.UNRESOLVED

        if objective.ambiguous:
            reason = (
                "objective clarification requested"
                if objective.clarification_requested
                else "objective is materially ambiguous and needs clarification"
            )
            reasons.append(reason)
            if (
                objective.clarification_requested
                and progress.convergence_action is not ConvergenceAction.ASK_FOR_CRITERIA
            ):
                reasons.append(
                    "ambiguous objective requires the ask-for-criteria convergence action"
                )
            if decision is Decision.ACCEPT:
                decision = Decision.UNRESOLVED

        if progress.non_progress_count >= 3:
            reasons.append("convergence guard requires a strategy change or blocker report")
            if decision is Decision.ACCEPT:
                decision = Decision.UNRESOLVED

        if evaluator_integrity.evaluator_modified and not evaluator_integrity.spec_correction:
            reasons.append("evaluator changes are not justified as a specification correction")
            decision = Decision.REJECT

        for metric in metric_results:
            if metric.improvement < -metric.allowed_regression:
                reasons.append(f"metric regressed beyond allowance: {metric.name}")
                if metric.required or metric.critical:
                    decision = Decision.REJECT
            elif metric.required and metric.improvement < metric.min_improvement:
                reasons.append(f"metric did not meet improvement threshold: {metric.name}")
                if decision is Decision.ACCEPT:
                    decision = Decision.UNRESOLVED

        if tied:
            reasons.append("evaluation is tied")
            if decision is Decision.ACCEPT:
                decision = Decision.UNRESOLVED
        if confidence is None or confidence < min_confidence:
            reasons.append("evaluation confidence is below the acceptance threshold")
            if decision is Decision.ACCEPT:
                decision = Decision.UNRESOLVED

        return cls(
            objective=objective,
            decision=decision,
            criteria=criterion_results,
            metrics=metric_results,
            confidence=confidence,
            tied=tied,
            min_confidence=min_confidence,
            evaluator=evaluator,
            progress=progress,
            evaluator_integrity=evaluator_integrity,
            traceability=traceability_results,
            provenance=dict(provenance or {}),
            reasons=tuple(reasons),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": EVALUATION_SCHEMA_VERSION,
            "objective": self.objective.to_dict(),
            "decision": self.decision.value,
            "criteria": [criterion.to_dict() for criterion in self.criteria],
            "raw_metrics": [metric.to_dict() for metric in self.metrics],
            "acceptance": {
                "confidence": self.confidence,
                "tied": self.tied,
                "min_confidence": self.min_confidence,
                "reasons": list(self.reasons),
            },
            "evaluator": self.evaluator,
            "progress": self.progress.to_dict(),
            "evaluator_integrity": self.evaluator_integrity.to_dict(),
            "traceability": [record.to_dict() for record in self.traceability],
            "provenance": dict(self.provenance),
        }
