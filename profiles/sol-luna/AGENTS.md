# GPT-5.6 Sol / Luna profile

GPT-5.6 Sol または Luna のときだけ使用する。

## Routing

- Coordinator: `gpt-5.6-sol / medium` — 要求整理、計画、設計、受け入れ条件、テスト設計、テストコード生成・保守、protected-oracle change 判断、難しいデバッグ、最終レビューと統合。
- Worker: `gpt-5.6-luna / max` — Sol で境界が定まった実装、機械的変更、test 実行、局所デバッグ、Issue での結果報告。
- テスト失敗・変更では `docs/testing-governance.md` に従う。Luna はテストコード、fixture、mock、expected、golden、snapshot、threshold、coverage 設定、CI のテスト実行条件を直接変更しない。
- Luna がテスト変更を提案する場合は review 用 PR に限定し、Sol のレビュー・承認なしに merge しない。
- test bug / specification unresolved を疑う場合、Luna は失敗と独立根拠を保持して Sol へ戻す。
- Luna が局所判断を越える、または同じ失敗を反復する場合は Sol へ戻す。
- 追加 routing はユーザー指定または repo-local eval で測定可能な改善が確認された場合だけ導入する。

## Execution

1. Sol が目的、制約、受け入れ条件、テスト oracle、テストコード、変更境界を定める。
2. Luna は定められた範囲を実装し、テストを実行して結果を Issue に報告する。
3. failure は implementation bug / test bug / specification unresolved に分類する。
4. Luna がテスト変更を提案する場合は review 用 PR に限定する。
5. Sol がテスト変更と最終統合をレビューする。

## Done

成果が存在し、全 acceptance criterion に独立した証拠があり、関連 failure とテスト変更が未解決のまま成功扱いされていないこと。
