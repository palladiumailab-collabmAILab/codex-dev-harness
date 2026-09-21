# Codex 開発ハーネス

Codex をソフトウェア開発に使うための再利用可能なハーネスです。共通の最小入口、モデル別 profile、条件付き task skill、共通 contract、project baseline、task prompt、機械的 validation を分離します。

## 構成

```text
codex-dev-harness/
├── AGENTS.md                         # 全モデル共通の最小入口
├── .github/workflows/validate.yml   # push/PR時の検証
├── .githooks/pre-commit             # 任意の軽量チェック
├── pyproject.toml                   # このハーネス自身のRuff設定
├── profiles/
│   ├── astra/AGENTS.md              # GPT-6 Astra固有
│   └── sol-luna/AGENTS.md           # GPT-5.6 Sol/Luna固有
├── docs/
│   ├── model-profiles.md            # モデル分離方針
│   ├── harness-architecture.md      # 共通contractの意味
│   ├── contracts/                    # 実行・評価contractの利用ガイド
│   ├── project-baseline.md          # 再利用するプロジェクト基準
│   ├── evals/                        # 代表的なrouting/evaluation fixtureの説明
│   └── history/                     # 過去の監査・設計記録
├── harness_contracts/                # 標準ライブラリの実行・評価ヘルパー
├── schemas/                          # versioned execution/evaluation schemas
│   └── canonical-model.schema.json  # schema-first canonical model contract
├── skills/
│   ├── repo-research/
│   ├── github-operations/
│   ├── code-review/
│   ├── self-improvement/
│   ├── long-running-work/
│   ├── reverse-engineering/         # 任意導入
│   ├── architecture-design/         # 構造変更時だけ使う条件付きskill
│   ├── asset-extraction/            # 大規模asset tree向け、任意導入
│   └── schema-first-design/         # data modelを横断変更するときだけ使う条件付きskill
├── scripts/
│   ├── harness-provenance.ps1     # manifest / hash / sync primitives
│   ├── install-githooks.ps1
│   ├── install-skills.ps1          # first-time install only
│   ├── sync-skills.ps1             # dry-run and idempotent update
│   ├── validate-harness-manifest.ps1
│   ├── validate-harness.ps1
│   ├── validate-code-review-evals.py
│   ├── validate-skill-registration.py
│   ├── validate-model-profiles.py
│   ├── validate-architecture-evals.py
│   ├── validate-contracts.py
│   ├── validate-schema-first.py
│   └── validate-skills.py
├── tests/
│   ├── test-harness-sync.ps1
│   └── test-pre-commit.sh
└── templates/
    ├── task-prompts/
    │   ├── astra.md
    │   └── sol-luna.md
    ├── codex-progress.md
    ├── downstream/
    │   ├── AGENTS.md                # 下流向け共通入口（upstream-managed）
    │   ├── AGENTS.project.md        # プロジェクト固有規則の分離先
    │   └── harness-upstream.md      # 同期元revision/managed files記録
    └── project-specs/README.md      # 対象repoの docs/specs/ 用ひな形
```

詳細な手順は root `AGENTS.md` に複製せず、対応する model profile と、発火条件に一致した skill / docs だけを参照します。

## モデル分離

root `AGENTS.md` は共通不変条件と routing だけを持ちます。作業時には対応する profile を1つだけ読み、Astra と Sol/Luna の補助指示を混ぜません。

- GPT-6 Astra: `profiles/astra/AGENTS.md`
- GPT-5.6 Sol / Luna: `profiles/sol-luna/AGENTS.md`

Astra profile は、必要な guidance の条件付き読み込み、安全なローカル作業の継続、明示的な Done を重視します。Sol/Luna profile は従来の明示的な workflow と Sol/Luna routing を保持します。

詳細は `docs/model-profiles.md` を参照してください。

## Skill

skill は model-neutral に保ちます。frontmatter の description は「何に関連するか」ではなく「どの具体的な作業で発火するか」を記述し、root `AGENTS.md` の発火条件に一致した skill だけ読み込みます。

既定導入:

- `repo-research`
- `github-operations`
- `code-review`
- `self-improvement`
- `long-running-work`

構造変更用の `architecture-design`、データモデル横断変更用の `schema-first-design`、特殊用途の `reverse-engineering` は、該当時だけ明示的に選択します。いずれも日常の小さな修正向けの既定導入には含めません。
大規模または混在したasset treeを扱う場合は `asset-extraction` を明示的に選択します。

