# Team Insight

> Backlog のデータを活用したチーム分析ツール。チームのパフォーマンスを可視化し、ボトルネックの特定や生産性の向上を支援します。

## 📋 目次

- [概要](#概要)
- [技術スタック](#技術スタック)
- [セットアップ](#セットアップ)
- [開発ガイド](#開発ガイド)
  - [Makefile コマンド一覧](#makefileコマンド一覧)
  - [バックエンド開発](#バックエンド開発)
  - [フロントエンド開発](#フロントエンド開発)
  - [データベース管理](#データベース管理)
  - [テスト](#テスト)
- [アーキテクチャ](#アーキテクチャ)
- [トラブルシューティング](#トラブルシューティング)
- [コントリビューション](#コントリビューション)

## 概要

Team Insight は、Backlog API と連携してチームの開発プロセスを分析・可視化する生産性向上プラットフォームです。個人、プロジェクト、組織レベルでの包括的なダッシュボードを提供し、データに基づいた意思決定を支援します。

### 主な機能

#### 実装済み ✅
- **Backlog OAuth 認証**: セキュアな OAuth2.0 認証と JWT セッション管理（特定スペース専用）
- **RBAC（ロールベースアクセス制御）**: プロジェクト単位での柔軟な権限管理
- **管理画面**: ユーザー管理UI（/admin/users）でGUIによるロール管理が可能
  - ユーザー一覧表示（グローバル/プロジェクトロールの区別表示）
  - Backlogユーザー一括インポート機能
  - ユーザーステータス管理（ログイン可/不可）
- **個人ダッシュボード**: タスク情報とパフォーマンス指標の可視化（実データ連携済み）
- **プロジェクト管理**: プロジェクト情報の取得と管理
- **Backlog同期**: 
  - プロジェクトとタスクデータの自動同期
  - ユーザー一括インポート（全プロジェクトから収集）
  - 定期同期スケジューラー（日次ユーザー同期、6時間ごとのプロジェクト同期）
- **データ可視化**: D3.js によるボトルネック分析とスループット表示
- **ヘルスチェック**: システム稼働状況の監視
- **キャッシュシステム**: Redis によるAPI レスポンスのキャッシュ（有効化済み）
- **統一エラーハンドリング**: 構造化されたエラーレスポンスとロギング
- **セキュリティ強化**: レート制限、機密データマスキング
- **自動トークンリフレッシュ**: Backlog OAuth トークンの自動更新機能
- **レポート配信システム**: 定期的な分析レポートのメール配信（APScheduler使用）
- **チーム管理機能**: Team Insight独自のチーム概念
  - チームの作成・編集・削除（/admin/teams）
  - チームメンバー管理とロール設定（チームリーダー/メンバー）
  - チームごとの統計情報表示
  - ユーザー一覧でのチーム・プロジェクトフィルター
- **チーム生産性ダッシュボード**: チームごとの生産性分析（/teams）
  - メンバー別パフォーマンス表示
  - タスク分配の可視化
  - 生産性推移グラフ
  - チームアクティビティタイムライン

#### 開発中 🚧
- **プロジェクトダッシュボード**: プロジェクト全体の分析機能
- **組織ダッシュボード**: 組織全体の生産性分析
- **高度な分析機能**: ボトルネック検出アルゴリズム（実データとの連携）

#### 計画中 📋
- **通知システム**: ボトルネックアラートと改善提案
- **予測分析**: AI を活用した将来予測
- **WebSocket 統合**: リアルタイム更新
- **レポート生成**: PDF/Excel形式でのレポート出力

## 技術スタック

### バックエンド

- **FastAPI** (0.109.2): 高速で型安全な Web API フレームワーク
- **Python** (3.11): モダンな Python ランタイム
- **SQLAlchemy** (2.0): 最新の ORM とデータベース管理
- **PostgreSQL** (15): メインデータベース（team_insight スキーマ使用）
- **Redis** (7): キャッシュとセッション管理（パスワード認証付き）
- **Alembic**: データベースマイグレーション
- **httpx**: 非同期 HTTP クライアント（Backlog API 連携用）
- **python-jose[cryptography]**: JWT トークン処理
- **passlib[bcrypt]**: パスワードハッシュ化

### フロントエンド

- **Next.js** (14): App Router を使用した React フレームワーク
- **React** (18): UI ライブラリ
- **TypeScript** (5): 型安全な開発
- **Redux Toolkit**: グローバル状態管理（ユーザー認証情報のみ）
- **TanStack Query** (v5): サーバー状態管理とデータフェッチング
- **shadcn/ui**: Radix UI ベースのコンポーネントライブラリ
- **Tailwind CSS** (v3): ユーティリティファースト CSS
- **D3.js**: データ可視化ライブラリ
- **Yarn v4 (Berry)**: パッケージ管理（Corepack 使用）
- **react-hook-form + zod**: フォーム処理とバリデーション
- **axios**: HTTP クライアント（統一されたエラーハンドリング付き）

### インフラ

- **Docker & Docker Compose**: コンテナ化と開発環境
- **Nginx**: リバースプロキシ（API ルーティング）
- **Node.js v22 LTS**: フロントエンドランタイム
- **Make**: 開発タスクの自動化

## セットアップ

### 前提条件

- Docker Desktop
- Git
- Backlog OAuth アプリケーションの登録

### 初回セットアップ

1. **リポジトリのクローン**

```bash
git clone https://github.com/your-org/team-insight.git
cd team-insight
```

2. **環境変数の設定**

バックエンド環境変数 (`backend/.env`):

```env
# データベース設定
DATABASE_URL=postgresql://teaminsight:teaminsight@postgres:5432/teaminsight

# Redis設定
REDIS_URL=redis://redis:6379/0

# セキュリティ
SECRET_KEY=your-secret-key-here  # 32文字以上の強力なキーを使用

# Backlog OAuth設定
BACKLOG_CLIENT_ID=your-client-id
BACKLOG_CLIENT_SECRET=your-client-secret
BACKLOG_REDIRECT_URI=http://localhost/auth/callback
BACKLOG_SPACE_KEY=your-space-key

# SMTP設定（開発環境はMailHogが自動設定されます）
# プロダクション環境の場合は以下を設定
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# SMTP_FROM_EMAIL=noreply@teaminsight.dev
# SMTP_FROM_NAME=Team Insight
```

3. **セットアップスクリプトの実行**

```bash
# 実行権限を付与
chmod +x setup.sh

# セットアップ実行
./setup.sh
```

または

```bash
make setup
```

4. **アプリケーションへのアクセス**

- フロントエンド: http://localhost (Nginx経由)
- バックエンド API: http://localhost/api (Nginx経由)
- API ドキュメント: http://localhost/api/v1/docs (Nginx経由)
- MailHog Web UI: http://localhost:8025 (開発環境のメール確認)

## 開発ガイド

### Makefile コマンド一覧

#### 基本操作

```bash
make start          # 開発サーバーを起動
make stop           # 開発サーバーを停止
make restart        # 開発サーバーを再起動
make status         # サービスの状態を確認
make logs           # 全サービスのログを表示
```

#### データベース操作

```bash
make db-shell      # PostgreSQLに接続
make db-backup     # データベースのバックアップを作成
make db-restore    # バックアップから復元
make migrate       # 最新のマイグレーションを適用
make migrate-rollback  # 最後のマイグレーションをロールバック
```

#### 開発用コマンド

```bash
make test          # バックエンドテストを実行
make test-frontend # フロントエンドテストを実行
make test-all      # 全てのテストを実行
make test-coverage # カバレッジレポート付きでテスト実行
make lint          # コードの静的解析を実行
make format        # コードをフォーマット
make clean         # コンテナとボリュームを削除
```

#### TypeScript型生成

```bash
make update-types   # OpenAPIスキーマからTypeScript型を生成
make generate-types # 型生成のみ（バックエンド起動確認なし）
make dev-sync       # マイグレーション + 型生成を一括実行
```

#### Redis操作

```bash
make redis-keys     # 全Redisキー一覧を表示
make redis-cli      # Redis CLIに接続
```

#### Nginx操作

```bash
make nginx-access-log # Nginxアクセスログを表示
make nginx-reload     # Nginx設定をリロード
```

#### コンテナ操作

```bash
make build         # 全イメージをビルド
make rebuild       # 全イメージを再ビルド
make ps            # コンテナの状態を表示
make shell         # バックエンドコンテナのシェルに入る
```

#### ロール管理

Team Insightは**独自のロールベースアクセス制御（RBAC）システム**を実装しており、Backlogのロールとは独立して動作します。

**Team Insight固有のロール**:
- **ADMIN（管理者）**: システム全体の管理権限、ユーザー管理、全プロジェクトへのアクセス
- **PROJECT_LEADER（プロジェクトリーダー）**: 担当プロジェクトの管理権限、メンバー管理
- **MEMBER（メンバー）**: 所属プロジェクトへの参照権限

**Backlogロールとの関係**:
- Team InsightのロールはBacklogのロール（管理者、一般ユーザー等）とは**完全に独立**
- Backlogでの権限に関わらず、Team Insight内で個別に権限を設定可能
- この設計により、Team Insight固有の機能（レポート配信、ダッシュボード管理等）に対する柔軟な権限制御を実現

**管理方法**:

**管理画面（GUI）**: http://localhost/admin/users でユーザー・ロール管理が可能です。

**CLIツール（並行して利用可能）**:
```bash
make set-admin EMAIL=user@example.com       # ユーザーを管理者に設定
make set-role EMAIL=user@example.com ROLE=PROJECT_LEADER  # ロール設定
make list-users     # 全ユーザーとロールを一覧表示
make remove-role EMAIL=user@example.com ROLE=MEMBER # ロール削除
make init-admin     # 環境変数から初期管理者を設定
```

#### ユーザーステータス管理

Team Insightでは、ユーザーのログイン可否を`is_active`フラグで管理しています。

**ステータスの種類**:
- **ログイン可（is_active = true）**: ユーザーがシステムにログインできる状態
- **ログイン不可（is_active = false）**: ユーザーがシステムにログインできない状態

**使用場面**:
1. **退職・休職時**: 従業員が退職または休職した際に、一時的にアクセスを停止
2. **セキュリティ対応**: 不正アクセスの疑いがある場合の緊急アカウント停止
3. **ライセンス管理**: 利用人数に制限がある場合の調整
4. **一時的な利用停止**: プロジェクト終了後もデータ履歴は残したいが、アクセスは制限したい場合

**管理方法**:
- 管理画面（http://localhost/admin/users）から各ユーザーのステータスを変更可能
- フィルター機能で「ログイン可」「ログイン不可」のユーザーを絞り込み表示

**注意事項**:
- Backlog OAuth認証を使用しているため、Backlog側でもアカウントが有効である必要があります
- このフラグはTeam Insight側での追加的なアクセス制御として機能します

### バックエンド開発

#### ディレクトリ構造

```
backend/
├── app/
│   ├── api/          # APIエンドポイント
│   │   └── v1/       # APIバージョン1
│   ├── core/         # 設定とセキュリティ
│   ├── db/           # データベース関連
│   ├── models/       # SQLAlchemyモデル
│   ├── schemas/      # Pydanticスキーマ
│   ├── services/     # ビジネスロジック
│   └── main.py       # アプリケーションエントリーポイント
├── alembic/          # データベースマイグレーション
└── tests/            # テストコード
```

#### 新しい API エンドポイントの追加

1. **スキーマの定義** (`app/schemas/your_feature.py`):

```python
from pydantic import BaseModel, Field
from typing import Optional

class YourFeatureResponse(BaseModel):
    """レスポンススキーマ"""
    id: int = Field(..., description="ID")
    name: str = Field(..., description="名前")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "サンプル"
            }
        }
```

2. **モデルの定義** (`app/models/your_feature.py`):

```python
from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class YourFeature(BaseModel):
    """データベースモデル"""
    __tablename__ = "your_features"
    __table_args__ = {"schema": "team_insight"}

    # idは BaseModel で定義済み
    name = Column(String(255), nullable=False)
    # created_at, updated_at も BaseModel で定義済み
```

3. **サービスの実装** (`app/services/your_feature_service.py`):

```python
from sqlalchemy.orm import Session
from app.models.your_feature import YourFeature

class YourFeatureService:
    """ビジネスロジック"""

    async def get_all(self, db: Session):
        """すべてのデータを取得"""
        return db.query(YourFeature).all()

your_feature_service = YourFeatureService()
```

4. **API エンドポイントの実装** (`app/api/v1/your_feature.py`):

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.your_feature import YourFeatureResponse
from app.services.your_feature_service import your_feature_service
from app.core.security import get_current_active_user

router = APIRouter(prefix="/your-feature", tags=["your-feature"])

@router.get("/", response_model=List[YourFeatureResponse])
async def get_your_features(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """データ一覧を取得"""
    return await your_feature_service.get_all(db)
```

5. **ルーターの登録** (`app/api/v1/__init__.py`):

```python
from .your_feature import router as your_feature_router
# 既存のインポートに追加

api_router.include_router(your_feature_router)
```

### フロントエンド開発

#### ディレクトリ構造

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── (routes)/     # ページコンポーネント
│   │   ├── api/          # APIルート
│   │   └── layout.tsx    # ルートレイアウト
│   ├── components/       # 再利用可能なコンポーネント
│   │   └── ui/          # shadcn/uiコンポーネント
│   ├── hooks/           # カスタムフック
│   ├── services/        # APIクライアント
│   ├── store/           # Redux store
│   │   └── slices/      # Redux slices
│   └── types/           # TypeScript型定義
```

#### 新しいページの追加

1. **型定義** (`src/types/your-feature.ts`):

```typescript
export interface YourFeature {
  id: number;
  name: string;
}
```

2. **API サービス** (`src/services/your-feature.service.ts`):

```typescript
import axios from "axios";
import { YourFeature } from "@/types/your-feature";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class YourFeatureService {
  async getAll(): Promise<YourFeature[]> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/your-feature`);
    return response.data;
  }
}

export const yourFeatureService = new YourFeatureService();
```

3. **React Query Hook** (`src/hooks/queries/useYourFeature.ts`):

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { yourFeatureService } from '@/services/your-feature.service'
import { YourFeature } from '@/types/your-feature'
import { queryKeys } from '@/lib/react-query'
import { useToast } from '@/hooks/use-toast'

export const useYourFeatures = () => {
  return useQuery({
    queryKey: queryKeys.yourFeature.all,
    queryFn: () => yourFeatureService.getAll(),
    staleTime: 5 * 60 * 1000, // 5分
  })
}

export const useCreateYourFeature = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  
  return useMutation({
    mutationFn: yourFeatureService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.yourFeature.all })
      toast({ title: '作成しました' })
    },
    onError: (error) => {
      toast({ 
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive'
      })
    }
  })
}
```

4. **ページコンポーネント** (`src/app/your-feature/page.tsx`):

```typescript
"use client";

import { useYourFeatures } from "@/hooks/queries/useYourFeature";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function YourFeaturePage() {
  const { data: items, isLoading, error } = useYourFeatures();

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <Skeleton className="h-[200px] w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Your Feature</h1>
      <div className="grid gap-4">
        {items?.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <CardTitle>{item.name}</CardTitle>
            </CardHeader>
            <CardContent>{/* コンテンツ */}</CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

### TypeScript型の自動生成

Team InsightではOpenAPIスキーマからTypeScript型を自動生成し、フロントエンドとバックエンド間の型の整合性を保証しています。

#### 仕組み

1. **バックエンド**: FastAPIが自動的にOpenAPIスキーマを生成（`/api/v1/openapi.json`）
2. **型生成**: `openapi-typescript`がスキーマからTypeScript型定義を生成
3. **フロントエンド**: 生成された型を使用してタイプセーフな開発

#### 使用方法

```bash
# TypeScript型を生成（バックエンドが起動している必要があります）
make update-types

# 型生成のみ（起動確認なし）
make generate-types

# 開発ワークフロー：マイグレーションと型生成を一括実行
make dev-sync
```

#### 実装例

1. **バックエンドでPydanticスキーマを定義**:

```python
# backend/app/schemas/your_feature.py
from pydantic import BaseModel, Field
from typing import Literal

class YourFeatureResponse(BaseModel):
    """レスポンススキーマ"""
    id: int = Field(..., description="ID")
    name: str = Field(..., description="名前")
    status: Literal["active", "inactive"] = Field(..., description="ステータス")
```

2. **エンドポイントでスキーマを使用**:

```python
# backend/app/api/v1/your_feature.py
@router.get("/", response_model=List[YourFeatureResponse])
async def get_your_features():
    """データ一覧を取得"""
    return await your_feature_service.get_all()
```

3. **型を生成**:

```bash
make update-types
```

4. **フロントエンドで自動生成された型を使用**:

```typescript
// frontend/src/services/your-feature.service.ts
import type { components } from "@/types/api";

// 自動生成された型を使用
type YourFeatureResponse = components["schemas"]["YourFeatureResponse"];

export async function getYourFeatures(): Promise<YourFeatureResponse[]> {
    const response = await axios.get("/api/v1/your-feature");
    return response.data;
}
```

#### メリット

- **型の一元管理**: バックエンドのPydanticモデルが唯一の真実の源
- **自動同期**: API変更時に型定義が自動的に更新
- **型安全性**: コンパイル時に型の不整合を検出
- **開発効率**: 手動での型定義が不要

#### 注意事項

- 型生成時はバックエンドが起動している必要があります
- 生成された型ファイル（`src/types/api.d.ts`）は直接編集しないでください
- APIを変更した後は必ず`make update-types`を実行してください

### データベース管理

#### マイグレーション

```bash
# 新しいマイグレーションの作成
make migration-create name="migration_name"

# マイグレーションの適用
make migrate

# マイグレーションのロールバック
make migrate-rollback

# マイグレーション履歴の確認
make migration-history
```

#### バックアップとリストア

```bash
# バックアップの作成
make db-backup

# バックアップからの復元
make db-restore

# バックアップ一覧の表示
make db-backup-list
```

### テスト

#### バックエンドテスト

1. **テストファイルの作成** (`backend/tests/test_your_feature.py`):

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_your_features():
    """データ一覧取得のテスト"""
    response = client.get("/api/v1/your-feature")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

2. **テストの実行**:

```bash
# すべてのテストを実行
make test

# 特定のテストファイルを実行
make test path="tests/test_your_feature.py"

# カバレッジレポート付きで実行
make test-coverage
```

#### フロントエンドテスト

1. **コンポーネントテスト** (`frontend/src/__tests__/YourFeature.test.tsx`):

```typescript
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { store } from "@/store";
import YourFeaturePage from "@/app/your-feature/page";

describe("YourFeaturePage", () => {
  it("renders without crashing", () => {
    render(
      <Provider store={store}>
        <YourFeaturePage />
      </Provider>
    );

    expect(screen.getByText("Your Feature")).toBeInTheDocument();
  });
});
```

2. **テストの実行**:

```bash
# フロントエンドコンテナ内でテストを実行
docker-compose exec frontend yarn test

# ローカルでテストを実行
cd frontend
yarn test

# ウォッチモードで実行
yarn test:watch

# 特定のテストファイルを実行
yarn test src/services/__tests__/health.service.test.ts

# カバレッジレポート付きで実行（設定が必要）
# yarn test:coverage
```

> 注意: プロジェクトではYarn v4 (Berry)を使用してテストを実行します。

**詳細なテストガイド**: フロントエンドテストの詳細（setupTests.ts、モックの使用方法、ベストプラクティス）については、[frontend/docs/testing.md](frontend/docs/testing.md)を参照してください。

## アーキテクチャ

### システム構成図

```mermaid
graph TB
    subgraph "Frontend"
        A[React App]
        B[Redux Store]
        C[API Client]
    end

    subgraph "Backend"
        D[FastAPI]
        E[Business Logic]
        F[ORM Layer]
    end

    subgraph "Infrastructure"
        G[PostgreSQL]
        H[Redis]
        I[Nginx]
    end

    subgraph "External"
        J[Backlog API]
    end

    A --> B
    B --> C
    C --> I
    I --> D
    D --> E
    E --> F
    F --> G
    E --> H
    E --> J
```

## トラブルシューティング

### よくある問題と解決方法

#### ポート競合エラー

```bash
# 使用中のポートを確認
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド

# プロセスを終了
kill -9 [PID]
```

#### データベース接続エラー

```bash
# PostgreSQLコンテナの状態を確認
docker-compose ps postgres

# ログを確認
docker-compose logs postgres

# データベースを再作成
docker-compose down -v
docker-compose up -d
```

#### 認証エラー

- Backlog OAuth 設定を確認
- リダイレクト URI が正しいか確認
- 環境変数が正しく設定されているか確認

### 開発のヒント

1. **API ドキュメント**: http://localhost/api/v1/docs で対話的に API をテスト（Nginx経由）
2. **Redux DevTools**: ブラウザ拡張機能で状態管理をデバッグ
3. **Docker logs**: `docker-compose logs -f [service]` でリアルタイムログ確認
4. **Hot Reload**: フロントエンド・バックエンドともに自動リロード対応
5. **型の自動生成**: API変更後は必ず`make update-types`を実行して型定義を更新

## APIアクセスとネットワーク構成

### 開発環境でのAPIアクセス

開発環境では、Nginxがリバースプロキシとして動作し、すべてのHTTPトラフィックを適切なサービスにルーティングします：

```
ブラウザ → http://localhost → Nginx → 各サービス
  └─ /         → Frontend (Next.js) :3000
  └─ /api      → Backend (FastAPI) :8000
  └─ /health   → Backend (FastAPI) :8000
  └─ /admin    → Backend (FastAPI) :8000
  └─ /graphql  → Backend (FastAPI) :8000
```

### 環境変数の設定

フロントエンドからAPIへのアクセスは環境変数で制御されます：

- **開発環境**: `NEXT_PUBLIC_API_URL=http://localhost`
- **本番環境**: `NEXT_PUBLIC_API_URL=https://your-domain.com`

### テスト環境での注意点

テストファイルでは、環境変数をモックして`http://localhost:8000`を直接使用しています：

```typescript
// テスト環境でのモック
jest.mock("@/config/env", () => ({
  env: {
    get: jest.fn().mockReturnValue("http://localhost:8000"),
  },
}));
```

これは実際のNginxを経由せずに、バックエンドAPIを直接モックするためです。

## トラブルシューティング

### 認証関連

#### 別のBacklogスペースでログイン中の場合

Team Insightは特定のBacklogスペース（設定されたスペース）専用のツールです。別のBacklogスペースのアカウントでログインしている場合、以下の手順で対処してください：

1. **エラーメッセージが表示される場合**
   - ログイン時に「このBacklogスペースへのアクセス権限がありません」というエラーが表示されます
   - これは正常な動作で、別のスペースのアカウントでログインしているためです

2. **対処方法**
   別のBacklogアカウントでログインする必要がある場合は、以下のいずれかの方法をご利用ください：
   - **プライベートブラウジング（推奨）**: 新しいプライベート/シークレットウィンドウでアクセス
   - **別のブラウザを使用**: Chrome、Firefox、Safari など異なるブラウザでアクセス
   - **Cookieをクリア**: ブラウザの設定から nulab.com のCookieを削除してからアクセス

3. **技術的な制約**
   - Backlog/Nulabの認証はドメインが異なるため、事前に別スペースでのログイン状態を検知できません
   - そのため、認証後にスペースの確認を行い、適切なエラーメッセージを表示します

#### CORSエラーについて

Nulab認証ページで以下のようなエラーが表示されることがあります：
```
Unsafe attempt to load URL https://d1lvv0q42gy9jf.cloudfront.net/...
```

これはNulab側の実装に起因するもので、Team Insightの動作には影響しません。無視して問題ありません。

## コントリビューション

1. Feature ブランチを作成: `git checkout -b feature/your-feature`
2. 変更をコミット: `git commit -m 'Add your feature'`
3. ブランチをプッシュ: `git push origin feature/your-feature`
4. プルリクエストを作成

### コーディング規約

- Python: PEP 8, Black, isort
- TypeScript: ESLint, Prettier
- コミット: Conventional Commits

## 参考資料

- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/)
- [React 公式ドキュメント](https://react.dev/)
- [Docker Compose 公式ドキュメント](https://docs.docker.com/compose/)
- [Backlog API 仕様](https://developer.nulab.com/ja/docs/backlog/)
