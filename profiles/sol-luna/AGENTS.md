# GPT-5.6 Sol / Luna profile

GPT-5.6 Sol または Luna のときだけ使用する。

## Routing

- Coordinator: `gpt-5.6-sol / medium` — 要求整理、計画、設計、受け入れ条件、テスト設計、protected oracle 判断、難しいデバッグ、最終レビューと統合。
- Worker: `gpt-5.6-luna / max` — Sol で境界が定まった実装、機械的変更、新規 unit test、test 実行、局所デバッグ。
- テスト失敗・変更では `docs/testing-governance.md` に従う。Luna は既存 assertion / expected / golden / snapshot、regression / acceptance / contract test、skip / xfail / deletion を green 化のために変更しない。
- test bug / specification unresolved を疑う場合、Luna は失敗と独立根拠を保持して Sol へ戻す。protected-oracle change は review 用 PR に留める。
- Luna が局所判断を越える、または同じ失敗を反復する場合は Sol へ戻す。
- 追加 routing はユーザー指定または repo-local eval で測定可能な改善が確認された場合だけ導入する。

## Execution

1. Sol が目的、制約、受け入れ条件、テスト oracle、変更境界を定める。
2. Luna は定められた範囲を実装し、必要な developer test を追加して検証する。
3. failure は implementation bug / test bug / specification unresolved に分類する。
4. Sol が protected-oracle change と最終統合をレビューする。

## Done

成果が存在し、全 acceptance criterion に独立した証拠があり、関連 failure と oracle 変更が未解決のまま成功扱いされていないこと。
