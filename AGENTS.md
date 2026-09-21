# Codex Software Development Harness

このファイルは全モデル共通の最小入口です。システム・開発者指示とユーザーの明示依頼を優先し、リポジトリ内では現在地に近い `AGENTS.override.md` / `AGENTS.md` を優先します。

## 正本と下流リポジトリ

- 共通ハーネスの正本はこの `palladiumailab-collabmAILab/codex-dev-harness` リポジトリとする。
- 下流リポジトリへコピーされた共通ハーネスの内容は upstream-managed として扱い、プロジェクト固有の規則・設定・skill 以外を下流で直接書き換えない。
- 共通ハーネスを変更する必要がある場合は、先にこの正本を変更・検証し、その確定 revision から下流へ同期する。下流だけの独自 fork を作らない。
- プロジェクト固有の差分は `AGENTS.project.md`、project-specific skill、project docs など明示的に分離した領域へ置き、共通規則を黙って弱めない。
- 下流リポジトリは `docs/harness-upstream.md` に同期元 revision と upstream-managed file を記録する。

## モデルプロファイル

作業開始時に、実行中のモデルに対応するプロファイルを **1つだけ** 読みます。複数プロファイルを混ぜません。

- GPT-6 Astra: `profiles/astra/AGENTS.md`
- GPT-5.6 Sol / Luna: `profiles/sol-luna/AGENTS.md`
- その他のモデル: この共通入口だけを適用し、モデル固有の補助指示は推測で流用しません。

## 共通不変条件

- 依頼された成果、明示された制約、受け入れ条件を変更しない。
- 長期に有効な製品・システム仕様を変更する場合は、関連する `docs/specs/` または既存の正本を参照する。仕様と実装が矛盾する場合は黙って片方へ寄せない。
- テスト、lint、build、評価結果は受け入れ条件の証拠であり、それ自体を成果とみなさない。合格のためだけにテスト、評価器、閾値、受け入れ条件を弱めない。
- 依頼されていない機能、依存関係、外部連携、大規模リファクタリングを追加しない。
- 既存の未コミット変更や他者の変更を保持する。破壊的な reset / clean / checkout、force push を既定動作にしない。
- 秘密情報、秘密鍵、トークン、不要な個人情報を出力・コミット・外部送信しない。
- 依頼のないデプロイ、課金、データ削除、権限変更、外部サービスへの書き込みを行わない。

## 条件付きガイダンス

必要な場面でだけ読みます。

- 実行可能なソフトウェアの実装・変更・検証で、Docker再現性、GitHub Actions、Python/Ruff、仕様正本の扱いが関係するとき: `docs/project-baseline.md`
- task contract、評価、自己改善、実行結果の意味を変更するとき: `docs/harness-architecture.md`
- 長時間作業の引き継ぎが必要なとき: `templates/codex-progress.md`
- モデル別タスク依頼を組み立てるとき: `templates/task-prompts/`

## Skill の発火条件

- `repo-research`: 未知のリポジトリで複数モジュールを横断して入口・依存・実行経路を特定する必要があるとき。既知ファイルの小修正では使わない。
- `github-operations`: GitHub の branch / commit / push / pull / Issue / PR / CI 確認 / remote file mutation を明示的に依頼されたとき。ローカルだけの編集では使わない。
- `self-improvement`: 既存の agent / prompt / tool / workflow を、baseline と評価基準に対して候補比較しながら反復改善するとき。一回限りの書き換えでは使わない。
- `long-running-work`: 1回の通常実装パスでは完了できず、複数の大きな段階またはセッション間 handoff が必要なとき。単に手順が複数あるだけでは使わない。
- `reverse-engineering`: 許可された opaque / legacy / binary / protocol component の観測可能な挙動を、互換性・移行・診断・防御目的で調べるとき。通常のコード読解では使わない。
- `schema-first-design`: API / DB / 型 / 業務フロー / UIを横断する新規・大幅変更で、canonical data modelと派生成果物の整合性を先に確定するとき。通常の局所修正では使わない。

該当する skill だけ `SKILL.md` を読みます。全 skill の事前読み込みはしません。
