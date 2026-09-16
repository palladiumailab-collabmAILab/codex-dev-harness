# Codex 開発ハーネス

Codex をソフトウェア開発に使うための再利用可能な最小構成です。常時読む不変条件、必要時だけ読む task skill、共通contract、機械的validationを分離します。

## 構成

```text
codex-dev-harness/
├── AGENTS.md                         # 常時ルールの短い入口
├── .github/workflows/validate.yml   # push/PR時の検証
├── .githooks/pre-commit             # 任意の軽量チェック
├── docs/
│   ├── harness-architecture.md      # 共通contractの意味
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
└── templates/codex-progress.md
```

詳細な手順は `AGENTS.md` に複製せず、該当する skill / docs を参照します。

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

ホストPythonへ `requirements-dev.txt` の依存関係を導入済みなら `-SkipDocker` も使えます。GitHub Actionsでもpush/PRごとに同じ主要不変条件を確認します。

## モデル既定

- 通常の実装・設計・統合: `gpt-5.6-sol / medium`
- 限定された探索・機械的確認: `gpt-5.6-luna / max`
- Lunaで条件を満たせなければ、同じ失敗を反復せずSolへ昇格

詳細な判断規則は `AGENTS.md` を参照します。

## 参照先

- 共通contractと評価ゲート: `docs/harness-architecture.md`
- 未知のrepo調査: `skills/repo-research/SKILL.md`
- GitHub操作: `skills/github-operations/SKILL.md`
- agent/workflow自己改善: `skills/self-improvement/SKILL.md`
- 長時間・複数セッション作業: `skills/long-running-work/SKILL.md`
- 特殊なblack-box/互換性解析: `skills/reverse-engineering/SKILL.md`

設計方針はOpenAIの公開するHarness Engineering、AGENTS.md、Subagents、モデルガイダンスを一次資料として扱います。
