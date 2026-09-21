# Codex Software Development Harness

この共通入口は `palladiumailab-collabmAILab/codex-dev-harness` 管理です。下流では共通部分を直接変更せず、project固有規則は `AGENTS.project.md` に置き、存在するときだけ併読します。

## Common invariants

- 依頼された成果、明示制約、受け入れ条件を変更しない。
- durable behaviorを変更するときは関連する正本仕様だけを読む。
- test / lint / build / CI は証拠であり成果そのものではない。合格のためだけに弱めない。
- 変更を最小範囲に保ち、依頼外機能・依存・大規模refactorを追加しない。
- unrelated changesを保持し、破壊的 reset / clean / force push を既定にしない。
- secretsを出力・commit・外部送信しない。未承認のdeploy、課金、削除、権限変更、外部書込みをしない。
- 同じ情報の無目的な再読込、状態変化のない同一検証の反復を避ける。

## Conditional references

必要な項目だけ読む。通常実装で `docs/project-baseline.md` 全体を先読みしない。

- 仕様変更: `docs/baselines/specifications.md`
- Docker / 再現環境: `docs/baselines/docker.md`
- GitHub Actions / remote gate: `docs/baselines/github-ci.md`
- Python / Ruff: `docs/baselines/python-ruff.md`
- task/evaluation/optimization contract: `docs/harness-architecture.md`
- explicit GitHub operations: `skills/github-operations/SKILL.md`
- unfamiliar cross-module research: `skills/repo-research/SKILL.md`
- iterative agent/workflow optimization: `skills/self-improvement/SKILL.md`
- multi-session handoff: `skills/long-running-work/SKILL.md`

## Model routing

- Default: `gpt-5.6-sol / medium`。
- `gpt-5.6-luna / max` は、独立した限定作業に切り出して Sol のcontext/往復を減らせる場合だけ使う。
- 短い・局所化済み・handoffの方が高くつくタスクは Sol 単独。Lunaの限定試行が失敗したら反復せず、根拠を短く渡してSolへ戻す。

同期元revisionとmanaged filesは `docs/harness-upstream.md` に記録します。
