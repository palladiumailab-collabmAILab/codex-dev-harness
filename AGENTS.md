# Codex Software Development Harness

このファイルは常時読む最小入口です。詳細手順は必要なときだけ対応する docs / skill を読みます。

## 正本

- OpenAI公式の Codex / skills / security / action / runtime が最上位の正本。
- このリポジトリは公式挙動を上書きせず、非衝突の補助規則だけを提供する。
- 下流の共通ファイルは upstream-managed とし、プロジェクト固有ルールは `AGENTS.project.md`、project-specific skill / docs に分離する。
- 公式とローカルが衝突した場合は、`docs/openai-official-harness.md` に従い公式を優先する。

## 共通不変条件

- 依頼された成果、明示された制約、受け入れ条件を変えない。
- durable な製品・システム挙動を変える前に、関連する `docs/specs/` または既存の正本を確認し、仕様と実装の矛盾を黙って解消しない。
- test / lint / build / evaluation は証拠であり成果の代替ではない。失敗時に oracle を実装へ追随させず、テスト変更は `docs/testing-governance.md` に従う。
- 変更は必要最小限にし、無関係な変更を保持する。破壊的 reset / clean / checkout や force push を既定にしない。
- 秘密情報を出力・コミット・送信しない。依頼のない deploy、課金、削除、権限変更、外部書き込みを行わない。
- 最寄りの指示、必要な仕様・コード・テスト・設定だけを読み、無目的な全件走査や巨大ログ展開を避ける。
- モデル名・モデル役割・既定モデルをローカルで固定しない。Codex の公式挙動と利用可能モデルをその時点の正本とする。

## 必要時だけ読む

- `repo-research`: 未知のリポジトリ、複雑な依存関係、外部仕様を実装前に調査するとき。
- `github-operations`: GitHubへの作成・同期・push/pull・Issue・PR等を明示的に依頼されたとき。
- `code-review`: PR、diff、patch、commit、AI生成コードをレビューするとき。
- `self-improvement`: agent/workflow を評価付きで反復改善するとき。
- `long-running-work`: 長時間または複数セッションにまたがる作業を分割・引き継ぐとき。
- OpenAI公式との優先順位と統合: `docs/openai-official-harness.md`
- Docker / GitHub Actions / Python-Ruff / 共通仕様配置: `docs/project-baseline.md`
- task contract / evaluation / optimization semantics: `docs/harness-architecture.md`
- セッション間 handoff: `templates/codex-progress.md`
- GitHub remote 操作: `skills/github-operations/SKILL.md`
- 未知の repo を横断調査: `skills/repo-research/SKILL.md`
- agent / workflow の評価付き反復改善: `skills/self-improvement/SKILL.md`
- agent harness の効率機構や外部候補を比較評価: `skills/harness-efficiency-evaluation/SKILL.md`
- Computer Use の decision backend を比較評価: `skills/computer-use-backend-evaluation/SKILL.md`
- canonical data model と派生成果物の整合性設計: `skills/schema-first-design/SKILL.md`
- 抽象化・pattern・module boundary の比較: `skills/architecture-design/SKILL.md`
- 大規模 asset tree の inventory・重複排除・候補絞り込み: `skills/asset-extraction/SKILL.md`
- 許可された opaque / legacy / binary / protocol の互換性調査: `skills/reverse-engineering/SKILL.md`

該当するものだけ読む。全 docs / skill の先読みは禁止。
