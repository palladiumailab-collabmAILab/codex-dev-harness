# Codex 開発ハーネス

Codex をソフトウェア開発に使うための再利用可能なハーネスです。共通の最小入口、モデル別 profile、条件付き task skill、project baseline、task prompt、機械的 validation を分離します。

## 構成

```text
codex-dev-harness/
├── AGENTS.md
├── profiles/
│   ├── astra/AGENTS.md
│   └── sol-luna/AGENTS.md
├── skills/
│   ├── repo-research/
│   ├── github-operations/
│   ├── self-improvement/
│   ├── long-running-work/
│   └── reverse-engineering/
├── templates/
│   ├── task-prompts/
│   │   ├── astra.md
│   │   └── sol-luna.md
│   ├── codex-progress.md
│   └── project-specs/README.md
├── docs/
│   ├── model-profiles.md
│   ├── harness-architecture.md
│   └── project-baseline.md
├── scripts/
│   ├── validate-skills.py
│   ├── validate-model-profiles.py
│   └── validate-harness.ps1
└── .github/workflows/validate.yml
```

## モデル分離

root `AGENTS.md` は共通不変条件と routing だけを持ちます。作業時には対応する profile を1つだけ読み、Astra と Sol/Luna の補助指示を混ぜません。

- GPT-6 Astra: `profiles/astra/AGENTS.md`
- GPT-5.6 Sol / Luna: `profiles/sol-luna/AGENTS.md`

Astra profile は、必要な guidance の条件付き読み込み、安全なローカル作業の継続、明示的な Done を重視します。Sol/Luna profile は、従来の明示的な workflow と Sol/Luna routing を保持します。

詳細は `docs/model-profiles.md` を参照してください。

## Skill

skill は model-neutral に保ちます。frontmatter の description は「何に関連するか」ではなく「どの具体的な作業で発火するか」を記述し、root `AGENTS.md` の発火条件に一致した skill だけ読み込みます。

既定導入:

- `repo-research`
- `github-operations`
- `self-improvement`
- `long-running-work`

特殊用途の `reverse-engineering` は明示的に選択します。

```powershell
pwsh ./scripts/install-skills.ps1 -CodexSkillsRoot 'C:\Users\<ユーザー名>\.codex\skills'
```

特定 skill だけ導入する場合:

```powershell
pwsh ./scripts/install-skills.ps1 `
  -CodexSkillsRoot 'C:\Users\<ユーザー名>\.codex\skills' `
  -Name repo-research,reverse-engineering
```

## Task prompt

モデル別の task prompt を分離しています。

- Astra: `templates/task-prompts/astra.md`
- Sol/Luna: `templates/task-prompts/sol-luna.md`

特に Astra 用 prompt は、Outcome / Scope / Constraints / 必要時だけ読む資料 / Done when を明示し、最初の実装で止まらず必要な検証と修正まで継続する許可を含みます。

## Project baseline

共通の project baseline は `docs/project-baseline.md` を正本とします。

- durable specification は `docs/specs/` または既存の単一正本に集約
- 実行可能なソフトウェアは Docker で再現可能な経路を持つ
- GitHub で管理する実行可能なソフトウェアは GitHub Actions を遠隔品質ゲートにする
- Python は Ruff を lint / format の標準品質ゲートにする
- framework、DB、service topology、frontend/backend の物理分離はプロジェクト固有

## 検証

Windows:

```powershell
pwsh ./scripts/validate-harness.ps1
```

既定では Docker 上で Ruff、skill validation、model-profile separation validation を実行します。ホスト依存関係がある場合は `-SkipDocker` も利用できます。

GitHub Actions でも以下を検証します。

- Ruff lint / format
- skill frontmatter
- Astra と Sol/Luna の profile / task prompt 分離
- root `AGENTS.md` のサイズ
- whitespace / hook invariant

## 参照先

- モデル分離: `docs/model-profiles.md`
- 共通 contract と評価: `docs/harness-architecture.md`
- project baseline: `docs/project-baseline.md`
- Astra task prompt: `templates/task-prompts/astra.md`
- Sol/Luna task prompt: `templates/task-prompts/sol-luna.md`
