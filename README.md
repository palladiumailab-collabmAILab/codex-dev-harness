# Codex 開発ハーネス

Codex向けの再利用可能ハーネスです。狙いは、共通の安全・品質条件を保ちながら **常時コンテキストを小さくし、必要な規則だけ遅延読込すること** です。

## 構造

- `AGENTS.md`: 常時読む最小ルータ
- `profiles/`: モデル固有の短い補助指示
- `docs/baselines/`: 仕様 / Docker / GitHub CI / Python-Ruff を個別に遅延読込
- `docs/harness-architecture.md`: task/evaluation/optimization contract
- `skills/`: 発火条件付きの詳細workflow
- `templates/downstream/`: 下流repo同期用
- `scripts/`, `tests/`, `.github/workflows/`: 機械的検証

`docs/project-baseline.md` は互換性用の索引です。通常タスクでは全文を読まず、変更対象に対応する `docs/baselines/*.md` だけ参照します。

## Context / token 方針

1. 常時ファイルには不変条件とroutingだけを置く。
2. repo-wide scanよりtargeted searchを優先する。
3. 大きなlog/tool outputを会話へ丸ごと複製しない。
4. 状態変化のない再読込・同一検証を反復しない。
5. worker委譲は、handoff + 再読込を含めても親モデルのcontext/往復を減らせる場合だけ行う。
6. 詳細な品質規則はdocs/skills/CIへ移し、root promptへ重複させない。

## Model routing

- GPT-6 Astra: `profiles/astra/AGENTS.md`
- GPT-5.6 Sol / Luna: `profiles/sol-luna/AGENTS.md`

Sol/LunaではSolを既定とし、Lunaは独立したbounded workで実際に総仕事量を減らせる場合だけ使います。局所化済みの短いタスクを無理にサブエージェントへ分解しません。

## Downstream

共通ハーネスの正本はこのrepoです。下流では:

- `templates/downstream/AGENTS.md` を共通入口として同期
- project固有規則は `AGENTS.project.md`
- `docs/harness-upstream.md` にsource revisionとmanaged file setを記録
- 共通規則は下流でforkせず正本を変更してから再同期

## Validation

Windows:

```powershell
pwsh ./scripts/validate-harness.ps1
```

CIではRuff、skill frontmatter、model profile分離、root AGENTS size、hook invariantを検証します。

## 主な参照先

- baseline index: `docs/project-baseline.md`
- specifications: `docs/baselines/specifications.md`
- Docker: `docs/baselines/docker.md`
- GitHub CI: `docs/baselines/github-ci.md`
- Python/Ruff: `docs/baselines/python-ruff.md`
- contracts: `docs/harness-architecture.md`
- repo research: `skills/repo-research/SKILL.md`
- GitHub operations: `skills/github-operations/SKILL.md`
- self improvement: `skills/self-improvement/SKILL.md`
- long-running work: `skills/long-running-work/SKILL.md`
