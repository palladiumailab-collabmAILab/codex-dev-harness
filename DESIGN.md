# Design

## Purpose

Codexを用いたソフトウェア開発で、計画・実装・テスト・レビュー・長時間作業を再現可能な形で統制するための再利用可能ハーネスを提供する。

## Design principles

- **共通規則とproject固有規則を分離する。**
- **モデル固有指示を混在させない。** AstraとSol/Lunaはprofileを分け、必要なprofileだけを読む。
- **skillは条件付きで読む。** 常時大量の指示を注入せず、具体的な作業条件に一致したskillだけを有効化する。
- **テストoracleを実装者から保護する。** 実装と検証基準の同時改変を避け、変更はレビュー対象とする。
- **機械的validationを優先する。** 文章上の「完了」ではなく、schema、test、lint、CI、manifestで状態を検証する。
- **下流repoへの展開はprovenance付きで行う。** upstream-managed fileとproject固有fileを区別し、driftを監査可能にする。
- **抽象化は必要なときだけ導入する。** architecture-designやschema-firstは日常の小修正には強制しない。

## Non-goals

- すべてのprojectへ同じframework、DB、service topologyを強制すること。
- モデルの能力不足を大量promptで補うこと。
- AIが変更したテストを無条件で正しいoracleとして受け入れること。

## Source of truth

共通architectureは `docs/harness-architecture.md`、project baselineは `docs/project-baseline.md`、testing governanceは `docs/testing-governance.md`、model routingは `docs/model-profiles.md` を正本とする。
