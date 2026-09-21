from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum


class Decision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    UNRESOLVED = "unresolved"


class CriterionStatus(StrEnum):
    MET = "met"
    UNMET = "unmet"
    UNRESOLVED = "unresolved"


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
    decision: Decision
    criteria: tuple[CriterionResult, ...]
    metrics: tuple[MetricObservation, ...]
    confidence: float | None
    tied: bool
    min_confidence: float
    evaluator: str
    provenance: Mapping[str, object] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()

    @classmethod
    def decide(
        cls,
        *,
        criteria: Sequence[CriterionResult],
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
        reasons: list[str] = []
        decision = Decision.ACCEPT
        criterion_ids = [criterion.criterion_id for criterion in criterion_results]
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("criterion IDs must be unique")

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
            decision=decision,
            criteria=criterion_results,
            metrics=metric_results,
            confidence=confidence,
            tied=tied,
            min_confidence=min_confidence,
            evaluator=evaluator,
            provenance=dict(provenance or {}),
            reasons=tuple(reasons),
        )

    def to_dict(self) -> dict[str, object]:
        return {
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
            "provenance": dict(self.provenance),
        }
