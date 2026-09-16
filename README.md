# Codex 開発ハーネス

Codex をソフトウェア開発に使うための再利用可能な最小構成です。常時読む不変条件、必要時だけ読む task skill、共通contract、プロジェクト基準、機械的validationを分離します。

## 構成

```text
codex-dev-harness/
├── AGENTS.md                         # 常時ルールの短い入口
├── .github/workflows/validate.yml   # push/PR時の検証
├── .githooks/pre-commit             # 任意の軽量チェック
├── pyproject.toml                   # このハーネス自身のRuff設定
├── docs/
│   ├── harness-architecture.md      # 共通contractの意味
│   ├── project-baseline.md          # 再利用するプロジェクト基準
│   └── history/                     # 過去の監査・設計記録
├── skills/
│   ├── repo-research/
│   ├── github-operations/
│   ├── self-improvement/
│   ├── long-running-work/
│   └── reverse-engineering/         # 任意導入
├── scripts/
│   ├── install-githooks.ps1
│   ├── install-skills.ps1
│   ├── validate-harness.ps1
│   └── validate-skills.py
├── tests/
└── templates/
    ├── codex-progress.md
    └── project-specs/README.md      # 対象repoの docs/specs/ 用ひな形
```

詳細な手順は `AGENTS.md` に複製せず、該当する skill / docs を参照します。

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

対象リポジトリへ必要なファイルをコピーします。既存の `AGENTS.md` がある場合は上書きせず、プロジェクト固有ルールを残したまま統合します。

Codex のユーザー skill ディレクトリへ導入する場合、既定では日常利用する4 skillだけをコピーします。

```powershell
pwsh ./scripts/install-skills.ps1 -CodexSkillsRoot 'C:\Users\<ユーザー名>\.codex\skills'
```

既定導入:

- `repo-research`
- `github-operations`
- `self-improvement`
- `long-running-work`

特定skillだけ、または `reverse-engineering` のような特殊用途skillを導入する場合は明示します。

```powershell
pwsh ./scripts/install-skills.ps1 `
  -CodexSkillsRoot 'C:\Users\<ユーザー名>\.codex\skills' `
  -Name repo-research,reverse-engineering
```

既存の同名skillは上書きしません。

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

既定では Docker を使い、ハーネス自身の Ruff lint / format と skill validation を再現可能な環境で実行します。ホストPythonへ `requirements-dev.txt` の依存関係を導入済みなら `-SkipDocker` も使えます。GitHub Actionsでもpush/PRごとに同じ主要不変条件を確認します。

対象プロジェクトでも、ローカル/Docker検証は事前確認として扱い、GitHubへ反映した変更は対象commitまたはPRのGitHub Actions結果まで確認します。期待されるCIが存在しない、実行不能、または失敗している場合は、遠隔検証済みとは扱いません。

## モデル既定

Plusで利用可能な GPT-5.6 を前提に、利用枠を重要な判断へ集中させます。

- 通常の実装・設計・統合: `gpt-5.6-sol / medium`
- Sol利用枠を温存する限定探索・機械的確認: `gpt-5.6-luna / max`
- Lunaで条件を満たせない、または横断判断が必要なら、同じ失敗を反復せずSolへ昇格

詳細な判断規則は `AGENTS.md` を参照します。

## 参照先

- 共通contractと評価ゲート: `docs/harness-architecture.md`
- プロジェクト共通基準: `docs/project-baseline.md`
- 未知のrepo調査: `skills/repo-research/SKILL.md`
- GitHub操作: `skills/github-operations/SKILL.md`
- agent/workflow自己改善: `skills/self-improvement/SKILL.md`
- 長時間・複数セッション作業: `skills/long-running-work/SKILL.md`
- 特殊なblack-box/互換性解析: `skills/reverse-engineering/SKILL.md`

設計方針はOpenAIの公開するHarness Engineering、AGENTS.md、Subagents、モデルガイダンスを一次資料として扱います。
