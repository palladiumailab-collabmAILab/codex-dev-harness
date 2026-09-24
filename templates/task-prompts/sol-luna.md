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

- Sol: requirements, plan, architecture, acceptance criteria, test design, test-code generation/maintenance, protected-oracle ownership, final review/integration.
- Luna: bounded implementation, test execution, Issue での結果報告, local debugging.
- Luna はテストコードや fixture / mock / expected / golden / snapshot / threshold / coverage / CI test conditions を直接変更しない。
- Luna が test/spec defect を疑う場合は failure と独立根拠を Sol へ返す。
- GitHub scope では Luna のテスト変更案は review 用 PR に留め、Sol のレビュー・承認なしに merge しない。

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
- [ ] Luna のテスト変更提案は review PR に限定され、Sol の承認前に merge されていない。
