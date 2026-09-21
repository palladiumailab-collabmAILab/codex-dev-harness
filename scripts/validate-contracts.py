from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CONTRACT_SCHEMAS = {
    "execution": "execution-result.schema.json",
    "evaluation": "evaluation-result.schema.json",
    "optimization": "optimization-record.schema.json",
}
CONVERGENCE_ACTIONS = {"continue", "change-strategy", "surface-blocker", "ask-for-criteria"}


def _is_int(value: object) -> bool:
    return type(value) is int


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _required(record: object, keys: tuple[str, ...], location: str) -> list[str]:
    if not isinstance(record, dict):
        return [f"{location}: expected an object"]
    return [f"{location}.{key}: required field is missing" for key in keys if key not in record]


def _string(value: object, location: str, *, non_empty: bool = True) -> list[str]:
    if not isinstance(value, str) or (non_empty and not value.strip()):
        return [f"{location}: expected a non-empty string"]
    return []


def _boolean(value: object, location: str) -> list[str]:
    return [] if isinstance(value, bool) else [f"{location}: expected a boolean"]


def _sha(value: object, location: str) -> list[str]:
    return (
        []
        if isinstance(value, str) and SHA256_PATTERN.fullmatch(value)
        else [f"{location}: expected a lowercase SHA-256 digest"]
    )


def _relative_path(value: object, location: str) -> list[str]:
    if not isinstance(value, str) or not value:
        return [f"{location}: expected a non-empty relative path"]
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if normalized.startswith("/") or ":" in path.parts[0] or ".." in path.parts:
        return [f"{location}: path must stay relative to its run root"]
    return []


def _non_negative_int(value: object, location: str) -> list[str]:
    return [] if _is_int(value) and value >= 0 else [f"{location}: expected a non-negative integer"]


def _snapshot(record: object, location: str) -> list[str]:
    errors = _required(record, ("path", "size", "sha256"), location)
    if errors or not isinstance(record, dict):
        return errors
    errors.extend(_string(record["path"], f"{location}.path"))
    errors.extend(_non_negative_int(record["size"], f"{location}.size"))
    errors.extend(_sha(record["sha256"], f"{location}.sha256"))
    return errors


