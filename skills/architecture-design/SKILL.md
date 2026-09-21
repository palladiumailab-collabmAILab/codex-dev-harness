---
name: architecture-design
description: Choose the simplest sufficient architecture for real module boundaries, external integrations, interchangeable implementations, persistence boundaries, large refactors, or explicit design reviews. Do not use for routine local edits.
metadata:
  short-description: Evaluate structural design pressure before abstraction
---

# Evidence-based architecture design

Use this skill only when a change may alter a module boundary, dependency direction, external-system boundary, lifecycle, or another structural property, or when the user explicitly asks for architecture/design review. Do not load it for an isolated bug fix, small CRUD change, local function, or an existing repository pattern that already answers the design question.

The objective is the least complex design that satisfies the current requirement and credible near-term variation. A named pattern is an option, not a goal. "No new abstraction" is a valid architecture decision.

## Evidence gate

Before choosing a design:

1. State the requested outcome and the acceptance criteria that the design must preserve.
2. If the relevant codebase or flow is unfamiliar, use `repo-research` first. Do not infer a new architecture from a partial file search.
3. Inspect the existing entry points, dependency direction, local conventions, tests, and integration boundaries that the change will touch.
4. Name the concrete pressure and its evidence: a stable variation axis, coupling that crosses a boundary, dependency-direction failure, lifecycle/construction complexity, replaceability need, or a real producer/consumer independence requirement.
5. Compare a direct implementation, the smallest extraction that would help, and any larger abstraction. Reject options whose only benefit is stylistic cleanliness or future speculation.

If no concrete pressure is supported by evidence, choose the direct implementation or a small function/module extraction and record why a pattern is unnecessary.

## Decision sequence

Evaluate these questions in order:

1. Can the requirement be met directly without weakening a boundary or creating repeated variation?
2. Does the repository already have a local solution or convention? Prefer extending it over importing a new architectural style.
3. What change axis or boundary needs isolation, and what is the smallest mechanism that isolates it?
4. Would the proposed indirection improve coupling, cohesion, dependency direction, lifecycle control, replaceability, or testability now - not merely in a hypothetical future?
5. Select a named pattern only when its property is clearer and more durable than a direct implementation or small extraction.
6. Define validation that demonstrates the gained property and protects the existing behavior.

## Lightweight pattern criteria

| Option | Consider only when | Do not use when |
|---|---|---|
| Direct implementation | One local, stable behavior is sufficient. | A real boundary or repeated variation would be hidden or duplicated. |
| Function/module extraction | Cohesion or duplication is the problem and polymorphism is not needed. | An interface is being added only for aesthetic "clean code." |
| Strategy | Multiple algorithms are genuinely interchangeable and selection or independent testing matters. | There is one trivial algorithm or no credible second variation. |
| Adapter / port | External provider details must be kept out of domain/application code, or provider replacement/migration is realistic. | A wrapper only renames a stable local function. |
| Factory | Construction has meaningful branching, lifecycle, or dependency knowledge that callers should not own. | Construction is one simple expression. |
| Repository | Persistence isolation provides real value through multiple implementations, complex mapping, or a meaningful test boundary. | A database exists but direct persistence is simple and local. |
| Event / observer | Multiple consumers must evolve independently or asynchronous/event semantics are part of the requirement. | An event merely hides a simple synchronous call. |

Do not apply Clean Architecture, hexagonal architecture, dependency-injection layers, queues, factories, repositories, or interfaces wholesale to a small application without demonstrated pressure.

## Decision record

For a non-trivial structural choice, return a compact record with:

```text
Current pressure:
Evidence:
Simplest viable option:
Alternatives considered:
Chosen design:
Property gained:
Why more complex options were rejected:
Validation/tests:
```

Use concrete paths, symbols, tests, or observed behavior as evidence where available. Explain the choice by the property gained - such as provider isolation, dependency direction, replaceability, lifecycle control, or testability - not by pattern-name recognition.

The record guides the requested implementation or review; it does not authorize unrelated redesign. Keep the change small enough that the stated property can be verified.

## Boundaries with other guidance

- `repo-research` maps the existing architecture and evidence; this skill decides whether structural change is warranted.
- A future or project-specific schema-first skill may define a canonical data model and derive API, type, database, or UI artifacts. This skill handles broader software-architecture choices such as module boundaries, external integrations, dependency direction, lifecycle, and concurrency/event boundaries.
- `code-review` should identify concrete structural findings. Use this skill when resolving a finding requires a non-trivial boundary, abstraction, or pattern choice; do not turn an ordinary review into a redesign.

## Anti-pattern check

Before finalizing, explicitly check that the proposal does not:

- add an interface, factory, repository, or service layer without a concrete change pressure;
- apply a GoF pattern before understanding the actual collaboration or boundary;
- create an abstraction with one trivial implementation and no boundary value;
- rewrite a working local architecture to match a preferred global style;
- use events or queues to conceal straightforward synchronous control flow;
- treat speculative future requirements as present acceptance criteria.
