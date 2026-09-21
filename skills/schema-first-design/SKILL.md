---
name: schema-first-design
description: Establish and validate a canonical data model before a substantial feature changes API, database, types, business flow, or UI structure. Do not use for routine local edits or an established schema-preserving change.
metadata:
  short-description: Derive design artifacts from one canonical model
---

# Schema-first design

Use this skill when a new or substantially changed feature changes the data model across two or more of API, database, application types, business flow, or UI structure, or when the user explicitly asks for schema-first design. Do not load it for a local field/route change that follows an established model, a small isolated UI edit, or ordinary code maintenance.

The canonical structured JSON is the source of truth. ER diagrams, business flows, UI maps, API mappings, types, and database changes are derived views or implementation outputs; do not make one of those views the independent authority.

## Workflow

1. State the requested outcome, domain scope, and acceptance criteria. Ask about materially ambiguous lifecycle, ownership, cardinality, or nullable behavior before encoding assumptions.
2. Read the relevant repository specification, entry points, existing data model, API conventions, and tests. Preserve established naming and types where they do not conflict with the requested model.
3. Define or update one canonical model containing the domain, entities, attributes, identifiers, constraints, relations, cardinalities, enums/statuses, business events/flows, screens, screen-to-entity references, and API input/output mappings.
4. Run the dependency-free validator before implementation. It must reject duplicate identifiers, missing required identifiers, dangling entity/screen/event/attribute references, invalid cardinality, and inconsistent API mappings.
5. Render ER, business-flow, and UI-map artifacts from the same canonical JSON. Generated artifacts must carry the canonical schema version and source digest; do not hand-edit them as a second source of truth.
6. Inspect the rendered artifacts together and resolve relation, lifecycle, nullable, ownership, and screen/API mismatches before generating code.
7. After the model is agreed, derive or implement API schemas, application types, database/ORM changes, and UI structure. Keep any non-generated implementation detail explicit and traceable to the canonical model.
8. Re-run validation and regeneration after model changes. Report the source version/digest and the checks that establish consistency.

## Minimum model contract

Use the versioned contract at `schemas/canonical-model.schema.json`. At minimum, every model needs:

- a `schema_version`, `model_id`, and domain;
- entities with stable IDs, typed attributes, nullability/required status, constraints, and at least one primary identifier;
- relations with valid endpoint entity IDs and explicit cardinality;
- enums/status values referenced by attributes when applicable;
- business events and ordered flow steps with valid references;
- screens with the entities/events they use;
- API operations whose input/output entity and attribute mappings are valid.

The validator is responsible for cross-reference and consistency rules that are awkward to express only in JSON Schema. A model that parses as JSON is not necessarily a valid design.

## Derivation mapping

Use the canonical fields as the mapping contract for implementation outputs:

- API/OpenAPI: each operation's method/path and input/output mapping becomes the endpoint contract; mapped attribute IDs determine the request and response fields.
- Application types: entity and attribute IDs/names become stable types; canonical attribute types, required, nullable, enum, and constraints become type/validation metadata.
- SQL/ORM: entities become tables/models, primary identifiers become keys, relation endpoints become foreign-key/association candidates, and nullability/constraints remain explicit migration inputs.
- UI structure: screens become routes/views, `entity_ids` define their data sources, and `event_ids`/flow steps define user-visible transitions.

Do not silently invent fields while deriving an artifact. If a target technology needs information the canonical model does not express, extend the model or document the explicit project-specific mapping before code generation.

## Design checks

Before implementation, explicitly check:

- every relation endpoint and cardinality matches the business lifecycle;
- identifiers are stable and required, and nullable attributes are not silently used as keys;
- constraints and enum/status values are represented once and referenced consistently;
- event and flow steps reference existing entities, screens, and events;
- screens do not invent fields or entities outside the model;
- API input/output mappings do not reference unknown or unrelated attributes;
- generated views have the same source schema version and digest.

If the model exposes a contradiction, stop at the model boundary and report it instead of hiding it in a UI-only field, ad-hoc API response, or migration.

## Boundaries with other guidance

- `repo-research` maps existing code and conventions before the model is changed.
- `architecture-design` handles broader module boundaries, dependency direction, provider isolation, lifecycle, and pattern selection. This skill handles domain/data source-of-truth and derived design artifacts.
- The model does not authorize unrelated implementation, migration, or deployment changes. Keep derived generation and code changes within the requested scope.