def _execution(record: object) -> list[str]:
    location = "execution"
    errors = _required(
        record,
        (
            "schema_version",
            "stage",
            "outcome",
            "inputs",
            "artifacts",
            "provenance",
            "command",
            "diagnostics",
            "reason",
        ),
        location,
    )
    if errors or not isinstance(record, dict):
        return errors
    if record["schema_version"] != SCHEMA_VERSION or not _is_int(record["schema_version"]):
        errors.append(f"{location}.schema_version: expected version {SCHEMA_VERSION}")
    errors.extend(_string(record["stage"], f"{location}.stage"))
    if record["outcome"] not in {"complete", "partial", "failed"}:
        errors.append(f"{location}.outcome: expected complete, partial, or failed")

    inputs = record["inputs"]
    if not isinstance(inputs, list):
        errors.append(f"{location}.inputs: expected an array")
    else:
        for index, input_record in enumerate(inputs):
            item_location = f"{location}.inputs[{index}]"
            item_errors = _required(
                input_record,
                ("path", "before", "after", "unchanged"),
                item_location,
            )
            errors.extend(item_errors)
            if item_errors or not isinstance(input_record, dict):
                continue
            errors.extend(_string(input_record["path"], f"{item_location}.path"))
            errors.extend(_snapshot(input_record["before"], f"{item_location}.before"))
            after = input_record["after"]
            if after is not None:
                errors.extend(_snapshot(after, f"{item_location}.after"))
            errors.extend(_boolean(input_record["unchanged"], f"{item_location}.unchanged"))
            expected_unchanged = after is not None and input_record["before"] == after
            if input_record["unchanged"] != expected_unchanged:
                errors.append(f"{item_location}.unchanged: does not match before/after snapshots")

    artifacts = record["artifacts"]
    if not isinstance(artifacts, list):
        errors.append(f"{location}.artifacts: expected an array")
    else:
        for index, artifact in enumerate(artifacts):
            item_location = f"{location}.artifacts[{index}]"
            item_errors = _required(
                artifact,
                ("path", "size", "sha256", "committed"),
                item_location,
            )
            errors.extend(item_errors)
            if item_errors or not isinstance(artifact, dict):
                continue
            errors.extend(_relative_path(artifact["path"], f"{item_location}.path"))
            errors.extend(_non_negative_int(artifact["size"], f"{item_location}.size"))
            errors.extend(_sha(artifact["sha256"], f"{item_location}.sha256"))
            errors.extend(_boolean(artifact["committed"], f"{item_location}.committed"))

    provenance = record["provenance"]
    if provenance is not None:
        provenance_errors = _required(
            provenance,
            ("tool", "runtime", "configuration", "dependencies"),
            f"{location}.provenance",
        )
        errors.extend(provenance_errors)
        if not provenance_errors and isinstance(provenance, dict):
            errors.extend(_string(provenance["tool"], f"{location}.provenance.tool"))
            errors.extend(_string(provenance["runtime"], f"{location}.provenance.runtime"))
            if not isinstance(provenance["configuration"], dict):
                errors.append(f"{location}.provenance.configuration: expected an object")
            if not isinstance(provenance["dependencies"], dict):
                errors.append(f"{location}.provenance.dependencies: expected an object")
            provider_refs = provenance.get("provider_refs")
            if provider_refs is not None:
                errors.extend(_string_map(provider_refs, f"{location}.provenance.provider_refs"))

    command = record["command"]
    if command is not None:
        command_errors = _required(
            command,
            (
                "argv",
                "returncode",
                "stdout",
                "stderr",
                "timed_out",
                "duration_seconds",
                "succeeded",
            ),
            f"{location}.command",
        )
        errors.extend(command_errors)
        if not command_errors and isinstance(command, dict):
            argv = command["argv"]
            if (
                not isinstance(argv, list)
                or not argv
                or any(not isinstance(value, str) or not value for value in argv)
            ):
                errors.append(f"{location}.command.argv: expected non-empty string arguments")
            if command["returncode"] is not None and not _is_int(command["returncode"]):
                errors.append(f"{location}.command.returncode: expected an integer or null")
            errors.extend(_string(command["stdout"], f"{location}.command.stdout", non_empty=False))
            errors.extend(_string(command["stderr"], f"{location}.command.stderr", non_empty=False))
            errors.extend(_boolean(command["timed_out"], f"{location}.command.timed_out"))
            if not _is_number(command["duration_seconds"]) or command["duration_seconds"] < 0:
                errors.append(
                    f"{location}.command.duration_seconds: expected a non-negative number"
                )
            errors.extend(_boolean(command["succeeded"], f"{location}.command.succeeded"))
            expected_success = not command["timed_out"] and command["returncode"] == 0
            if command["succeeded"] != expected_success:
                errors.append(
                    f"{location}.command.succeeded: does not match timeout and exit status"
                )

    if not isinstance(record["diagnostics"], list) or any(
        not isinstance(value, str) for value in record["diagnostics"]
    ):
        errors.append(f"{location}.diagnostics: expected an array of strings")
    if record["reason"] is not None:
        errors.extend(_string(record["reason"], f"{location}.reason"))

    if record["outcome"] == "complete":
        if provenance is None:
            errors.append(f"{location}: complete result requires provenance")
        if isinstance(inputs, list) and any(
            not item.get("unchanged", False) for item in inputs if isinstance(item, dict)
        ):
            errors.append(f"{location}: complete result requires unchanged verified inputs")
        if (
            command is not None
            and isinstance(command, dict)
            and command.get("succeeded") is not True
        ):
            errors.append(f"{location}: complete result cannot contain a failed command")
        if isinstance(artifacts, list) and any(
            not item.get("committed", False) for item in artifacts if isinstance(item, dict)
        ):
            errors.append(f"{location}: complete result requires committed artifacts")
    return errors


