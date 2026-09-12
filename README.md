# Codex 開発ハーネス

Codex をソフトウェア開発に使うための、再利用可能な最小構成です。常時読み込むルールと、必要なときだけ使う調査 skill、任意で有効化する Git hook を分離しています。

## 構成

```text
codex-dev-harness/
├── AGENTS.md                         # プロジェクト作業の常時ルール
├── .githooks/pre-commit              # 任意の安全チェック
├── skills/
│   ├── repo-research/SKILL.md        # 未知のリポジトリ・仕様の事前調査
│   ├── reverse-engineering/SKILL.md  # 許可された対象の挙動解析
│   └── github-operations/SKILL.md    # 明示依頼時のGitHub同期・操作
├── scripts/
│   ├── install-githooks.ps1
│   └── install-skills.ps1
└── templates/codex-progress.md       # 長時間・複数セッション作業の引き継ぎ用
```

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
- 並列化で時間または総トークンを節約できる、独立した読み取り専用の調査だけをサブエージェントへ委譲します。親エージェントが最終判断と編集を担当します。
- 未知のリポジトリを調べるときだけ `repo-research`、挙動解析が必要なときだけ `reverse-engineering` を使います。通常の実装でこれらを自動実行しません。
- 長い作業では `templates/codex-progress.md` をプロジェクトの既存の進捗ファイルへ統合し、次の作業単位・検証結果・未解決点を残します。

## 設計根拠

構成を更新するときは、まず次の一次資料を確認してください。

- [OpenAI Models](https://developers.openai.com/api/docs/models): Sol を複雑な専門作業、Luna をコスト重視の高頻度作業として位置づけています。
- [OpenAI Model guidance](https://developers.openai.com/api/docs/guides/latest-model): サブエージェントの委譲条件を明示し、テスト・検証の量を作業に合わせて調整する方針を示しています。資料内の具体例は Astra 向けですが、本ハーネスではユーザー指定どおり Sol/Luna に適用しています。
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): 初期化、作業の小分け、構造化した引き継ぎという考え方を採用しています。
- [Anthropic: Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps): planner/generator/evaluator の分離と、複雑さを必要最小限に保つ考え方を、常時機構ではなく必要時の運用ルールへ落とし込んでいます。

## 適用範囲

このハーネスは開発作業の判断と記録を整えるものであり、デプロイ、外部サービスへの書き込み、課金の発生、データ削除、アクセス制御の回避を自動許可するものではありません。そうした操作は、依頼の範囲と承認を個別に確認してください。