## Task prompt

モデル別の task prompt を分離しています。

- Astra: `templates/task-prompts/astra.md`
- Sol/Luna: `templates/task-prompts/sol-luna.md`

Astra 用 prompt は Outcome / Scope / Constraints / 必要時だけ読む資料 / Done when を明示し、最初の実装で止まらず必要な検証と修正まで継続する許可を含みます。

## プロジェクト基準

対象リポジトリへ適用する共通基準は `docs/project-baseline.md` を正本とします。主要ルールは次の通りです。

- 長期に有効な製品・システム仕様は `docs/specs/` に集約し、実装判断より先に関連仕様を参照する。
- 実行可能なソフトウェアは Docker で再現可能な開発・検証経路を持つ。
- GitHubで管理する実行可能なソフトウェアでは、GitHub Actions を標準の遠隔品質ゲートとし、PRとdefault branch pushでプロジェクト固有の検証を実行する。
- Python を含むリポジトリでは、新規・既存を問わず Ruff を lint / format の標準品質ゲートにし、GitHub Actionsでも実行する。
- テスト、型チェック、build、repository invariant、domain validator 等は適用範囲に応じてCIへ載せ、ローカル成功だけで完了扱いしない。
- Webアプリの `frontend/` / `backend/` 物理分離、framework、DB、service topology はプロジェクト固有とし、ハーネスから一律強制しない。

`templates/project-specs/README.md` は対象リポジトリの `docs/specs/README.md` として利用できます。既存仕様書がある場合は、上書きせず正本を一つに整理します。

## 導入

共通ハーネスの正本はこのリポジトリです。対象リポジトリへコピーした共通部分は upstream-managed とし、下流側では直接改変しません。共通規則の変更はこのリポジトリで行い、検証済み revision から同期します。

新規導入では `templates/downstream/AGENTS.md` を root `AGENTS.md` として使い、プロジェクト固有規則は `AGENTS.project.md` へ分離します。同期元 revision と managed file set は `docs/harness-upstream.md` に記録します。既存の project-specific `AGENTS.md` がある場合は、その固有部分を `AGENTS.project.md` 等へ移し、共通部分と混在させないでください。

対象リポジトリへ必要なSkillをコピーします。既存の共通 `AGENTS.md` は上書きせず、プロジェクト固有ルールは `AGENTS.project.md` に分離します。Skillの導入先を対象リポジトリ内（例: `.codex/skills`）に置き、`harness.lock.json` をコミットすると、導入元commitと管理対象ファイルのhashをCIで監査できます。

Codex のユーザー skill ディレクトリへ導入する場合、既定では日常利用する5 skillだけをコピーします。

```powershell
pwsh ./scripts/install-skills.ps1 -CodexSkillsRoot 'C:\Users\<ユーザー名>\.codex\skills'
```

特定skillだけ、または `reverse-engineering` / `asset-extraction` のような特殊用途skillを導入する場合は明示します。

```powershell
pwsh ./scripts/install-skills.ps1 `
  -CodexSkillsRoot 'C:\Users\<ユーザー名>\.codex\skills' `
  -Name repo-research,reverse-engineering,asset-extraction
```

既存の同名skillは上書きしません。

初回導入後の更新は `install-skills.ps1` ではなく `sync-skills.ps1` を使います。`install` は既存のSkillディレクトリやmanifestを上書きしないため、誤った再導入でローカル変更を壊しません。

```powershell
pwsh ./scripts/install-skills.ps1 `
  -RepositoryRoot 'C:\path\to\codex-dev-harness' `
  -CodexSkillsRoot '.\.codex\skills' `
  -ManifestPath '.\harness.lock.json'

pwsh ./scripts/sync-skills.ps1 `
  -RepositoryRoot 'C:\path\to\codex-dev-harness' `
  -CodexSkillsRoot '.\.codex\skills' `
  -ManifestPath '.\harness.lock.json' `
  -DryRun

pwsh ./scripts/sync-skills.ps1 `
  -RepositoryRoot 'C:\path\to\codex-dev-harness' `
  -CodexSkillsRoot '.\.codex\skills' `
  -ManifestPath '.\harness.lock.json'
```

Dry-runは `add` / `update` / `unchanged` / `remove` / `conflict` を表示します。manifestに記録したhashと異なるローカル変更は `conflict` として終了コード2で報告し、更新を一切適用しません。管理対象外のファイルはコピー・削除しないため、下流リポジトリ固有のファイルは保持されます。

