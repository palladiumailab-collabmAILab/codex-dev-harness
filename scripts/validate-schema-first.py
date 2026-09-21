from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CARDINALITIES = {"one", "zero_or_one", "many", "zero_or_many"}
ATTRIBUTE_TYPES = {
    "array",
    "boolean",
    "date",
    "datetime",
    "integer",
    "number",
    "object",
    "string",
    "uuid",
}
METHODS = {"DELETE", "GET", "PATCH", "POST", "PUT"}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPOSITORY_ROOT / "schemas/canonical-model.schema.json"
CARDINALITY_SYMBOLS = {
    "one": "||",
    "zero_or_one": "o|",
    "many": "|{",
    "zero_or_many": "o{",
}


def validate_schema_metadata() -> list[str]:
    if not SCHEMA_PATH.is_file():
        return [f"missing canonical model schema: {SCHEMA_PATH}"]
    try:
        schema = read_json(SCHEMA_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"cannot read canonical model schema: {error}"]
    if not isinstance(schema, dict):
        return ["canonical model schema must be a JSON object"]
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("canonical model schema must use JSON Schema draft 2020-12")
    if not str(schema.get("$id", "")).endswith("/schemas/canonical-model.schema.json"):
        errors.append("canonical model schema $id must identify the versioned repository schema")
    if schema.get("properties", {}).get("schema_version", {}).get("const") != 1:
        errors.append("canonical model schema must pin schema_version to 1")
    return errors


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def object_list(value: Any, label: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be an object")
        else:
            result.append(item)
    return result


def id_map(items: list[dict[str, Any]], label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        item_id = item.get("id")
        if not isinstance(item_id, str) or not ID_PATTERN.fullmatch(item_id):
            errors.append(f"{label}[{index}].id must be a lowercase stable ID")
        elif item_id in result:
            errors.append(f"{label} has duplicate id {item_id!r}")
        else:
            result[item_id] = item
    return result


def require_named(item: dict[str, Any], label: str, errors: list[str]) -> None:
    if not isinstance(item.get("name"), str) or not item["name"].strip():
        errors.append(f"{label}.name must be a non-empty string")


def reference_list(
    value: Any,
    label: str,
    allowed: set[str],
    errors: list[str],
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    references: list[str] = []
    for index, reference in enumerate(value):
        if not isinstance(reference, str) or reference not in allowed:
            errors.append(f"{label}[{index}] references an unknown ID: {reference!r}")
        else:
            references.append(reference)
    return references


def validate_model(model: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict):
        return ["model must be a JSON object"]

    required = (
        "schema_version",
        "model_id",
        "domain",
        "entities",
        "relations",
        "events",
        "flows",
        "screens",
        "api",
    )
    for key in required:
        if key not in model:
            errors.append(f"missing required top-level field: {key}")
    if model.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(model.get("model_id"), str) or not ID_PATTERN.fullmatch(model["model_id"]):
        errors.append("model_id must be a lowercase stable ID")

    domain = model.get("domain")
    if not isinstance(domain, dict):
        errors.append("domain must be an object")
    else:
        if not isinstance(domain.get("id"), str) or not ID_PATTERN.fullmatch(domain["id"]):
            errors.append("domain.id must be a lowercase stable ID")
        require_named(domain, "domain", errors)

    enums = object_list(model.get("enums", []), "enums", errors)
    enum_map = id_map(enums, "enums", errors)
    enum_values: dict[str, set[str]] = {}
    for enum_id, enum in enum_map.items():
        require_named(enum, f"enums[{enum_id}]", errors)
        values = enum.get("values")
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
        ):
            errors.append(f"enums[{enum_id}].values must be non-empty strings")
        else:
            if len(values) != len(set(values)):
                errors.append(f"enums[{enum_id}].values must be unique")
            enum_values[enum_id] = set(values)

    entities = object_list(model.get("entities"), "entities", errors)
    entity_map = id_map(entities, "entities", errors)
    attribute_maps: dict[str, dict[str, dict[str, Any]]] = {}
    for entity_id, entity in entity_map.items():
        require_named(entity, f"entities[{entity_id}]", errors)
        attributes = object_list(
            entity.get("attributes"), f"entities[{entity_id}].attributes", errors
        )
        attributes_by_id = id_map(attributes, f"entities[{entity_id}].attributes", errors)
        attribute_maps[entity_id] = attributes_by_id
        for attribute_id, attribute in attributes_by_id.items():
            label = f"entities[{entity_id}].attributes[{attribute_id}]"
            if attribute.get("type") not in ATTRIBUTE_TYPES:
                errors.append(f"{label}.type is unsupported: {attribute.get('type')!r}")
            if not isinstance(attribute.get("required"), bool):
                errors.append(f"{label}.required must be boolean")
            if not isinstance(attribute.get("nullable"), bool):
                errors.append(f"{label}.nullable must be boolean")
            if attribute.get("enum_id") not in (None, *enum_map):
                errors.append(f"{label}.enum_id references an unknown enum")
            constraints = attribute.get("constraints", [])
            if not isinstance(constraints, list) or any(
                not isinstance(constraint, dict) or not isinstance(constraint.get("kind"), str)
                for constraint in constraints
            ):
                errors.append(f"{label}.constraints must contain objects with kind")

        identifiers = object_list(
            entity.get("identifiers"), f"entities[{entity_id}].identifiers", errors
        )
        primary_found = False
        for identifier_index, identifier in enumerate(identifiers):
            label = f"entities[{entity_id}].identifiers[{identifier_index}]"
            if not isinstance(identifier.get("kind"), str):
                errors.append(f"{label}.kind must be a string")
            identifier_attributes = reference_list(
                identifier.get("attribute_ids"),
                f"{label}.attribute_ids",
                set(attributes_by_id),
                errors,
            )
            if identifier.get("kind") == "primary":
                primary_found = True
                for attribute_id in identifier_attributes:
                    attribute = attributes_by_id[attribute_id]
                    if (
                        attribute.get("required") is not True
                        or attribute.get("nullable") is not False
                    ):
                        errors.append(
                            f"{label} primary attributes must be required and non-nullable"
                        )
        if not primary_found:
            errors.append(f"entities[{entity_id}] must define a primary identifier")

        for attribute_id, attribute in attributes_by_id.items():
            if attribute.get("identifier") and (
                attribute.get("required") is not True or attribute.get("nullable") is not False
            ):
                errors.append(
                    f"entities[{entity_id}].attributes[{attribute_id}] identifier must be "
                    "required and non-nullable"
                )

    relations = object_list(model.get("relations"), "relations", errors)
    relation_map = id_map(relations, "relations", errors)
    for relation_id, relation in relation_map.items():
        label = f"relations[{relation_id}]"
        require_named({"name": relation.get("label")}, label, errors)
        for endpoint_name in ("from", "to"):
            endpoint = relation.get(endpoint_name)
            if not isinstance(endpoint, dict):
                errors.append(f"{label}.{endpoint_name} must be an object")
                continue
            if endpoint.get("entity") not in entity_map:
                errors.append(f"{label}.{endpoint_name}.entity is unknown")
            if endpoint.get("cardinality") not in CARDINALITIES:
                errors.append(f"{label}.{endpoint_name}.cardinality is invalid")

    events = object_list(model.get("events"), "events", errors)
    event_map = id_map(events, "events", errors)
    for event_id, event in event_map.items():
        require_named(event, f"events[{event_id}]", errors)
        reference_list(
            event.get("entity_ids"),
            f"events[{event_id}].entity_ids",
            set(entity_map),
            errors,
        )

    screens = object_list(model.get("screens"), "screens", errors)
    screen_map = id_map(screens, "screens", errors)
    for screen_id, screen in screen_map.items():
        require_named(screen, f"screens[{screen_id}]", errors)
        reference_list(
            screen.get("entity_ids"),
            f"screens[{screen_id}].entity_ids",
            set(entity_map),
            errors,
        )
        reference_list(
            screen.get("event_ids"),
            f"screens[{screen_id}].event_ids",
            set(event_map),
            errors,
        )

    flows = object_list(model.get("flows"), "flows", errors)
    flow_map = id_map(flows, "flows", errors)
    for flow_id, flow in flow_map.items():
        require_named(flow, f"flows[{flow_id}]", errors)
        steps = object_list(flow.get("steps"), f"flows[{flow_id}].steps", errors)
        step_map = id_map(steps, f"flows[{flow_id}].steps", errors)
        for step_id, step in step_map.items():
            label = f"flows[{flow_id}].steps[{step_id}]"
            require_named({"name": step.get("label")}, label, errors)
            if step.get("event_id") is not None and step.get("event_id") not in event_map:
                errors.append(f"{label}.event_id is unknown")
            if step.get("screen_id") is not None and step.get("screen_id") not in screen_map:
                errors.append(f"{label}.screen_id is unknown")
            if step.get("entity_ids") is not None:
                reference_list(
                    step.get("entity_ids"), f"{label}.entity_ids", set(entity_map), errors
                )
            reference_list(step.get("next"), f"{label}.next", set(step_map), errors)

    api_operations = object_list(model.get("api"), "api", errors)
    api_map = id_map(api_operations, "api", errors)
    for operation_id, operation in api_map.items():
        label = f"api[{operation_id}]"
        require_named(operation, label, errors)
        if operation.get("method") not in METHODS:
            errors.append(f"{label}.method is invalid")
        if not isinstance(operation.get("path"), str) or not operation["path"].startswith("/"):
            errors.append(f"{label}.path must start with /")
        for mapping_name in ("input", "output"):
            mapping = operation.get(mapping_name)
            mapping_label = f"{label}.{mapping_name}"
            if not isinstance(mapping, dict):
                errors.append(f"{mapping_label} must be an object")
                continue
            entity_id = mapping.get("entity")
            if entity_id not in entity_map:
                errors.append(f"{mapping_label}.entity is unknown")
                continue
            reference_list(
                mapping.get("attribute_ids"),
                f"{mapping_label}.attribute_ids",
                set(attribute_maps[entity_id]),
                errors,
            )

    return errors


def canonical_bytes(model: dict[str, Any]) -> bytes:
    return json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def source_digest(model: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(model)).hexdigest()


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def quoted(value: str) -> str:
    return value.replace('"', "'").replace("\n", " ")


def primary_attributes(entity: dict[str, Any]) -> set[str]:
    return {
        attribute_id
        for identifier in entity["identifiers"]
        if identifier.get("kind") == "primary"
        for attribute_id in identifier.get("attribute_ids", [])
    }


def artifact_header(model: dict[str, Any]) -> str:
    return (
        f"<!-- schema_version: {model['schema_version']} -->\n"
        f"<!-- source_sha256: {source_digest(model)} -->\n"
    )


def render_er(model: dict[str, Any]) -> str:
    lines = [artifact_header(model), "erDiagram"]
    for entity in model["entities"]:
        entity_name = safe_id(entity["id"]).upper()
        lines.append(f"    {entity_name} {{")
        primary = primary_attributes(entity)
        for attribute in entity["attributes"]:
            marker = " PK" if attribute["id"] in primary else ""
            lines.append(f"        {attribute['type']} {safe_id(attribute['id'])}{marker}")
        lines.append("    }")
    for relation in model["relations"]:
        left = relation["from"]
        right = relation["to"]
        lines.append(
            f"    {safe_id(left['entity']).upper()} "
            f"{CARDINALITY_SYMBOLS[left['cardinality']]}--"
            f"{CARDINALITY_SYMBOLS[right['cardinality']]} "
            f"{safe_id(right['entity']).upper()} : {quoted(relation['label'])}"
        )
    return "\n".join(lines) + "\n"


def render_flow(model: dict[str, Any]) -> str:
    lines = [artifact_header(model), "flowchart LR"]
    for flow in model["flows"]:
        flow_node = safe_id(flow["id"])
        lines.append(f'    subgraph {flow_node}["{quoted(flow["name"])}"]')
        for step in flow["steps"]:
            node = f"{flow_node}__{safe_id(step['id'])}"
            lines.append(f'        {node}["{quoted(step["label"])}"]')
        for step in flow["steps"]:
            source = f"{flow_node}__{safe_id(step['id'])}"
            for next_step in step["next"]:
                target = f"{flow_node}__{safe_id(next_step)}"
                lines.append(f"        {source} --> {target}")
        lines.append("    end")
    return "\n".join(lines) + "\n"


def render_ui(model: dict[str, Any]) -> str:
    entity_names = {entity["id"]: entity["name"] for entity in model["entities"]}
    event_names = {event["id"]: event["name"] for event in model["events"]}
    lines = [artifact_header(model), "flowchart LR"]
    for entity_id, name in entity_names.items():
        lines.append(f'    entity__{safe_id(entity_id)}(("{quoted(name)}"))')
    for event_id, name in event_names.items():
        lines.append(f'    event__{safe_id(event_id)}{{"{quoted(name)}"}}')
    for screen in model["screens"]:
        screen_node = f"screen__{safe_id(screen['id'])}"
        lines.append(f'    {screen_node}["{quoted(screen["name"])}"]')
        for entity_id in screen["entity_ids"]:
            lines.append(f"    {screen_node} --> entity__{safe_id(entity_id)}")
        for event_id in screen["event_ids"]:
            lines.append(f"    {screen_node} -.-> event__{safe_id(event_id)}")
    return "\n".join(lines) + "\n"


def generated_outputs(model: dict[str, Any]) -> dict[str, str]:
    return {
        "model.er.mmd": render_er(model),
        "model.flow.mmd": render_flow(model),
        "model.ui.mmd": render_ui(model),
    }


def write_outputs(model: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = generated_outputs(model)
    manifest_items: list[dict[str, str]] = []
    for name, content in artifacts.items():
        path = output_dir / name
        path.write_text(content, encoding="utf-8", newline="\n")
        manifest_items.append(
            {"path": name, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}
        )
    manifest = {
        "schema_version": model["schema_version"],
        "source_sha256": source_digest(model),
        "artifacts": manifest_items,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def check_generated(model: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="schema-first-") as temporary:
        output_dir = Path(temporary)
        first_manifest = write_outputs(model, output_dir)
        first_bytes = {path.name: path.read_bytes() for path in output_dir.iterdir()}
        second_manifest = write_outputs(model, output_dir)
        second_bytes = {path.name: path.read_bytes() for path in output_dir.iterdir()}
        if first_bytes != second_bytes:
            errors.append("generated artifacts are not deterministic")
        if first_manifest != second_manifest:
            errors.append("generated manifest is not deterministic")
        expected_digest = source_digest(model)
        if first_manifest.get("source_sha256") != expected_digest:
            errors.append("manifest source_sha256 does not match canonical model")
        for artifact in first_manifest.get("artifacts", []):
            path = output_dir / artifact["path"]
            content = path.read_text(encoding="utf-8")
            if f"schema_version: {model['schema_version']}" not in content:
                errors.append(f"{artifact['path']} is missing schema version provenance")
            if f"source_sha256: {expected_digest}" not in content:
                errors.append(f"{artifact['path']} is missing source digest provenance")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and render a schema-first model")
    parser.add_argument("--input", required=True, type=Path, help="canonical model JSON")
    parser.add_argument("--output-dir", type=Path, help="write generated artifacts here")
    parser.add_argument("--check-generated", action="store_true")
    parser.add_argument("--expect-invalid", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema_errors = validate_schema_metadata()
    if schema_errors:
        print("\n".join(schema_errors))
        return 1
    try:
        model = read_json(args.input)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"Cannot read canonical model: {error}")
        return 1

    errors = validate_model(model)
    if args.expect_invalid:
        if not errors:
            print("Expected the canonical model to be invalid, but validation passed")
            return 1
        print(f"Rejected invalid canonical model with {len(errors)} error(s).")
        print("\n".join(f"- {error}" for error in errors))
        return 0
    if errors:
        print("\n".join(errors))
        return 1

    if args.output_dir is not None:
        manifest = write_outputs(model, args.output_dir)
        print(f"Generated {len(manifest['artifacts'])} artifacts in {args.output_dir}")
    if args.check_generated:
        generated_errors = check_generated(model)
        if generated_errors:
            print("\n".join(generated_errors))
            return 1
        print("Deterministic generated artifacts and provenance checks passed.")
    print(f"Validated canonical model: {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
