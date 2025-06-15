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

Team Insight は、Backlog API と連携してチームの開発プロセスを分析・可視化する Web アプリケーションです。

### 主な機能

- **Backlog OAuth 認証**: セキュアな OAuth2.0 認証
- **ダッシュボード**: プロジェクトとチームの統計情報を一覧表示
- **プロジェクト分析**: 課題の進捗状況やボトルネックを可視化
- **チーム分析**: メンバーの生産性やワークロードを分析

## 技術スタック

### バックエンド

- **FastAPI** (Python 3.11): 高速で型安全な Web API フレームワーク
- **SQLAlchemy 2.0**: ORM とデータベース管理
- **PostgreSQL 15**: メインデータベース
- **Redis 7**: キャッシュとセッション管理
- **Alembic**: データベースマイグレーション

### フロントエンド

- **React 18**: UI フレームワーク
- **TypeScript 5**: 型安全な開発
- **Redux Toolkit**: 状態管理
- **shadcn/ui**: UI コンポーネントライブラリ
- **Tailwind CSS v3**: ユーティリティファースト CSS
- **Yarn v4 (Berry)**: パッケージ管理

### インフラ

- **Docker & Docker Compose**: コンテナ化と開発環境
- **Nginx**: リバースプロキシ
- **Node.js v22 LTS**: フロントエンドランタイム

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
DATABASE_URL=postgresql://team_insight_user:team_insight_password@postgres:5432/team_insight

# Redis設定
REDIS_URL=redis://redis:6379/0

# セキュリティ
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Backlog OAuth設定
BACKLOG_CLIENT_ID=your-client-id
BACKLOG_CLIENT_SECRET=your-client-secret
BACKLOG_REDIRECT_URI=http://localhost:3000/auth/callback
BACKLOG_SPACE_KEY=your-space-key
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

- フロントエンド: http://localhost:3000
- バックエンド API: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

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
make test          # テストを実行
make test-coverage # カバレッジレポート付きでテスト実行
make lint          # コードの静的解析を実行
make format        # コードをフォーマット
make clean         # コンテナとボリュームを削除
```

#### コンテナ操作

```bash
make build         # 全イメージをビルド
make rebuild       # 全イメージを再ビルド
make ps            # コンテナの状態を表示
make shell         # バックエンドコンテナのシェルに入る
```

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

class YourFeature(Base):
    """データベースモデル"""
    __tablename__ = "your_features"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
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

3. **Redux Slice** (`src/store/slices/yourFeatureSlice.ts`):

```typescript
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { yourFeatureService } from "@/services/your-feature.service";
import { YourFeature } from "@/types/your-feature";

interface YourFeatureState {
  items: YourFeature[];
  loading: boolean;
  error: string | null;
}

const initialState: YourFeatureState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchYourFeatures = createAsyncThunk(
  "yourFeature/fetchAll",
  async () => {
    return await yourFeatureService.getAll();
  }
);

const yourFeatureSlice = createSlice({
  name: "yourFeature",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchYourFeatures.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchYourFeatures.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchYourFeatures.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "エラーが発生しました";
      });
  },
});

export default yourFeatureSlice.reducer;
```

4. **ページコンポーネント** (`src/app/your-feature/page.tsx`):

```typescript
"use client";

import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchYourFeatures } from "@/store/slices/yourFeatureSlice";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function YourFeaturePage() {
  const dispatch = useAppDispatch();
  const { items, loading, error } = useAppSelector(
    (state) => state.yourFeature
  );

  useEffect(() => {
    dispatch(fetchYourFeatures());
  }, [dispatch]);

  if (loading) {
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
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Your Feature</h1>
      <div className="grid gap-4">
        {items.map((item) => (
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
# すべてのテストを実行
cd frontend
yarn test

# ウォッチモードで実行
yarn test:watch

# カバレッジレポート付きで実行
yarn test:coverage
```

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

1. **API ドキュメント**: http://localhost:8000/docs で対話的に API をテスト
2. **Redux DevTools**: ブラウザ拡張機能で状態管理をデバッグ
3. **Docker logs**: `docker-compose logs -f [service]` でリアルタイムログ確認
4. **Hot Reload**: フロントエンド・バックエンドともに自動リロード対応

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