導入先のCIではmanifest driftを次のように検査できます。

```powershell
pwsh ./path/to/codex-dev-harness/scripts/validate-harness-manifest.ps1 `
  -CodexSkillsRoot '.\.codex\skills' `
  -ManifestPath '.\harness.lock.json'
```

競合から復旧する場合は、ローカル変更をレビューして別名へ退避した後、manifest記載の旧内容へ戻すか、意図したローカル変更を新しい導入元へ取り込んでから再度 `sync-skills.ps1 -DryRun` を実行します。rollbackは、別のharness checkoutを対象commitに切り替えて同じdry-run/sync手順を使います。いずれもforce pushや無条件上書きは必要ありません。

Git hook は任意です。

```powershell
pwsh ./scripts/install-githooks.ps1
```

解除:

```powershell
git config --unset core.hooksPath
```

## 検証

Windowsでは次を実行します。

```powershell
pwsh ./scripts/validate-harness.ps1
```

既定では Docker を使い、ハーネス自身の Ruff lint / format、skill validation、skill登録整合性、代表評価ケースのcoverage、model-profile separation validation を再現可能な環境で実行します。ホストPythonへ `requirements-dev.txt` の依存関係を導入済みなら `-SkipDocker` も使えます。

GitHub Actionsでもpush/PRごとに以下を確認します。

- Ruff lint / format
- skill frontmatter
- Astra と Sol/Luna の profile / task prompt 分離
- schema-first canonical modelのvalid/invalid fixture、参照整合性、決定的レンダー
- Sol/Luna の既定route、bounded worker、escalation、profile非混在の代表fixture
- architecture-design の代表評価fixture（抽象化が有効なケースと過剰設計のケース）
- execution/evaluation contractのunit testとvalid/invalid fixture
- root `AGENTS.md` のサイズ
- whitespace / hook invariant
- provenance-aware skill sync regression transitions

対象プロジェクトでも、ローカル/Docker検証は事前確認として扱い、GitHubへ反映した変更は対象commitまたはPRのGitHub Actions結果まで確認します。期待されるCIが存在しない、実行不能、または失敗している場合は、遠隔検証済みとは扱いません。

## モデル既定

- GPT-6 Astra: `profiles/astra/AGENTS.md` (optional)
- GPT-5.6 Sol / Luna: `profiles/sol-luna/AGENTS.md` (standalone; Astra is not a prerequisite)

Sol/Luna の routing 詳細は model profile に限定し、Astra へ流用しません。Sol/Luna を使うときに Astra profile を追加で読む必要はありません。

## 参照先

- モデル分離: `docs/model-profiles.md`
- 共通contractと評価ゲート: `docs/harness-architecture.md`
- GPT-5.6 routing の代表評価: `docs/evals/model-routing.md`
- 実行・評価contract: `docs/contracts/execution.md`, `docs/contracts/evaluation.md`
- プロジェクト共通基準: `docs/project-baseline.md`
- 未知のrepo調査: `skills/repo-research/SKILL.md`
- GitHub操作: `skills/github-operations/SKILL.md`
- コードレビューとレビュー中心の回帰検証: `skills/code-review/SKILL.md`
- コードレビュー評価ケース: `docs/evals/code-review.md`
- コードレビュー方法論の出典記録: `docs/history/code-review-methodology.md`
- agent/workflow自己改善: `skills/self-improvement/SKILL.md`
- 長時間・複数セッション作業: `skills/long-running-work/SKILL.md`
- 特殊なblack-box/互換性解析: `skills/reverse-engineering/SKILL.md`
- canonical data modelから派生成果物を作る設計: `skills/schema-first-design/SKILL.md`
- schema-first評価: `docs/evals/schema-first-design.md`
- 構造設計・pattern選択: `skills/architecture-design/SKILL.md`
- architecture-design の代表評価: `docs/evals/architecture-design.md`
- 大規模asset treeのinventory/候補抽出: `skills/asset-extraction/SKILL.md`
- Astra task prompt: `templates/task-prompts/astra.md`
- Sol/Luna task prompt: `templates/task-prompts/sol-luna.md`

設計方針はOpenAIの公開するHarness Engineering、AGENTS.md、Subagents、モデルガイダンスを一次資料として扱います。