def _string_map(value: object, location: str) -> list[str]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()
    ):
        return [f"{location}: expected a string-to-string object"]
    return []


def _evaluation(record: object) -> list[str]:
    location = "evaluation"
    errors = _required(
        record,
        (
            "schema_version",
            "objective",
            "decision",
            "criteria",
            "raw_metrics",
            "acceptance",
            "evaluator",
            "progress",
            "evaluator_integrity",
            "traceability",
            "provenance",
        ),
        location,
    )
    if errors or not isinstance(record, dict):
        return errors
    if record["schema_version"] != SCHEMA_VERSION or not _is_int(record["schema_version"]):
        errors.append(f"{location}.schema_version: expected version {SCHEMA_VERSION}")
    decision = record["decision"]
    if decision not in {"accept", "reject", "unresolved"}:
        errors.append(f"{location}.decision: expected accept, reject, or unresolved")
    errors.extend(_string(record["evaluator"], f"{location}.evaluator"))
    if not isinstance(record["provenance"], dict):
        errors.append(f"{location}.provenance: expected an object")

    objective = record["objective"]
    objective_criteria: set[str] = set()
    objective_errors = _required(
        objective,
        (
            "requested_outcome",
            "acceptance_criteria",
            "ambiguous",
            "clarification_requested",
            "assumptions",
        ),
        f"{location}.objective",
    )
    errors.extend(objective_errors)
    if not objective_errors and isinstance(objective, dict):
        errors.extend(
            _string(objective["requested_outcome"], f"{location}.objective.requested_outcome")
        )
        acceptance_criteria = objective["acceptance_criteria"]
        if not isinstance(acceptance_criteria, list) or not acceptance_criteria:
            errors.append(f"{location}.objective.acceptance_criteria: expected a non-empty array")
        else:
            for index, criterion_id in enumerate(acceptance_criteria):
                errors.extend(
                    _string(criterion_id, f"{location}.objective.acceptance_criteria[{index}]")
                )
                if isinstance(criterion_id, str):
                    if criterion_id in objective_criteria:
                        errors.append(
                            f"{location}.objective.acceptance_criteria: duplicate criterion ID"
                        )
                    objective_criteria.add(criterion_id)
        errors.extend(_boolean(objective["ambiguous"], f"{location}.objective.ambiguous"))
        errors.extend(
            _boolean(
                objective["clarification_requested"],
                f"{location}.objective.clarification_requested",
            )
        )
        if objective["clarification_requested"] and not objective["ambiguous"]:
            errors.append(
                f"{location}.objective.clarification_requested requires an ambiguous objective"
            )
        assumptions = objective["assumptions"]
        if not isinstance(assumptions, list) or any(
            not isinstance(value, str) or not value.strip() for value in assumptions
        ):
            errors.append(f"{location}.objective.assumptions: expected an array of strings")

    progress = record["progress"]
    progress_errors = _required(
        progress,
        ("material_change", "validation_only", "non_progress_count", "convergence_action"),
        f"{location}.progress",
    )
    errors.extend(progress_errors)
    if not progress_errors and isinstance(progress, dict):
        errors.extend(_boolean(progress["material_change"], f"{location}.progress.material_change"))
        errors.extend(_boolean(progress["validation_only"], f"{location}.progress.validation_only"))
        errors.extend(
            _non_negative_int(
                progress["non_progress_count"], f"{location}.progress.non_progress_count"
            )
        )
        if progress["validation_only"] and progress["material_change"]:
            errors.append(
                f"{location}.progress: validation-only iteration cannot claim material change"
            )
        if progress["convergence_action"] not in CONVERGENCE_ACTIONS:
            errors.append(f"{location}.progress.convergence_action: invalid action")
        if (
            isinstance(objective, dict)
            and objective.get("ambiguous")
            and objective.get("clarification_requested")
            and progress["convergence_action"] != "ask-for-criteria"
        ):
            errors.append(
                f"{location}.progress: ambiguous objective requires ask-for-criteria action"
            )
        if (
            _is_int(progress["non_progress_count"])
            and progress["non_progress_count"] >= 3
            and progress["convergence_action"] == "continue"
        ):
            errors.append(
                f"{location}.progress: repeated non-progress requires a convergence action"
            )

    integrity = record["evaluator_integrity"]
    integrity_errors = _required(
        integrity,
        ("evaluator_modified", "spec_correction", "justification"),
        f"{location}.evaluator_integrity",
    )
    errors.extend(integrity_errors)
    if not integrity_errors and isinstance(integrity, dict):
        errors.extend(
            _boolean(
                integrity["evaluator_modified"],
                f"{location}.evaluator_integrity.evaluator_modified",
            )
        )
        errors.extend(
            _boolean(
                integrity["spec_correction"],
                f"{location}.evaluator_integrity.spec_correction",
            )
        )
        justification = integrity["justification"]
        if justification is not None:
            errors.extend(_string(justification, f"{location}.evaluator_integrity.justification"))
        if (integrity["evaluator_modified"] or integrity["spec_correction"]) and not (
            isinstance(justification, str) and justification.strip()
        ):
            errors.append(
                f"{location}.evaluator_integrity: changes require an explicit justification"
            )

    criteria = record["criteria"]
    required_criteria: list[dict[str, Any]] = []
    if not isinstance(criteria, list):
        errors.append(f"{location}.criteria: expected an array")
    else:
        seen_ids: set[str] = set()
        for index, criterion in enumerate(criteria):
            item_location = f"{location}.criteria[{index}]"
            item_errors = _required(
                criterion,
                ("criterion_id", "required", "status", "evidence", "note"),
                item_location,
            )
            errors.extend(item_errors)
            if item_errors or not isinstance(criterion, dict):
                continue
            errors.extend(_string(criterion["criterion_id"], f"{item_location}.criterion_id"))
            criterion_id = criterion["criterion_id"]
            if criterion_id in seen_ids:
                errors.append(f"{item_location}.criterion_id: duplicate criterion ID")
            seen_ids.add(criterion_id)
            errors.extend(_boolean(criterion["required"], f"{item_location}.required"))
            if criterion["status"] not in {"met", "unmet", "unresolved"}:
                errors.append(f"{item_location}.status: invalid criterion status")
            evidence = criterion["evidence"]
            if not isinstance(evidence, list) or any(
                not isinstance(value, str) or not value.strip() for value in evidence
            ):
                errors.append(f"{item_location}.evidence: expected non-empty string references")
            if criterion["note"] is not None:
                errors.extend(_string(criterion["note"], f"{item_location}.note"))
            if criterion["required"]:
                required_criteria.append(criterion)

    criterion_id_set = (
        {
            criterion["criterion_id"]
            for criterion in criteria
            if isinstance(criterion, dict) and "criterion_id" in criterion
        }
        if isinstance(criteria, list)
        else set()
    )
    traceability = record["traceability"]
    traceability_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(traceability, list):
        errors.append(f"{location}.traceability: expected an array")
    else:
        for index, item in enumerate(traceability):
            item_location = f"{location}.traceability[{index}]"
            item_errors = _required(item, ("criterion_id", "changes", "evidence"), item_location)
            errors.extend(item_errors)
            if item_errors or not isinstance(item, dict):
                continue
            criterion_id = item["criterion_id"]
            errors.extend(_string(criterion_id, f"{item_location}.criterion_id"))
            if criterion_id in traceability_by_id:
                errors.append(f"{item_location}.criterion_id: duplicate criterion ID")
            traceability_by_id[criterion_id] = item
            if criterion_id not in criterion_id_set:
                errors.append(f"{item_location}.criterion_id: unknown criterion ID")
            for field in ("changes", "evidence"):
                values = item[field]
                if not isinstance(values, list) or any(
                    not isinstance(value, str) or not value.strip() for value in values
                ):
                    errors.append(f"{item_location}.{field}: expected non-empty string references")

    for criterion in required_criteria:
        criterion_id = criterion["criterion_id"]
        trace = traceability_by_id.get(criterion_id)
        if trace is None:
            errors.append(
                f"{location}: required criterion lacks change/evidence traceability: {criterion_id}"
            )
        elif not trace["changes"] or not trace["evidence"]:
            errors.append(f"{location}: criterion traceability is incomplete: {criterion_id}")
    required_ids = {criterion["criterion_id"] for criterion in required_criteria}
    for criterion_id in sorted(required_ids - objective_criteria):
        errors.append(f"{location}.objective: required criterion is not listed: {criterion_id}")
    for criterion_id in sorted(objective_criteria - criterion_id_set):
        errors.append(f"{location}.objective: acceptance criterion is unknown: {criterion_id}")

    metrics = record["raw_metrics"]
    if not isinstance(metrics, list):
        errors.append(f"{location}.raw_metrics: expected an array")
        metrics = []
    seen_metrics: set[str] = set()
    for index, metric in enumerate(metrics):
        item_location = f"{location}.raw_metrics[{index}]"
        item_errors = _required(
            metric,
            (
                "name",
                "baseline",
                "candidate",
                "direction",
                "improvement",
                "min_improvement",
                "allowed_regression",
                "required",
                "critical",
            ),
            item_location,
        )
        errors.extend(item_errors)
        if item_errors or not isinstance(metric, dict):
            continue
        errors.extend(_string(metric["name"], f"{item_location}.name"))
        if metric["name"] in seen_metrics:
            errors.append(f"{item_location}.name: duplicate metric name")
        seen_metrics.add(metric["name"])
        for field in (
            "baseline",
            "candidate",
            "improvement",
            "min_improvement",
            "allowed_regression",
        ):
            if not _is_number(metric[field]):
                errors.append(f"{item_location}.{field}: expected a finite number")
        if metric["direction"] not in {"higher", "lower"}:
            errors.append(f"{item_location}.direction: expected higher or lower")
        if _is_number(metric["min_improvement"]) and metric["min_improvement"] < 0:
            errors.append(f"{item_location}.min_improvement: must be non-negative")
        if _is_number(metric["allowed_regression"]) and metric["allowed_regression"] < 0:
            errors.append(f"{item_location}.allowed_regression: must be non-negative")
        errors.extend(_boolean(metric["required"], f"{item_location}.required"))
        errors.extend(_boolean(metric["critical"], f"{item_location}.critical"))
        if (
            _is_number(metric["baseline"])
            and _is_number(metric["candidate"])
            and metric["direction"] in {"higher", "lower"}
        ):
            expected = (
                metric["candidate"] - metric["baseline"]
                if metric["direction"] == "higher"
                else metric["baseline"] - metric["candidate"]
            )
            if not math.isclose(metric["improvement"], expected, rel_tol=1e-9, abs_tol=1e-9):
                errors.append(
                    f"{item_location}.improvement: does not match baseline/candidate/direction"
                )

    acceptance = record["acceptance"]
    acceptance_errors = _required(
        acceptance,
        ("confidence", "tied", "min_confidence", "reasons"),
        f"{location}.acceptance",
    )
    errors.extend(acceptance_errors)
    if not acceptance_errors and isinstance(acceptance, dict):
        confidence = acceptance["confidence"]
        if confidence is not None and (not _is_number(confidence) or not 0 <= confidence <= 1):
            errors.append(f"{location}.acceptance.confidence: must be null or between 0 and 1")
        errors.extend(_boolean(acceptance["tied"], f"{location}.acceptance.tied"))
        if not _is_number(acceptance["min_confidence"]) or not (
            0 <= acceptance["min_confidence"] <= 1
        ):
            errors.append(f"{location}.acceptance.min_confidence: must be between 0 and 1")
        reasons = acceptance["reasons"]
        if not isinstance(reasons, list) or any(
            not isinstance(value, str) or not value.strip() for value in reasons
        ):
            errors.append(f"{location}.acceptance.reasons: expected an array of non-empty strings")

        if decision == "accept":
            if isinstance(objective, dict) and objective.get("ambiguous"):
                errors.append(f"{location}: accept is invalid while objective is ambiguous")
            if isinstance(progress, dict) and progress.get("non_progress_count", 0) >= 3:
                errors.append(f"{location}: accept is invalid after repeated non-progress")
            if (
                isinstance(integrity, dict)
                and integrity.get("evaluator_modified")
                and not integrity.get("spec_correction")
            ):
                errors.append(f"{location}: accept is invalid after unauthorized evaluator changes")
            for criterion in required_criteria:
                if criterion["status"] != "met":
                    errors.append(
                        f"{location}: accept is invalid while required criterion is not met"
                    )
                if not criterion["evidence"]:
                    errors.append(
                        f"{location}: accept requires evidence for {criterion['criterion_id']}"
                    )
            if acceptance["tied"]:
                errors.append(f"{location}: accept is invalid for a tied evaluation")
            if confidence is None or confidence < acceptance["min_confidence"]:
                errors.append(f"{location}: accept requires confidence at the declared threshold")
            for metric in metrics:
                if metric["required"] and (
                    metric["improvement"] < -metric["allowed_regression"]
                    or metric["improvement"] < metric["min_improvement"]
                ):
                    errors.append(f"{location}: accept is invalid for metric {metric['name']}")
            if reasons:
                errors.append(
                    f"{location}.acceptance.reasons: accepted result should have no "
                    "blocking reasons"
                )
        elif not reasons:
            errors.append(
                f"{location}.acceptance.reasons: non-accepted result needs an actionable reason"
            )

    return errors


