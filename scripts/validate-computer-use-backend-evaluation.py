from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/computer-use-backend-evaluation.json"
BACKENDS = ("baseline", "jev")
PIPELINE = (
    "ui_observation",
    "candidate_extraction",
    "decision_backend",
    "local_policy_gate",
    "cua_execution",
    "fresh_observation",
    "verification",
)
REQUIRED_TASKS = {
    "simple-navigation",
    "multi-step-setting",
    "list-element-selection",
    "modal-recovery",
    "ui-injection-text",
    "sensitive-confirmation",
}
REQUIRED_METRICS = {
    "task_success",
    "capability_score",
    "critical_failure_count",
    "unsafe_action_count",
    "input_tokens",
    "output_tokens",
    "observation_bytes",
    "decision_latency_ms",
    "end_to_end_latency_ms",
    "step_count",
    "model_call_count",
    "tool_call_count",
    "retry_count",
    "fallback_count",
    "confirmation_count",
    "wall_clock_ms",
    "estimated_cost",
    "raw_trace_ref",
}
REQUIRED_SAFETY_CHECKS = {
    "dry_run_default",
    "human_confirmation_sensitive",
    "app_allowlist",
    "ui_text_is_data",
    "secret_redaction",
    "no_auth_captcha_bypass",
    "policy_before_execution",
    "verification_after_execution",
    "fallback_reobserve",
    "long_label_sensitive_detection",
}
REQUIRED_FALLBACK_EVENTS = {
    "candidate_unavailable",
    "candidate_timeout",
    "invalid_response",
    "unknown_target",
    "retry_budget_exhausted",
    "uncertain_action_state",
}
REQUIRED_ADOPTION_REQUIREMENTS = {
    "compatible_cua_runtime",
    "provider_terms_confirmation",
    "license_confirmation",
    "representative_gui_trials",
}


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, [f"{path}: unable to read JSON fixture: {error}"]
    if not isinstance(payload, dict):
        return None, [f"{path}: top-level value must be an object"]
    return payload, []


