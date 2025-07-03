# OpenAPIスキーマからTypeScript型自動生成ガイド

## 概要

FastAPIは自動的にOpenAPIスキーマを生成します。このスキーマからTypeScriptの型定義を自動生成することで、バックエンドとフロントエンドの型の整合性を保証できます。

## 仕組みの流れ

```
1. FastAPI → OpenAPIスキーマ（自動生成）
2. OpenAPIスキーマ → TypeScript型定義（ツールで自動生成）
3. フロントエンドでTypeScript型定義を使用
```

## 実装例

### 1. FastAPIでスキーマを定義

```python
# backend/app/schemas/health.py
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class ServiceStatus(BaseModel):
    """サービスの健全性ステータス"""
    api: Literal["healthy", "unhealthy"]
    database: Literal["healthy", "unhealthy"]
    redis: Literal["healthy", "unhealthy"]

class HealthResponse(BaseModel):
    """ヘルスチェックのレスポンス"""
    status: Literal["healthy", "unhealthy"] = Field(
        ..., description="全体の健全性ステータス"
    )
    services: ServiceStatus = Field(
        ..., description="各サービスの健全性ステータス"
    )
    message: str = Field(
        ..., description="ステータスメッセージ"
    )
    timestamp: datetime = Field(
        ..., description="チェック実行時刻"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "services": {
                    "api": "healthy",
                    "database": "healthy",
                    "redis": "healthy"
                },
                "message": "Team Insight API is running",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
```

### 2. APIエンドポイントでスキーマを使用

```python
# backend/app/main.py
from app.schemas.health import HealthResponse

@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    # ... 健全性チェックの実装 ...
    return HealthResponse(
        status=overall_status,
        services=ServiceStatus(**health_status),
        message="Team Insight API is running",
        timestamp=datetime.utcnow()
    )
```

### 3. OpenAPIスキーマの確認

FastAPIは自動的に以下のURLでOpenAPIスキーマを公開：
- JSON形式: `http://localhost:8000/openapi.json`
- ドキュメント: `http://localhost:8000/docs`

### 4. TypeScript型の自動生成

#### 方法1: openapi-typescript を使用

```bash
# インストール
npm install -D openapi-typescript

# 型定義の生成
npx openapi-typescript http://localhost:8000/openapi.json -o ./src/types/api.d.ts
```

生成される型定義：
```typescript
// src/types/api.d.ts
export interface paths {
  "/health": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["HealthResponse"];
          };
        };
      };
    };
  };
}

export interface components {
  schemas: {
    HealthResponse: {
      status: "healthy" | "unhealthy";
      services: {
        api: "healthy" | "unhealthy";
        database: "healthy" | "unhealthy";
        redis: "healthy" | "unhealthy";
      };
      message: string;
      timestamp: string;
    };
  };
}
```

#### 方法2: openapi-generator を使用

```bash
# インストール
npm install -D @openapitools/openapi-generator-cli

# 設定ファイル作成
cat > openapi-generator-config.json << EOF
{
  "generatorName": "typescript-axios",
  "outputDir": "./src/generated",
  "inputSpec": "http://localhost:8000/openapi.json",
  "additionalProperties": {
    "supportsES6": true,
    "withInterfaces": true
  }
}
EOF

# 生成
npx openapi-generator-cli generate -c openapi-generator-config.json
```

### 5. package.jsonにスクリプトを追加

```json
{
  "scripts": {
    "generate:types": "openapi-typescript http://localhost:8000/openapi.json -o ./src/types/api.d.ts",
    "generate:api": "openapi-generator-cli generate -c openapi-generator-config.json"
  }
}
```

### 6. 自動生成された型を使用

```typescript
// src/services/health.service.ts
import type { components } from '@/types/api';

// 自動生成された型を使用
type HealthStatus = components['schemas']['HealthResponse'];

class HealthService {
  async checkHealth(): Promise<HealthStatus> {
    const response = await axios.get<HealthStatus>(
      `${API_BASE_URL}/health`
    );
    return response.data;
  }
}
```

## メリット

1. **型の一元管理**: バックエンドのPydanticモデルが唯一の真実の源
2. **自動同期**: APIが変更されると、型定義も自動的に更新
3. **型安全性**: コンパイル時に型の不一致を検出
4. **開発効率**: 手動での型定義が不要
5. **ドキュメント連携**: OpenAPIドキュメントと型定義が常に同期

## 注意点

1. **ビルドプロセス**: 型生成をCI/CDパイプラインに組み込む
2. **ローカル開発**: バックエンドが起動している必要がある
3. **カスタマイズ**: 生成された型に手を加えない（再生成で消える）

## 推奨ワークフロー

1. バックエンドでPydanticモデルを変更
2. `docker-compose up -d backend` でバックエンドを起動
3. `npm run generate:types` で型定義を再生成
4. TypeScriptのコンパイルエラーを確認・修正
5. テストを実行して動作確認

これにより、API契約の変更が自動的にフロントエンドに反映され、型の不整合によるバグを防げます。