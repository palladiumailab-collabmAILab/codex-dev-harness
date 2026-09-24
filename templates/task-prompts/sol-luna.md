# Sol / Luna task prompt

## Outcome

<!-- 依頼された成果。 -->

## Scope

- In scope:
- Out of scope:

## Acceptance criteria

- [ ] AC-1:
- [ ] AC-2:

## Required references

- canonical spec:
- `docs/testing-governance.md` when tests fail or change:

## Work split

- Sol: requirements, plan, architecture, acceptance criteria, test design, protected-oracle ownership, final review/integration.
- Luna: bounded implementation, new unit tests, test execution, local debugging.
- Luna が test/spec defect を疑う場合は既存 oracle を変更せず、failure と独立根拠を Sol へ返す。
- GitHub scope では Luna の protected-oracle change は専用 PR に留め、実装変更と同時に merge しない。

## Failure classification

- implementation bug:
- test bug:
- specification unresolved:

## Verification

- Required checks:
- Independent oracle/evidence:
- Remote CI required: yes / no

## Done when

- [ ] Outcome と全 AC に証拠がある。
- [ ] 必須検証が成功、または blocker が明示されている。
- [ ] oracle を green 化目的で変更していない。
- [ ] protected-oracle change は根拠とレビュー記録を持つ。