def _optimization(record: object) -> list[str]:
    location = "optimization"
    errors = _required(
        record,
        (
            "schema_version",
            "candidate_id",
            "parent_candidate_id",
            "baseline_id",
            "change",
            "data",
            "evaluation",
            "acceptance",
            "provenance",
        ),
        location,
    )
    if errors or not isinstance(record, dict):
        return errors
    if record["schema_version"] != SCHEMA_VERSION or not _is_int(record["schema_version"]):
        errors.append(f"{location}.schema_version: expected version {SCHEMA_VERSION}")
    for field in ("candidate_id", "baseline_id"):
        errors.extend(_string(record[field], f"{location}.{field}"))
    if record["parent_candidate_id"] is not None:
        errors.extend(_string(record["parent_candidate_id"], f"{location}.parent_candidate_id"))

    change = record["change"]
    change_errors = _required(change, ("summary", "scope", "diff_ref"), f"{location}.change")
    errors.extend(change_errors)
    if not change_errors and isinstance(change, dict):
        errors.extend(_string(change["summary"], f"{location}.change.summary"))
        if (
            not isinstance(change["scope"], list)
            or not change["scope"]
            or any(not isinstance(value, str) or not value.strip() for value in change["scope"])
        ):
            errors.append(f"{location}.change.scope: expected a non-empty string array")
        if change["diff_ref"] is not None:
            errors.extend(_string(change["diff_ref"], f"{location}.change.diff_ref"))

    data = record["data"]
    data_errors = _required(data, ("optimization_version", "holdout_version"), f"{location}.data")
    errors.extend(data_errors)
    if not data_errors and isinstance(data, dict):
        errors.extend(
            _string(data["optimization_version"], f"{location}.data.optimization_version")
        )
        errors.extend(_string(data["holdout_version"], f"{location}.data.holdout_version"))

    evaluation = record["evaluation"]
    evaluation_errors = _required(evaluation, ("decision", "reference"), f"{location}.evaluation")
    errors.extend(evaluation_errors)
    if not evaluation_errors and isinstance(evaluation, dict):
        if evaluation["decision"] not in {"accept", "reject", "unresolved"}:
            errors.append(f"{location}.evaluation.decision: invalid decision")
        errors.extend(_string(evaluation["reference"], f"{location}.evaluation.reference"))

    acceptance = record["acceptance"]
    acceptance_errors = _required(acceptance, ("decision", "reason"), f"{location}.acceptance")
    errors.extend(acceptance_errors)
    if not acceptance_errors and isinstance(acceptance, dict):
        if acceptance["decision"] not in {"accepted", "rejected", "unresolved"}:
            errors.append(f"{location}.acceptance.decision: invalid candidate decision")
        errors.extend(_string(acceptance["reason"], f"{location}.acceptance.reason"))
        if isinstance(evaluation, dict):
            expected = {
                "accept": "accepted",
                "reject": "rejected",
                "unresolved": "unresolved",
            }.get(evaluation.get("decision"))
            if expected and acceptance["decision"] != expected:
                errors.append(f"{location}.acceptance.decision: does not match evaluation decision")

    provenance = record["provenance"]
    provenance_errors = _required(
        provenance,
        ("harness_version", "evaluator", "experiment_id"),
        f"{location}.provenance",
    )
    errors.extend(provenance_errors)
    if not provenance_errors and isinstance(provenance, dict):
        for field in ("harness_version", "evaluator", "experiment_id"):
            errors.extend(_string(provenance[field], f"{location}.provenance.{field}"))
        provider_refs = provenance.get("provider_refs")
        if provider_refs is not None:
            errors.extend(_string_map(provider_refs, f"{location}.provenance.provider_refs"))
    return errors


