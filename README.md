# Codex 開発ハーネス

Codex をソフトウェア開発に使うための、再利用可能な最小構成です。常時読み込むルール、必要時だけ使う task skill、複数 workflow で共有する cross-cutting contract、任意の Git hook を分離しています。

## 構成

```text
codex-dev-harness/
├── .github/workflows/validate.yml     # push/PR時の自動検証
├── AGENTS.md                         # プロジェクト作業の常時ルール
├── .githooks/pre-commit              # 任意の安全チェック
├── .gitattributes / .editorconfig    # 改行・文字コード規約
├── .gitignore / requirements-dev.txt # 除外規則・検証依存関係
├── docs/
│   ├── harness-architecture.md       # 共通契約・改善ゲート
│   └── quality-audit-2026-09-12.md
├── skills/
│   ├── repo-research/SKILL.md
│   ├── reverse-engineering/SKILL.md
│   ├── github-operations/SKILL.md
│   └── self-improvement/SKILL.md     # 評価駆動の自己改善
├── scripts/
│   ├── install-githooks.ps1
│   ├── install-skills.ps1
│   ├── validate-harness.ps1
│   └── validate-skills.py
├── tests/test-pre-commit.sh
└── templates/codex-progress.md
```

## アーキテクチャ

ハーネスは4層に分けます。

1. `AGENTS.md`: 全作業に必要な不変条件だけを常時適用する。
2. `skills/`: 特定条件でのみ読み込む task-specific 手順を置く。
3. `docs/harness-architecture.md`: execution/evaluation/design/optimization の共通契約を定義する。
4. `scripts/`, `tests/`, CI: deterministic な不変条件をモデル判断より先に検証する。

詳細は `docs/harness-architecture.md` を参照してください。

## 導入

対象リポジトリのルートへ、`AGENTS.md`、`.githooks`、`skills`、`scripts`、`templates` をコピーしてください。既存の `AGENTS.md` がある場合は上書きせず、プロジェクト固有ルールを残したまま内容を統合します。

skill を Codex のユーザー skill ディレクトリへ追加する場合は、既存の同名ディレクトリを上書きしない安全なスクリプトを使います。

```powershell
pwsh ./scripts/install-skills.ps1 -CodexSkillsRoot 'C:\Users\<ユーザー名>\.codex\skills'
```

Git hook は任意です。導入すると、コミット前に空白エラーと典型的な秘密情報ファイル・秘密鍵の混入を検査します。プロジェクト固有のテストは hook に埋め込まず、既存の CI やプロジェクトの検証コマンドに任せます。

```powershell
pwsh ./scripts/install-githooks.ps1
```

解除する場合は対象リポジトリで `git config --unset core.hooksPath` を実行してください。

## 検証

WindowsではDockerを使ってskillを検証し、ホスト側のGit Bashでhookの構文・挙動を検証します。

```powershell
pwsh ./scripts/validate-harness.ps1
```

ホストPythonに`requirements-dev.txt`の依存関係が導入済みなら、`-SkipDocker`でも実行できます。GitHub ActionsでもpushとPull Requestごとに同じ不変条件を確認します。

最新の採点基準、検出した問題、改善内容は`docs/quality-audit-2026-09-12.md`に記録しています。

## 自己改善

既存エージェントや workflow を反復改善する場合は `skills/self-improvement/SKILL.md` を使います。

- train/optimization data と hold-out 評価データを分離する。
- 1 iteration の変更範囲を明示する。
- best-so-far を評価前に上書きしない。
- deterministic evaluator を優先する。
- aggregate score だけでなく failure type ごとの退行を確認する。
- 評価が unresolved の候補は採用しない。

## GitHub操作

GitHubへの作成・同期・push・pull・Issue・Pull Requestなどを依頼されたときだけ、`skills/github-operations/SKILL.md`を適用します。通常のローカル開発では自動的にGitHubへ書き込みません。

- 複数ファイルをローカルから同期する場合は、ローカルGitで一つのレビュー可能なコミットを作り、pushします。ファイルごとのAPI更新は使いません。
- リモート上の単一テキストファイルだけを更新する場合は、最新の内容とblob SHAを取得してからGitHub connectorで更新します。同じパスへの書き込みは並列化しません。
- リポジトリの存在確認は検索結果だけで判断せず、正確な`owner/name`またはURLでメタデータを取得します。
- 新規リポジトリ作成機能が接続先にない場合は、認証済みGitHub UIまたはインストール済みの`gh`へフォールバックします。既存のローカルツリーをpushする場合は、README・`.gitignore`・LICENSEの自動初期化をオフにします。
- push後はリモートrefまたはGitHub connectorの読み取りで、対象ブランチとコミットを検証します。

## 運用方針

- 複数モジュールにまたがる実装、設計判断、難しいデバッグ、最終レビューは `gpt-5.6-sol` を優先します。
- 短い探索、ファイル一覧化、機械的な整形、独立した読み取り専用チェックは `gpt-5.6-luna` を優先します。
- ユーザーがモデルを指定した場合はそれを優先し、別モデルへ黙って置き換えません。
- 小さな単一ファイル修正にサブエージェントを使うと、調整コストが勝ちやすいため使いません。
- サブエージェントは総トークンを通常増やしますが、独立した読み取り中心の作業を分離すると主スレッドの文脈汚染と所要時間を抑えられます。効果が調整コストを上回る場合だけ使い、親エージェントが最終判断と編集を担当します。
- 未知のリポジトリを調べるときだけ `repo-research`、挙動解析が必要なときだけ `reverse-engineering` を使います。通常の実装でこれらを自動実行しません。
- 長い作業では `templates/codex-progress.md` をプロジェクトの既存の進捗ファイルへ統合し、次の作業単位・検証結果・未解決点を残します。

## 設計根拠

構成を更新するときは、まず次の一次資料を確認してください。

- [OpenAI Models](https://developers.openai.com/api/docs/models): Sol を複雑な専門作業、Luna をコスト重視の高頻度作業として位置づけています。
- [OpenAI: Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md): 指示の探索順、現在地に近い指示の優先、既定の32 KiB上限、読込確認方法を反映しています。
- [OpenAI: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): subagentの総トークン増加、主スレッドの文脈分離、読み取り中心の並列化という使い分けを反映しています。
- [OpenAI Model guidance](https://developers.openai.com/api/docs/guides/latest-model): サブエージェントの委譲条件を明示し、テスト・検証の量を作業に合わせて調整する方針を示しています。資料内の具体例は Astra 向けですが、本ハーネスではユーザー指定どおり Sol/Luna に適用しています。
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): 初期化、作業の小分け、構造化した引き継ぎという考え方を採用しています。
- [Anthropic: Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps): planner/generator/evaluator の分離と、複雑さを必要最小限に保つ考え方を、常時機構ではなく必要時の運用ルールへ落とし込んでいます。

## 適用範囲

このハーネスは開発作業の判断と記録を整えるものであり、デプロイ、外部サービスへの書き込み、課金の発生、データ削除、アクセス制御の回避を自動許可するものではありません。そうした操作は、依頼の範囲と承認を個別に確認してください。
