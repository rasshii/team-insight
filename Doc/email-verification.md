# Email Verification Feature

## Overview

Team Insightでは、ユーザーのメールアドレスを検証する機能を提供しています。この機能により、通知やレポートを確実にユーザーに届けることができます。

## Features

### Backend

1. **メール検証フィールド**
   - `is_email_verified`: メールアドレスが検証済みかどうか
   - `email_verification_token`: 検証用トークン
   - `email_verification_token_expires`: トークンの有効期限
   - `email_verified_at`: 検証完了日時

2. **API エンドポイント**
   - `POST /api/v1/auth/email/verify`: 検証メールを送信
   - `POST /api/v1/auth/email/verify/confirm`: メールアドレスを検証
   - `POST /api/v1/auth/email/verify/resend`: 検証メールを再送信

3. **メールサービス**
   - HTMLテンプレートによる美しいメールデザイン
   - 検証メールと検証成功通知メールの送信

### Frontend

1. **検証ページ** (`/auth/verify-email`)
   - トークンを使用したメールアドレスの検証
   - 検証成功/失敗のフィードバック
   - 自動リダイレクト

2. **プロフィール設定** (`/settings/profile`)
   - メールアドレスの更新
   - 検証状態の表示
   - 検証メールの再送信

3. **メール検証バナー**
   - 未検証のユーザーに対する通知
   - 検証メールの再送信ボタン

## Configuration

### 環境変数 (.env)

```env
# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@teaminsight.dev
SMTP_FROM_NAME=Team Insight
SMTP_TLS=true
SMTP_SSL=false
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS=24
```

### Gmail App Password設定

Gmailを使用する場合、アプリパスワードが必要です：

1. Googleアカウントで2段階認証を有効化
2. [アプリパスワード](https://myaccount.google.com/apppasswords)を生成
3. 生成されたパスワードを`SMTP_PASSWORD`に設定

## User Flow

1. **新規ユーザー登録時**
   - Backlog OAuth認証でログイン
   - メールアドレスが設定されている場合、未検証状態で保存

2. **メールアドレス設定/更新**
   - プロフィール設定でメールアドレスを入力
   - 検証メールが送信される
   - メール内のリンクをクリック

3. **検証プロセス**
   - 検証リンクをクリック
   - `/auth/verify-email?token=xxx`にアクセス
   - トークンが有効な場合、メールアドレスが検証済みに更新
   - ダッシュボードにリダイレクト

## Testing

### メール送信テスト

```bash
# バックエンドコンテナに入る
make backend-shell

# テストスクリプトを実行
python scripts/test_email_verification.py
```

### API テスト

```bash
# 検証メール送信（要認証）
curl -X POST http://localhost:8000/api/v1/auth/email/verify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# メール検証確認
curl -X POST http://localhost:8000/api/v1/auth/email/verify/confirm \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_VERIFICATION_TOKEN"}'
```

## Security Considerations

1. **トークンセキュリティ**
   - 32バイトのランダムトークン（`secrets.token_urlsafe`使用）
   - 24時間の有効期限
   - 使用後は即座に無効化

2. **メールアドレスの重複チェック**
   - 他のユーザーが検証済みの同じメールアドレスは使用不可
   - 未検証のメールアドレスは上書き可能

3. **レート制限**
   - 現在は実装されていません（今後の改善点）

## Future Improvements

1. **レート制限の実装**
   - メール送信回数の制限
   - IPアドレスベースの制限

2. **メールテンプレートの国際化**
   - 多言語対応
   - ユーザーの言語設定に基づくメール送信

3. **メール配信追跡**
   - 開封率、クリック率の追跡
   - バウンスメールの処理

4. **代替通知チャネル**
   - SMS検証
   - Slack/Teams通知