def validate_record(record: object, contract_type: str) -> list[str]:
    validators = {
        "execution": _execution,
        "evaluation": _evaluation,
        "optimization": _optimization,
    }
    try:
        validator = validators[contract_type]
    except KeyError as error:
        raise ValueError(f"unknown contract type: {contract_type}") from error
    return validator(record)


def validate_schema_files(schema_root: Path) -> list[str]:
    errors: list[str] = []
    for contract_type, filename in CONTRACT_SCHEMAS.items():
        path = schema_root / filename
        if not path.is_file():
            errors.append(f"{path}: schema file is missing")
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: cannot read JSON schema: {error}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"{path}: schema must be an object")
            continue
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{path}: schema must declare JSON Schema 2020-12")
        if schema.get("type") != "object":
            errors.append(f"{path}: top-level schema type must be object")
        if schema.get("properties", {}).get("schema_version", {}).get("const") != SCHEMA_VERSION:
            errors.append(f"{path}: schema_version const must be {SCHEMA_VERSION}")
        if not schema.get("$id"):
            errors.append(f"{path}: schema must have an $id")
        if contract_type == "optimization" and "evaluation" not in schema.get("properties", {}):
            errors.append(f"{path}: optimization schema must include evaluation")
    return errors


def infer_contract_type(path: Path) -> str:
    name = path.name
    for contract_type in CONTRACT_SCHEMAS:
        if contract_type in name:
            return contract_type
    raise ValueError(f"{path}: filename must contain one of {', '.join(CONTRACT_SCHEMAS)}")


def validate_fixture_directory(
    schema_root: Path,
    fixture_root: Path,
    *,
    expect_invalid: bool = False,
) -> list[str]:
    errors = validate_schema_files(schema_root)
    files = sorted(fixture_root.glob("*.json"))
    if not files:
        errors.append(f"{fixture_root}: no JSON fixtures found")
        return errors
    for path in files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            contract_type = infer_contract_type(path)
            record_errors = validate_record(record, contract_type)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            record_errors = [str(error)]
        if expect_invalid:
            if not record_errors:
                errors.append(f"{path}: expected fixture to be rejected")
        else:
            errors.extend(f"{path}: {error}" for error in record_errors)
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate harness contract records and fixtures.")
    parser.add_argument("--schema-root", type=Path, default=Path("schemas"))
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--expect-invalid", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = validate_fixture_directory(
        args.schema_root,
        args.fixture_root,
        expect_invalid=args.expect_invalid,
    )
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    mode = "invalid" if args.expect_invalid else "valid"
    print(f"Validated {mode} harness contract fixtures in {args.fixture_root}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
