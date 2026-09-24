# Testing governance

テストは実装の自己採点ではなく、仕様・契約・既知の正解・不変条件に対する独立した証拠として扱う。ただしテスト自体も誤り得るため、固定化ではなく変更権限と根拠を管理する。

## Core rule

テスト失敗を見つけても、実装に合わせて既存の oracle を自動修正しない。まず次のいずれかに分類する。

1. **implementation bug** — 実装が仕様・契約・既知の正解に反する。
2. **test bug** — テストの期待値、前提、fixture、mock、assertion が独立した根拠に反する。
3. **specification unresolved** — 実装とテストのどちらが正しいかを決める上位根拠が不足または矛盾している。

分類できない状態でテストと実装を同時に変更して green にしない。

## Independent oracle

既存テストの意味を変える変更には、実装とは独立した根拠を最低1つ要求する。

- canonical specification / acceptance criterion
- API / schema / protocol contract
- known-good input/output or reference implementation
- domain invariant or mathematically derived property
- independently reproduced bug report or external conformance evidence

「現在の実装がそう動く」「この変更ならCIが通る」は根拠にならない。

## Test asset ownership

Sol はテスト仕様、テストコード、fixture、mock、expected value、golden file、snapshot、threshold / tolerance、grader / evaluation criterion、coverage 設定、CI のテスト実行条件を含むテスト資産の設計・生成・保守・監査に責任を持つ。

Luna はテスト資産を直接変更しない。権限は以下に限定する。

- test / lint / build / evaluation の実行
- 実行結果、失敗分類候補、再現条件、根拠の Issue 報告
- テスト資産の変更案を review 用 PR として提案

Luna が提出したテスト変更 PR は Sol のレビュー・承認なしに merge しない。

## Protected oracle

次は成功条件を変え得るため、通常の実装変更から分離する。

- assertion / expected value
- regression / acceptance / contract tests
- golden files / snapshots / reference outputs
- failure を消す skip / xfail / disable / deletion
- fixture / mock の追加・変更・削除
- threshold / tolerance / grader / evaluation criterion
- coverage 設定
- CI の test selection、filter、実行条件、allow-failure 条件
- 新規 unit test を含むテストコード全般

## Sol / Luna responsibility

**Sol**

- 要求・制約・acceptance criteria の整理
- 実装計画とテスト設計
- テストコードの生成・保守
- protected oracle を含むテスト資産全体の所有と変更判断
- test bug / specification unresolved の裁定
- Luna からのテスト変更 PR のレビュー・採否判断
- 難しいデバッグ、最終レビュー、統合判断

**Luna**

- Sol が境界を定めた実装
- 機械的変更、局所デバッグ
- test / lint / build / evaluation の実行と結果収集
- Issue での結果・失敗・再現条件の報告
- テスト変更が必要と考える場合の review 用 PR 提案

Luna はテストコードや protected oracle を直接改変しない。test bug または specification unresolved を疑った場合は、失敗を保持して根拠と変更案を Sol に返す。

## Failure workflow

```text
Sol: requirements / plan / test design / test asset ownership
  -> Luna: bounded implementation
  -> Luna: run tests
     -> implementation bug: Luna fixes implementation and reruns
     -> suspected test bug: preserve failure, report issue, optionally propose test-only PR
     -> specification unresolved: stop semantic changes and return conflict to Sol
  -> Sol: review evidence and decide whether implementation, test asset, or specification changes
  -> test change, if justified: Sol owns approval and merge decision
  -> final verification against the resulting canonical criterion
```

## Review record

テスト変更の提案には最低限次を残す。

- failing test / criterion
- classification: test bug or specification unresolved
- independent evidence
- why the old oracle or test asset is wrong or obsolete
- exact proposed change
- whether the canonical specification also changes
- regression risk and verification plan

テスト変更の目的は「通すこと」ではなく、「より正しい oracle に更新すること」である。
