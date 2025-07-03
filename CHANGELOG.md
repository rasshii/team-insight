# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- メール/パスワード認証機能の実装
- メール検証機能（検証メール送信、再送信）
- 統一的なエラーハンドリング（AppException、エラーレスポンス形式）
- セキュリティユーティリティ（パスワード検証、トークン生成、レート制限）
- 構造化ログとセキュリティ対応（機密データマスキング）
- フロントエンドのエラー型定義（ApiError、ErrorResponse）
- TanStack Query v5の全面採用
- キャッシュミドルウェアの有効化

### Changed
- バックエンドのエラーハンドリングを統一（HTTPException → AppException）
- auth.pyのリファクタリング（共通処理の抽出、レスポンス形式統一）
- React QueryフックでのエラーハンドリングをgetApiErrorMessageで統一
- ログシステムを構造化ログに移行
- README.mdの更新（現在の実装状況を反映）
- CLAUDE.mdの更新（最新のアーキテクチャ決定事項を反映）

### Fixed
- 認証エラーレスポンスの一貫性
- フロントエンドのAPIエラーハンドリング

### Security
- パスワードポリシーの強化（大文字・小文字・数字・特殊文字必須）
- レート制限の実装準備
- ログ内の機密データ自動マスキング

## [0.1.0] - 2024-06-XX

### Added
- 初期リリース
- Backlog OAuth認証
- RBAC（ロールベースアクセス制御）
- プロジェクト管理機能
- 基本的なダッシュボードUI
- Docker Compose開発環境