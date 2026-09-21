# Codex Software Development Harness

このファイルは常時読む最小入口です。詳細手順は必要なときだけ対応する profile / docs / skill を読みます。

## 正本

- 共通ハーネスの正本は `palladiumailab-collabmAILab/codex-dev-harness`。
- 下流の共通ファイルは upstream-managed とし、共通ルールは正本で変更してから同期する。
- プロジェクト固有ルールは `AGENTS.project.md`、project-specific skill / docs に分離する。

## 共通不変条件

- 依頼された成果、明示された制約、受け入れ条件を変えない。
- durable な製品・システム挙動を変える前に、関連する `docs/specs/` または既存の正本を確認し、仕様と実装の矛盾を黙って解消しない。
- test / lint / build / evaluation は証拠であり成果の代替ではない。通過のためだけに検証や閾値を弱めない。
- 変更は必要最小限にし、無関係な変更を保持する。破壊的 reset / clean / checkout や force push を既定にしない。
- 秘密情報を出力・コミット・送信しない。依頼のない deploy、課金、削除、権限変更、外部書き込みを行わない。
- 最寄りの指示、必要な仕様・コード・テスト・設定だけを読み、無目的な全件走査や巨大ログ展開を避ける。

## モデル profile

作業開始時に実行モデルに対応する profile を **1つだけ** 読む。

- GPT-6 Astra: `profiles/astra/AGENTS.md`
- GPT-5.6 Sol / Luna: `profiles/sol-luna/AGENTS.md`
- その他: この共通入口のみ。別モデルの profile を推測で流用しない。

## 必要時だけ読む

- Docker / GitHub Actions / Python-Ruff / 共通仕様配置: `docs/project-baseline.md`
- task contract / evaluation / optimization semantics: `docs/harness-architecture.md`
- セッション間 handoff: `templates/codex-progress.md`
- GitHub remote 操作: `skills/github-operations/SKILL.md`
- 未知の repo を横断調査: `skills/repo-research/SKILL.md`
- agent / workflow の評価付き反復改善: `skills/self-improvement/SKILL.md`
- agent harness の効率機構や外部候補を、baseline・hold-out・安全性ゲート付きで比較評価: `skills/harness-efficiency-evaluation/SKILL.md`
- 複数の大きな段階・セッションにまたがる作業: `skills/long-running-work/SKILL.md`
- 許可された opaque / legacy / binary / protocol の互換性調査: `skills/reverse-engineering/SKILL.md`

該当するものだけ読む。全 profile / docs / skill の先読みは禁止。
