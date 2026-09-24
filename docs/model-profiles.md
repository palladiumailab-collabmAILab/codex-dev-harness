# Model profiles

このハーネスは、モデル固有の補助指示を共通 `AGENTS.md` に混在させません。

## Selection

- GPT-6 Astra -> `profiles/astra/AGENTS.md`
- GPT-5.6 Sol / Luna -> `profiles/sol-luna/AGENTS.md`

root `AGENTS.md` は共通不変条件と routing だけを持ち、作業時には対応する profile を1つだけ読みます。skill は model-neutral に保ち、発火条件に一致した場合だけ読み込みます。

## Sol / Luna work split

Sol/Luna profile ではモデルの差より責務境界を優先する。

- Sol: requirements, plan, architecture, acceptance criteria, test design, test-code generation/maintenance, protected-oracle ownership, difficult debugging, final review/integration.
- Luna: bounded implementation, mechanical changes, test execution, result reporting, local debugging under a defined plan.
- Luna はテストコードおよび fixture / mock / expected / golden / snapshot / threshold / coverage / CI test conditions を直接変更しない。
- テスト変更が必要と考える場合、Luna は review 用 PR として提案し、Sol がレビュー・採否・merge 判断を担う。
- テストが失敗したとき Luna は oracle を実装へ追随させない。test bug / specification unresolved の疑いは `docs/testing-governance.md` に従って Sol へ返す。
- bounded worker の範囲を越える判断や反復失敗は Sol へ escalate する。

## Why Astra is separate

Astra 向けでは、常時 context を小さくし、必要な guidance を条件付きで読み込み、安全なローカル作業を過度な確認で止めず、タスク開始前に Done を明示することを重視します。Sol / Luna 向けの詳細な routing や段階的 workflow を Astra に流用しません。

一次資料:

- OpenAI Developers, “Rethinking skills and prompts for GPT-6 Astra”
  https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