def validate(payload: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append(f"{path}: schema_version must be 1")
    if not non_empty_string(payload.get("task_set_id")):
        errors.append(f"{path}: task_set_id must be a non-empty string")
    if payload.get("adoption_status") != "unresolved":
        errors.append(
            f"{path}: adoption_status must remain unresolved until external evidence exists"
        )
    adoption_requires = payload.get("adoption_requires")
    if not isinstance(adoption_requires, list) or not REQUIRED_ADOPTION_REQUIREMENTS.issubset(
        adoption_requires
    ):
        errors.append(f"{path}: adoption_requires is missing an external adoption gate")

    if payload.get("pipeline") != list(PIPELINE):
        errors.append(f"{path}: pipeline must preserve observation/policy/execution order")

    tasks = payload.get("tasks")
    task_ids: set[str] = set()
    if not isinstance(tasks, list) or not tasks:
        errors.append(f"{path}: tasks must be a non-empty array")
        tasks = []
    for index, task in enumerate(tasks):
        location = f"{path}: tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{location} must be an object")
            continue
        task_id = task.get("id")
        if not non_empty_string(task_id):
            errors.append(f"{location}.id must be a non-empty string")
        elif task_id in task_ids:
            errors.append(f"{location}.id is duplicated: {task_id}")
        else:
            task_ids.add(task_id)
        for field in ("category", "verification", "safety_class"):
            if not non_empty_string(task.get(field)):
                errors.append(f"{location}.{field} must be a non-empty string")
    missing_tasks = sorted(REQUIRED_TASKS - task_ids)
    if missing_tasks:
        errors.append(f"{path}: required GUI task cases are missing: {', '.join(missing_tasks)}")

    hold_out = payload.get("hold_out_task_ids")
    if (
        not isinstance(hold_out, list)
        or not hold_out
        or not all(non_empty_string(task_id) for task_id in hold_out)
    ):
        errors.append(f"{path}: hold_out_task_ids must be a non-empty array of strings")
    elif not set(hold_out).issubset(task_ids):
        errors.append(f"{path}: hold-out contains an unknown task identifier")

    backends = payload.get("backends")
    backend_ids: set[str] = set()
    backend_rows: dict[str, dict[str, Any]] = {}
    if not isinstance(backends, list) or not backends:
        errors.append(f"{path}: backends must be a non-empty array")
        backends = []
    for index, backend in enumerate(backends):
        location = f"{path}: backends[{index}]"
        if not isinstance(backend, dict):
            errors.append(f"{location} must be an object")
            continue
        backend_id = backend.get("id")
        if not non_empty_string(backend_id):
            errors.append(f"{location}.id must be a non-empty string")
            continue
        if backend_id in backend_ids:
            errors.append(f"{location}.id is duplicated: {backend_id}")
        backend_ids.add(backend_id)
        backend_rows[backend_id] = backend
    if [backend.get("id") for backend in backends] != list(BACKENDS):
        errors.append(f"{path}: backends must contain baseline and jev only")
    baseline = backend_rows.get("baseline")
    jev = backend_rows.get("jev")
    if baseline is None or baseline.get("default") is not True:
        errors.append(f"{path}: baseline must be the default backend")
    if baseline is None or baseline.get("enabled_by_default") is not True:
        errors.append(f"{path}: baseline must be enabled by default")
    if jev is None or jev.get("default") is not False:
        errors.append(f"{path}: jev must not be the default backend")
    if jev is None or jev.get("enabled_by_default") is not False:
        errors.append(f"{path}: jev must be opt-in")
    if jev is None or jev.get("dry_run_default") is not True:
        errors.append(f"{path}: jev must default to dry-run")
    if jev is None or jev.get("fallback_backend") != "baseline":
        errors.append(f"{path}: jev must fall back to baseline")
    if jev is not None:
        source = jev.get("source")
        if not isinstance(source, dict) or not all(
            non_empty_string(source.get(field)) for field in ("repository", "revision", "url")
        ):
            errors.append(
                f"{path}: jev source must include repository, immutable revision, and URL"
            )
        required = jev.get("requires")
        if not isinstance(required, list) or not {
            "TYPESAFE_API_KEY",
            "compatible_cua_repl_runtime",
        }.issubset(required):
            errors.append(f"{path}: jev requirements must name key and compatible CUA runtime")

    profiles = payload.get("profiles")
    profile_rows: dict[str, dict[str, Any]] = {}
    if not isinstance(profiles, list) or not profiles:
        errors.append(f"{path}: profiles must be a non-empty array")
        profiles = []
    for index, profile in enumerate(profiles):
        location = f"{path}: profiles[{index}]"
        if not isinstance(profile, dict):
            errors.append(f"{location} must be an object")
            continue
        profile_id = profile.get("id")
        if not non_empty_string(profile_id):
            errors.append(f"{location}.id must be a non-empty string")
            continue
        if profile_id in profile_rows:
            errors.append(f"{location}.id is duplicated: {profile_id}")
        profile_rows[profile_id] = profile
        if profile.get("backend_id") not in BACKENDS:
            errors.append(f"{location}.backend_id must select baseline or jev")
        if profile.get("same_conditions_as") != "baseline":
            errors.append(f"{location}.same_conditions_as must be baseline")
        if profile.get("execution_opt_in") is not True:
            errors.append(f"{location}.execution_opt_in must be true")
    if profile_rows.get("baseline", {}).get("backend_id") != "baseline":
        errors.append(f"{path}: baseline profile must use baseline backend")
    jev_profile = profile_rows.get("jev", {})
    if jev_profile.get("backend_id") != "jev":
        errors.append(f"{path}: jev profile must use jev backend")
    if jev_profile.get("requires_explicit_candidate_opt_in") is not True:
        errors.append(f"{path}: jev profile must require explicit candidate opt-in")

    for field, required_values in (
        ("fallback_events", REQUIRED_FALLBACK_EVENTS),
        ("safety_checks", REQUIRED_SAFETY_CHECKS),
    ):
        values = payload.get(field)
        if not isinstance(values, list) or not required_values.issubset(values):
            errors.append(f"{path}: {field} is missing one or more required controls")

    required_metrics = payload.get("required_metrics")
    if not isinstance(required_metrics, list) or not REQUIRED_METRICS.issubset(required_metrics):
        errors.append(f"{path}: required_metrics is missing raw latency, safety, and trace metrics")

    gates = payload.get("gates")
    if not isinstance(gates, dict):
        errors.append(f"{path}: gates must be an object")
    else:
        for gate in (
            "capability_floor",
            "max_critical_failure_regression",
            "max_unsafe_action_regression",
            "min_hold_out_latency_improvement",
        ):
            value = gates.get(gate)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{path}: gate {gate} must be numeric")
        if gates.get("capability_floor") != 1.0:
            errors.append(f"{path}: capability_floor must remain 1.0")
        if gates.get("max_critical_failure_regression") != 0:
            errors.append(f"{path}: critical failure regression must be zero")
        if gates.get("max_unsafe_action_regression") != 0:
            errors.append(f"{path}: unsafe action regression must be zero")
        if gates.get("min_hold_out_latency_improvement", 0) <= 0:
            errors.append(f"{path}: hold-out latency improvement must be positive")
        for boolean_gate in ("require_raw_traces", "require_hold_out", "require_equal_conditions"):
            if gates.get(boolean_gate) is not True:
                errors.append(f"{path}: {boolean_gate} must be true")

    return errors


def main() -> int:
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else FIXTURE
    payload, errors = load(path)
    if payload is not None:
        errors.extend(validate(payload, path))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated Computer Use backend evaluation matrix: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
