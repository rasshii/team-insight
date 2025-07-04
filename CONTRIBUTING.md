# Team Insight 貢献ガイド

Team Insightプロジェクトへの貢献を検討いただき、ありがとうございます！このガイドでは、プロジェクトへの貢献方法について説明します。

## 行動規範

プロジェクトに参加する前に、以下のガイドラインをお読みください：

- すべての参加者に対して敬意を持って接してください
- 建設的なフィードバックを心がけてください
- 多様性を尊重し、包括的なコミュニティを目指しましょう

## 貢献の方法

### バグ報告

バグを発見した場合は、GitHubのIssuesで報告してください。報告の際は以下の情報を含めてください：

1. **環境情報**
   - OS（Windows/Mac/Linux）とバージョン
   - Dockerバージョン
   - ブラウザとバージョン

2. **再現手順**
   - バグを再現するための具体的な手順
   - 期待される動作
   - 実際の動作

3. **ログ情報**
   - エラーメッセージ
   - `make logs`の出力（必要に応じて）

### 機能提案

新機能の提案は大歓迎です！以下の点を含めてIssueを作成してください：

- 提案する機能の概要
- なぜその機能が必要か
- 想定される使用例
- 実装のアイデア（あれば）

### プルリクエスト

#### 開発環境のセットアップ

1. リポジトリをフォーク
2. ローカル環境にクローン
   ```bash
   git clone https://github.com/YOUR_USERNAME/team-insight.git
   cd team-insight
   ```

3. 開発環境を起動
   ```bash
   make setup  # 初回のみ
   make start
   ```

#### ブランチ運用

- `main`ブランチから新しいブランチを作成
- ブランチ名は以下の形式を推奨：
  - `feature/機能名` - 新機能
  - `fix/バグ名` - バグ修正
  - `docs/ドキュメント名` - ドキュメント更新
  - `refactor/対象名` - リファクタリング

```bash
git checkout -b feature/awesome-feature
```

#### コーディング規約

##### Python（バックエンド）

- PEP 8準拠
- 型ヒント必須
- Blackフォーマッター使用
- docstring記載（Google形式推奨）

```python
def calculate_velocity(tasks: List[Task], days: int) -> float:
    """チームのベロシティを計算する
    
    Args:
        tasks: 完了したタスクのリスト
        days: 期間の日数
        
    Returns:
        1日あたりの平均ストーリーポイント
    """
    # 実装
```

##### TypeScript（フロントエンド）

- strictモード有効
- ESLint + Prettier設定に従う
- React Hooksのルールを遵守
- コンポーネントはアロー関数で定義

```typescript
interface Props {
  title: string
  onClose: () => void
}

export const MyComponent: FC<Props> = ({ title, onClose }) => {
  // 実装
}
```

#### コミットメッセージ

Conventional Commits形式を使用：

```
<type>(<scope>): <subject>

<body>

<footer>
```

例：
```
feat(auth): Backlog OAuth認証を実装

- OAuth 2.0フローの実装
- トークンリフレッシュ機能
- エラーハンドリング

Closes #123
```

タイプ：
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: コードスタイルの変更
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド関連・補助ツール

#### テスト

- 新機能・バグ修正には必ずテストを追加
- バックエンドテスト実行：
  ```bash
  make test
  ```
- 型チェック：
  ```bash
  make type-check
  ```
- Lint実行：
  ```bash
  make lint
  ```

#### プルリクエストのチェックリスト

- [ ] コーディング規約に従っている
- [ ] テストを追加・更新した
- [ ] `make test`が成功する
- [ ] `make lint`でエラーがない
- [ ] 必要に応じてドキュメントを更新
- [ ] コミットメッセージが規約に従っている
- [ ] CLAUDE.mdなど個人用ファイルが含まれていない

### ドキュメント

ドキュメントの改善も重要な貢献です：

- タイポや文法の修正
- わかりにくい説明の改善
- 使用例の追加
- 翻訳（事前に相談してください）

## 開発のヒント

### Makefileコマンド

主要なコマンド一覧：
```bash
make help         # ヘルプ表示
make start        # 全サービス起動
make stop         # 全サービス停止
make logs         # ログ表示
make test         # テスト実行
make lint         # Lint実行
make migrate      # DBマイグレーション
```

### デバッグ

- バックエンドデバッグ：
  ```bash
  make backend-shell
  # コンテナ内でPythonデバッガー使用可能
  ```

- フロントエンドデバッグ：
  - Chrome DevToolsを使用
  - Redux DevTools拡張機能推奨

### よくある問題

1. **ポート競合**
   - 3000, 8000, 5432, 6379番ポートを確認
   - 他のサービスを停止するか、ポート番号を変更

2. **認証エラー**
   - Backlog OAuth設定を確認
   - NEXT_PUBLIC_API_URLが`http://localhost`（ポート番号なし）

3. **マイグレーションエラー**
   - `make migrate-down`で前の状態に戻す
   - `make migrate-history`で履歴確認

## レビュープロセス

1. プルリクエスト作成後、自動チェックが実行されます
2. コードレビュアーがレビューを行います
3. 必要に応じて修正を依頼します
4. 承認後、メインブランチにマージされます

## リリースプロセス

- セマンティックバージョニング（SemVer）を使用
- CHANGELOGを更新
- GitHubリリースを作成

## コミュニティ

- 質問や議論はGitHub Discussionsで
- 緊急の問題はIssuesで報告
- 定期的なコントリビューターミーティング（予定）

## ライセンス

貢献いただいたコードは、プロジェクトと同じMITライセンスで公開されます。

## 謝辞

Team Insightプロジェクトへの貢献に感謝します！あなたの貢献がプロジェクトをより良いものにします。

何か質問があれば、お気軽にIssueやDiscussionsでお聞きください。