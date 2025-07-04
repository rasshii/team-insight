# アーキテクチャと技術スタック

**このガイドで学べること**：
- Team Insightのシステム構成
- 各技術の基本概念と使い方
- 各コンポーネントの役割と連携方法
- なぜこれらの技術を選んだのか

## 📐 システム全体構成

### Webアプリケーションの基本構造

まず、一般的なWebアプリケーションがどのように動作するか理解しましょう。

#### 従来のWebアプリケーション
```
ユーザー → Webサーバー → アプリケーション → データベース
         ←              ←                  ←
```

#### モダンなWebアプリケーション（Team Insight）
```
ユーザー → フロントエンド（React） → バックエンドAPI → データベース
         ← (JavaScript/HTML/CSS)   ← (JSON)          ←
```

**メリット**：
- フロントエンドとバックエンドを独立して開発できる
- ユーザー体験が向上（ページ遷移なしで動的に更新）
- スケーラビリティが高い（それぞれ別々に拡張可能）

### アーキテクチャ概要

Team Insightは、以下のコンポーネントで構成されるモダンなWebアプリケーションです：

```
┌─────────────────────────────────────────────────────────────┐
│                        ブラウザ                              │
└─────────────────────┬───────────────────────────────────────┘
                      │ http://localhost
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (リバースプロキシ)                   │
│  ・静的ファイル配信                                          │
│  ・APIリクエストのルーティング                               │
│  ・ロードバランシング（将来）                                │
└──────────┬──────────────────────────┬───────────────────────┘
           │ :3000                    │ :8000
           ▼                          ▼
┌──────────────────────┐    ┌────────────────────────────────┐
│  Next.js Frontend    │    │    FastAPI Backend             │
│  ・React Components  │    │    ・REST API                  │
│  ・Redux Toolkit     │◀───│    ・Business Logic            │
│  ・TanStack Query    │    │    ・Authentication            │
└──────────────────────┘    └────────┬───────────┬────────────┘
                                     │           │
                            ┌────────▼───┐   ┌───▼────────┐
                            │ PostgreSQL │   │   Redis    │
                            │  Database  │   │   Cache    │
                            └────────────┘   └────────────┘
                                     │
                                     ▼
                            ┌────────────────┐
                            │  Backlog API   │
                            │  (External)    │
                            └────────────────┘
```

### 各コンポーネントの役割（詳細）

#### 1. Nginx（エンジンエックス）
**役割**: リバースプロキシ（交通整理役）

**なぜ必要？**
- ユーザーは一つのURL（http://localhost）でアクセスしたい
- でも実際は、フロントエンド（:3000）とバックエンド（:8000）が別々
- Nginxがリクエストを適切に振り分ける

```nginx
# Nginxの設定例
location / {
    # 通常のリクエストはフロントエンドへ
    proxy_pass http://frontend:3000;
}

location /api {
    # APIリクエストはバックエンドへ
    proxy_pass http://backend:8000;
}
```

#### 2. Frontend（Next.js）
**役割**: ユーザーインターフェース（画面）

**特徴**:
- React（UIライブラリ）をベースにしたフレームワーク
- TypeScriptで型安全な開発
- ユーザーの操作に応じて動的に画面を更新

#### 3. Backend（FastAPI）
**役割**: ビジネスロジックとデータ処理

**特徴**:
- Pythonで書かれた高速なWebフレームワーク
- 自動的にAPIドキュメントを生成
- 型ヒントによる自動バリデーション

#### 4. PostgreSQL
**役割**: データの永続的な保存

**特徴**:
- リレーショナルデータベース（表形式でデータを管理）
- SQLという言語でデータを操作
- ACID特性（データの整合性を保証）

#### 5. Redis
**役割**: 高速なキャッシュストレージ

**特徴**:
- メモリ上でデータを管理（超高速）
- 一時的なデータの保存に使用
- セッション情報やAPIレスポンスのキャッシュ

### サービス構成とポート

| サービス | 内部ポート | 外部アクセス | 役割 | なぜこのポート？ |
|---------|-----------|-------------|------|----------------|
| Nginx | 80 | http://localhost | リバースプロキシ | HTTPの標準ポート |
| Frontend | 3000 | - | Next.jsアプリ | Next.jsのデフォルト |
| Backend | 8000 | - | FastAPI API | FastAPIのデフォルト |
| PostgreSQL | 5432 | localhost:5432 | メインDB | PostgreSQLの標準ポート |
| Redis | 6379 | localhost:6379 | キャッシュ | Redisの標準ポート |
| MailHog | 8025 | localhost:8025 | メール確認UI | MailHogのWebUI用 |

## 🛠️ 技術スタック詳細

### バックエンド技術

#### FastAPI (v0.109.2) - 詳細解説

**FastAPIとは？**
FastAPIは、Pythonで書かれた最新のWebフレームワークです。APIを簡単に、そして高速に作ることができます。

**基本的な構文と概念**：

1. **最小限のAPIの例**
```python
from fastapi import FastAPI

# アプリケーションインスタンスを作成
app = FastAPI()

# ルート（エンドポイント）を定義
@app.get("/")  # GETメソッドで"/"にアクセスしたときの処理
def read_root():
    return {"message": "Hello World"}

# パラメータを受け取る例
@app.get("/users/{user_id}")  # URLパスからパラメータを取得
def read_user(user_id: int):  # 型ヒントで自動的にintに変換
    return {"user_id": user_id}
```

2. **型ヒントによる自動バリデーション**
```python
from pydantic import BaseModel

# リクエストボディの型を定義
class User(BaseModel):
    name: str
    age: int
    email: str

@app.post("/users/")
def create_user(user: User):  # 自動的にJSONをUserオブジェクトに変換
    # userはUser型として扱える
    return {"name": user.name, "age": user.age}
```

3. **非同期処理（async/await）**
```python
import asyncio

# 非同期関数の定義
@app.get("/slow-operation")
async def slow_operation():
    # 時間のかかる処理（例：外部API呼び出し）
    await asyncio.sleep(1)  # 1秒待機（他の処理をブロックしない）
    return {"status": "complete"}
```

**Team Insightでの実装**：
```python
# backend/app/main.py より
app = FastAPI(
    title=settings.APP_NAME,              # APIの名前
    openapi_url=f"{settings.API_V1_STR}/openapi.json",  # APIドキュメントのURL
    lifespan=lifespan,                    # 起動・終了時の処理
    debug=settings.DEBUG                  # デバッグモード
)
```

**選定理由**：
- **高速**: Starlette + Pydanticによる最速レベルのPython Webフレームワーク
- **型安全**: Pythonの型ヒントを活用した自動バリデーション
- **自動ドキュメント**: OpenAPI（Swagger）の自動生成
- **非同期対応**: async/awaitをフルサポート
- **学習しやすい**: Pythonの標準的な書き方で実装できる

#### SQLAlchemy 2.0 + PostgreSQL - 詳細解説

**SQLAlchemyとは？**
SQLAlchemyは、PythonのORM（Object-Relational Mapping）ライブラリです。データベースのテーブルをPythonのクラスとして扱えるようにします。

**基本概念の説明**：

1. **従来のSQL（データベース操作）**
```sql
-- ユーザーを作成
INSERT INTO users (email, name) VALUES ('user@example.com', 'John Doe');

-- ユーザーを検索
SELECT * FROM users WHERE email = 'user@example.com';
```

2. **SQLAlchemyを使った場合**
```python
# ユーザーを作成（Pythonオブジェクトとして）
user = User(email='user@example.com', name='John Doe')
db.add(user)
db.commit()

# ユーザーを検索（Pythonの構文で）
user = db.query(User).filter(User.email == 'user@example.com').first()
```

**SQLAlchemyの基本的な使い方**：

```python
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ベースクラスを作成
Base = declarative_base()

# モデル（テーブル）を定義
class User(Base):
    __tablename__ = "users"  # データベースのテーブル名
    
    # カラム（列）を定義
    id = Column(Integer, primary_key=True)  # 主キー
    email = Column(String, unique=True)     # ユニーク制約
    name = Column(String, nullable=False)   # NULL不可
    age = Column(Integer)                   # 通常のカラム

# データベースに接続
engine = create_engine('postgresql://user:password@localhost/dbname')
Session = sessionmaker(bind=engine)
db = Session()

# CRUD操作の例
# Create（作成）
new_user = User(email='test@example.com', name='Test User', age=25)
db.add(new_user)
db.commit()

# Read（読み取り）
users = db.query(User).all()  # すべて取得
user = db.query(User).filter(User.email == 'test@example.com').first()

# Update（更新）
user.age = 26
db.commit()

# Delete（削除）
db.delete(user)
db.commit()
```

**Team Insightでの実装**：
```python
# backend/app/models/user.py より
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "team_insight"}  # スキーマを指定
    
    # UUIDを主キーとして使用（より安全）
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    
    # リレーション（他のテーブルとの関連）
    user_roles = relationship("UserRole", back_populates="user")
```

**PostgreSQLとは？**
PostgreSQLは、高機能なオープンソースのリレーショナルデータベースです。

**なぜPostgreSQL？**
- **信頼性**: 大規模なアプリケーションでも安定動作
- **高機能**: JSON型、配列型、全文検索など
- **拡張性**: 必要に応じて機能を追加可能
- **標準準拠**: SQL標準に準拠

**選定理由**：
- **強力なORM**: 複雑なクエリも簡潔に記述可能
- **型安全**: SQLAlchemy 2.0の改善された型サポート
- **PostgreSQL**: エンタープライズレベルの機能と信頼性

#### Redis - 詳細解説

**Redisとは？**
Redis（Remote Dictionary Server）は、メモリ上でデータを管理する高速なKey-Valueストアです。

**なぜキャッシュが必要？**
```
通常のフロー：
ユーザー → API → データベース（遅い：10-100ms）
           ←     ←

Redisを使ったフロー：
ユーザー → API → Redis（速い：1ms以下）
           ←     ←
                  ↓ キャッシュミスの場合のみ
                  データベース
```

**Redisの基本的な使い方**：

```python
import redis
import json

# Redisに接続
r = redis.Redis(host='localhost', port=6379, db=0)

# 基本的な操作
# SET: データを保存
r.set('user:1', 'John Doe')

# GET: データを取得
name = r.get('user:1')  # b'John Doe' (バイト文字列)

# 有効期限付きで保存（TTL: Time To Live）
r.setex('session:abc123', 3600, 'user_data')  # 1時間後に自動削除

# JSONデータの保存
user_data = {
    'id': 1,
    'name': 'John Doe',
    'email': 'john@example.com'
}
r.set('user:1:profile', json.dumps(user_data))

# JSONデータの取得
cached_data = r.get('user:1:profile')
if cached_data:
    user = json.loads(cached_data)
```

**Team Insightでの実装**：
```python
# backend/app/core/cache.py より
class RedisClient:
    async def cache_api_response(
        self, 
        key: str, 
        data: dict, 
        expire: int = 300  # 5分
    ):
        """APIレスポンスをキャッシュ"""
        redis_conn = await self.get_connection()
        await redis_conn.setex(
            key,
            expire,
            json.dumps(data)
        )
    
    async def get_cached_data(self, key: str):
        """キャッシュからデータを取得"""
        redis_conn = await self.get_connection()
        cached = await redis_conn.get(key)
        if cached:
            return json.loads(cached)
        return None

# 使用例
@app.get("/projects")
async def get_projects():
    # キャッシュキーを作成
    cache_key = f"projects:user:{current_user.id}"
    
    # キャッシュを確認
    cached = await redis_client.get_cached_data(cache_key)
    if cached:
        return cached  # キャッシュから返す（高速）
    
    # データベースから取得
    projects = db.query(Project).all()
    
    # キャッシュに保存
    await redis_client.cache_api_response(cache_key, projects)
    
    return projects
```

**Redisの活用例**：
1. **APIレスポンスのキャッシュ**
   - 頻繁にアクセスされるデータを高速化
   
2. **セッション管理**
   - ユーザーのログイン状態を保存
   
3. **レート制限**
   - APIへの過度なアクセスを防ぐ
   ```python
   # 1分間に10回までのアクセス制限
   key = f"rate_limit:{user_id}"
   count = r.incr(key)
   if count == 1:
       r.expire(key, 60)  # 60秒後に自動削除
   if count > 10:
       raise HTTPException(429, "Too many requests")
   ```

**選定理由**：
- **高速キャッシュ**: ミリ秒単位でのデータアクセス
- **柔軟なデータ構造**: 文字列、リスト、セット、ハッシュなど
- **自動削除機能**: TTLによるメモリ管理
- **スケーラビリティ**: 分散環境でも利用可能

### フロントエンド技術

#### Next.js 14.1 (App Router) - 詳細解説

**Next.jsとは？**
Next.jsは、Reactベースのフルスタックフレームワークです。Reactの機能を拡張し、本番環境に必要な機能を提供します。

**React vs Next.js**
```
React: UIライブラリ（画面の部品を作る）
Next.js: Reactを使ったフレームワーク（アプリケーション全体を構築）
```

**App Routerとは？**
Next.js 13から導入された新しいルーティングシステムで、ファイルシステムベースでページを作成します。

**基本的な構造**：
```
src/app/
├── layout.tsx          # 全ページ共通のレイアウト
├── page.tsx           # ホームページ（/）
├── about/
│   └── page.tsx       # /about ページ
├── blog/
│   ├── page.tsx       # /blog ページ
│   └── [id]/
│       └── page.tsx   # /blog/123 などの動的ルート
└── api/
    └── hello/
        └── route.ts   # /api/hello APIエンドポイント
```

**基本的な使い方**：

1. **ページコンポーネント**
```typescript
// src/app/page.tsx
export default function HomePage() {
  return (
    <div>
      <h1>ホームページ</h1>
      <p>これがトップページです</p>
    </div>
  )
}
```

2. **レイアウトコンポーネント**
```typescript
// src/app/layout.tsx
export default function RootLayout({
  children,  // ページコンテンツが入る
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>
        <header>
          <nav>共通ナビゲーション</nav>
        </header>
        <main>{children}</main>
        <footer>共通フッター</footer>
      </body>
    </html>
  )
}
```

3. **動的ルート**
```typescript
// src/app/projects/[id]/page.tsx
interface Props {
  params: { id: string }  // URLパラメータ
}

export default function ProjectPage({ params }: Props) {
  // /projects/123 にアクセスすると params.id = "123"
  return <div>プロジェクトID: {params.id}</div>
}
```

4. **Server Components（デフォルト）**
```typescript
// デフォルトでサーバーサイドで実行される
async function ProjectList() {
  // サーバーで直接データを取得（ブラウザでは実行されない）
  const projects = await fetch('http://backend:8000/api/projects')
  
  return (
    <ul>
      {projects.map(p => <li key={p.id}>{p.name}</li>)}
    </ul>
  )
}
```

5. **Client Components（インタラクティブな要素）**
```typescript
'use client'  // この指定でクライアントコンポーネントになる

import { useState } from 'react'

export function Counter() {
  const [count, setCount] = useState(0)
  
  // ブラウザで実行される（インタラクティブ）
  return (
    <button onClick={() => setCount(count + 1)}>
      クリック数: {count}
    </button>
  )
}
```

**Team Insightでの実装**：
```typescript
// frontend/src/app/layout.tsx より
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>
        <Providers>{children}</Providers>  {/* Redux/React Query の設定 */}
      </body>
    </html>
  )
}
```

**選定理由**：
- **Server Components**: 初期読み込みの高速化（サーバーでHTML生成）
- **App Router**: ディレクトリ構造＝URL構造で直感的
- **TypeScript標準**: 型によるバグの早期発見
- **最適化**: 自動的なコード分割、画像最適化、フォント最適化
- **開発体験**: ホットリロード、エラー表示の改善

#### Redux Toolkit + TanStack Query - 詳細解説

**状態管理とは？**
Webアプリケーションでは、様々なデータ（状態）を管理する必要があります：
- ユーザー情報（ログイン中のユーザー）
- UIの状態（メニューが開いているか、など）
- サーバーから取得したデータ（プロジェクト一覧、など）

**なぜ2つの状態管理ツールを使い分ける？**

1. **Redux Toolkit**: クライアント状態（アプリ内の状態）
   - ユーザー認証情報
   - UIの状態（テーマ、言語設定など）
   - アプリ全体で共有する設定

2. **TanStack Query**: サーバー状態（APIから取得するデータ）
   - プロジェクト一覧
   - ユーザー情報
   - タスクデータ

**Redux Toolkitの基本**：

```typescript
// 1. スライス（状態の一部）を定義
import { createSlice } from '@reduxjs/toolkit'

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    isAuthenticated: false
  },
  reducers: {
    // 状態を更新する関数（アクション）
    login: (state, action) => {
      state.user = action.payload
      state.isAuthenticated = true
    },
    logout: (state) => {
      state.user = null
      state.isAuthenticated = false
    }
  }
})

// 2. コンポーネントで使用
import { useSelector, useDispatch } from 'react-redux'

function UserProfile() {
  // 状態を取得
  const user = useSelector(state => state.auth.user)
  // アクションを実行する関数を取得
  const dispatch = useDispatch()
  
  const handleLogout = () => {
    dispatch(authSlice.actions.logout())
  }
  
  return (
    <div>
      <p>ユーザー名: {user?.name}</p>
      <button onClick={handleLogout}>ログアウト</button>
    </div>
  )
}
```

**TanStack Query（React Query）の基本**：

```typescript
// 1. カスタムフックを作成
import { useQuery, useMutation } from '@tanstack/react-query'

// データ取得用のフック
export function useProjects() {
  return useQuery({
    queryKey: ['projects'],  // キャッシュのキー
    queryFn: async () => {
      // APIからデータを取得
      const response = await fetch('/api/projects')
      return response.json()
    },
    staleTime: 5 * 60 * 1000,  // 5分間は再取得しない
  })
}

// データ更新用のフック
export function useCreateProject() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (newProject) => {
      const response = await fetch('/api/projects', {
        method: 'POST',
        body: JSON.stringify(newProject)
      })
      return response.json()
    },
    onSuccess: () => {
      // 成功したらプロジェクト一覧を再取得
      queryClient.invalidateQueries(['projects'])
    }
  })
}

// 2. コンポーネントで使用
function ProjectList() {
  // データを取得（自動的にキャッシュ管理）
  const { data, isLoading, error } = useProjects()
  const createMutation = useCreateProject()
  
  if (isLoading) return <div>読み込み中...</div>
  if (error) return <div>エラー: {error.message}</div>
  
  return (
    <div>
      {data.map(project => (
        <div key={project.id}>{project.name}</div>
      ))}
      <button onClick={() => createMutation.mutate({ name: '新規プロジェクト' })}>
        プロジェクト作成
      </button>
    </div>
  )
}
```

**TanStack Queryの便利な機能**：

1. **自動的な再取得**
   ```typescript
   useQuery({
     queryKey: ['projects'],
     queryFn: fetchProjects,
     refetchInterval: 60000,      // 1分ごとに自動更新
     refetchOnWindowFocus: true,  // タブに戻ったときに更新
   })
   ```

2. **楽観的更新**
   ```typescript
   useMutation({
     mutationFn: updateProject,
     onMutate: async (newData) => {
       // 即座にUIを更新（サーバーレスポンスを待たない）
       queryClient.setQueryData(['project', id], newData)
     },
     onError: () => {
       // エラー時は元に戻す
       queryClient.invalidateQueries(['project', id])
     }
   })
   ```

**Team Insightでの実装**：
```typescript
// frontend/src/hooks/queries/useProjects.ts より
export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],               // キャッシュキー
    queryFn: projectService.getProjects,  // API呼び出し関数
    staleTime: 5 * 60 * 1000,            // 5分間キャッシュ
  })
}
```

**選定理由**：
- **役割分担**: クライアント状態とサーバー状態を明確に分離
- **キャッシュ管理**: TanStack Queryが自動的にキャッシュを最適化
- **開発効率**: ボイラープレートコードが少ない
- **パフォーマンス**: 必要なデータのみを取得・更新

#### shadcn/ui (Radix UI + Tailwind CSS) - 詳細解説

**公式ドキュメント**: https://ui.shadcn.com/

shadcn/uiは、Radix UIとTailwind CSSを組み合わせたモダンなUIコンポーネントライブラリです。

**なぜshadcn/uiを選んだか**：
- **カスタマイズ可能**: コンポーネントのソースコードを直接プロジェクトにコピー
- **アクセシビリティ**: Radix UIによるWAI-ARIA準拠
- **デザインシステム**: 一貫性のあるUI/UX
- **TypeScript対応**: 完全な型サポート

**Team Insightでの実装例**：
```typescript
// components/ui/button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

#### D3.js (7.8.5) - データビジュアライゼーション

**公式ドキュメント**: https://d3js.org/

D3.js（Data-Driven Documents）は、データに基づいて動的なビジュアライゼーションを作成するJavaScriptライブラリです。

**Team Insightでの活用**：
- **スループットチャート**: タスク完了率の推移
- **円グラフ**: タスク分配の可視化
- **棒グラフ**: チームメンバーの生産性比較
- **ヒートマップ**: 時間帯別の活動状況

**実装例 - スループットチャート**：
```typescript
// components/charts/ThroughputChart.tsx
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export function ThroughputChart({ data }: { data: ThroughputData[] }) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || !data.length) return

    const margin = { top: 20, right: 30, bottom: 40, left: 50 }
    const width = 600 - margin.left - margin.right
    const height = 400 - margin.top - margin.bottom

    // SVG要素をクリア
    d3.select(svgRef.current).selectAll("*").remove()

    const svg = d3.select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // スケールの設定
    const x = d3.scaleTime()
      .domain(d3.extent(data, d => new Date(d.date)) as [Date, Date])
      .range([0, width])

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.completed) as number])
      .range([height, 0])

    // ラインジェネレーター
    const line = d3.line<ThroughputData>()
      .x(d => x(new Date(d.date)))
      .y(d => y(d.completed))
      .curve(d3.curveMonotoneX)

    // X軸
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d")))

    // Y軸
    g.append("g")
      .call(d3.axisLeft(y))

    // ライン描画
    g.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 2)
      .attr("d", line)

    // データポイント
    g.selectAll(".dot")
      .data(data)
      .enter().append("circle")
      .attr("class", "dot")
      .attr("cx", d => x(new Date(d.date)))
      .attr("cy", d => y(d.completed))
      .attr("r", 4)
      .attr("fill", "#3b82f6")

  }, [data])

  return <svg ref={svgRef}></svg>
}
```

#### React Hook Form (7.57.0) - 高性能フォーム管理

**公式ドキュメント**: https://react-hook-form.com/

React Hook Formは、パフォーマンスを重視したフォーム管理ライブラリです。

**なぜReact Hook Formを選んだか**：
- **最小限の再レンダリング**: 非制御コンポーネントベースで高速
- **軽量**: ~25KB（gzip圧縮時）
- **バリデーション統合**: Zodなどのスキーマライブラリと完全統合
- **開発者体験**: シンプルなAPIと優れたTypeScriptサポート

**Team Insightでの実装例**：
```typescript
// components/projects/CreateProjectForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// Zodでスキーマ定義
const createProjectSchema = z.object({
  name: z.string()
    .min(1, '名前は必須です')
    .max(100, '名前は100文字以内で入力してください'),
  description: z.string()
    .min(10, '説明は10文字以上で入力してください')
    .optional(),
  startDate: z.string().refine((date) => {
    return new Date(date) >= new Date()
  }, '開始日は今日以降の日付を選択してください'),
  endDate: z.string(),
  memberIds: z.array(z.string()).min(1, 'メンバーを1人以上選択してください')
}).refine((data) => {
  return new Date(data.endDate) > new Date(data.startDate)
}, {
  message: '終了日は開始日より後の日付を選択してください',
  path: ['endDate']
})

type CreateProjectFormData = z.infer<typeof createProjectSchema>

export function CreateProjectForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
    control
  } = useForm<CreateProjectFormData>({
    resolver: zodResolver(createProjectSchema),
    defaultValues: {
      memberIds: []
    }
  })

  const onSubmit = async (data: CreateProjectFormData) => {
    try {
      await projectService.createProject(data)
      toast.success('プロジェクトを作成しました')
    } catch (error) {
      toast.error('プロジェクトの作成に失敗しました')
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>プロジェクト名</label>
        <input
          {...register('name')}
          type="text"
          placeholder="新規プロジェクト"
        />
        {errors.name && (
          <span className="text-red-500">{errors.name.message}</span>
        )}
      </div>

      <div>
        <label>説明</label>
        <textarea
          {...register('description')}
          placeholder="プロジェクトの説明を入力"
          rows={4}
        />
        {errors.description && (
          <span className="text-red-500">{errors.description.message}</span>
        )}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? '作成中...' : 'プロジェクトを作成'}
      </button>
    </form>
  )
}
```

#### Zod (3.25.64) - TypeScript First スキーマバリデーション

**公式ドキュメント**: https://zod.dev/

Zodは、TypeScriptファーストなスキーマ宣言とバリデーションライブラリです。

**なぜZodを選んだか**：
- **型推論**: スキーマから自動的にTypeScript型を生成
- **豊富なバリデーション**: 組み込みの検証メソッドが充実
- **エラーメッセージ**: カスタマイズ可能な日本語エラーメッセージ
- **実行時検証**: APIレスポンスの検証にも使用可能

**Team Insightでの高度な使用例**：
```typescript
// schemas/user.ts
import { z } from 'zod'

// 基本的なスキーマ
export const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email('有効なメールアドレスを入力してください'),
  name: z.string().min(1, '名前は必須です'),
  role: z.enum(['ADMIN', 'PROJECT_LEADER', 'MEMBER']),
  isActive: z.boolean(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime()
})

// 部分的なスキーマ（更新用）
export const updateUserSchema = userSchema.partial().omit({
  id: true,
  createdAt: true,
  updatedAt: true
})

// APIレスポンスの検証
export const userResponseSchema = z.object({
  success: z.boolean(),
  data: userSchema,
  message: z.string().optional()
})

// 配列のバリデーション
export const usersListSchema = z.object({
  users: z.array(userSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  pageSize: z.number().int().positive()
})

// カスタムバリデーション
export const passwordSchema = z.string()
  .min(8, 'パスワードは8文字以上で入力してください')
  .regex(/[A-Z]/, '大文字を1文字以上含めてください')
  .regex(/[a-z]/, '小文字を1文字以上含めてください')
  .regex(/[0-9]/, '数字を1文字以上含めてください')
  .regex(/[^A-Za-z0-9]/, '特殊文字を1文字以上含めてください')

// 使用例
try {
  const validatedUser = userSchema.parse(apiResponse)
  // validatedUser は型安全
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error('バリデーションエラー:', error.errors)
  }
}
```

#### date-fns (4.1.0) - モダンな日付操作ライブラリ

**公式ドキュメント**: https://date-fns.org/

date-fnsは、モジュール式で軽量な日付操作ライブラリです。

**なぜdate-fnsを選んだか**：
- **ツリーシェイキング**: 使用する関数のみバンドル
- **イミュータブル**: 元の日付オブジェクトを変更しない
- **国際化対応**: 日本語ロケールのサポート
- **TypeScript**: 完全な型サポート

**Team Insightでの実装例**：
```typescript
// utils/date.ts
import {
  format,
  formatDistance,
  formatRelative,
  parseISO,
  addDays,
  subDays,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isWeekend,
  isSameDay,
  differenceInDays,
  differenceInBusinessDays
} from 'date-fns'
import { ja } from 'date-fns/locale'

// 日付フォーマット関数
export const formatDate = (date: string | Date, pattern = 'yyyy年MM月dd日') => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return format(dateObj, pattern, { locale: ja })
}

// 相対時間表示
export const formatRelativeTime = (date: string | Date) => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return formatDistance(dateObj, new Date(), {
    addSuffix: true,
    locale: ja
  })
}

// スプリント期間の計算
export const calculateSprintDays = (startDate: Date, endDate: Date) => {
  const days = eachDayOfInterval({ start: startDate, end: endDate })
  const businessDays = days.filter(day => !isWeekend(day))
  return {
    totalDays: days.length,
    businessDays: businessDays.length,
    weekends: days.length - businessDays.length
  }
}

// タスクの遅延日数計算
export const calculateDelay = (dueDate: string, completedDate?: string) => {
  const due = parseISO(dueDate)
  const completed = completedDate ? parseISO(completedDate) : new Date()
  
  const delayDays = differenceInDays(completed, due)
  const delayBusinessDays = differenceInBusinessDays(completed, due)
  
  return {
    delayDays,
    delayBusinessDays,
    isDelayed: delayDays > 0,
    status: delayDays > 0 ? '遅延' : '期限内'
  }
}

// Team Insightでの使用例
function TaskCard({ task }: { task: Task }) {
  const delay = calculateDelay(task.dueDate, task.completedDate)
  
  return (
    <div className="task-card">
      <h3>{task.title}</h3>
      <p>期限: {formatDate(task.dueDate)}</p>
      <p>作成: {formatRelativeTime(task.createdAt)}</p>
      {delay.isDelayed && (
        <span className="text-red-500">
          {delay.delayBusinessDays}営業日遅延
        </span>
      )}
    </div>
  )
}
```

## 🔄 データフロー - 詳細解説

### 認証フロー（OAuth 2.0）

**OAuth 2.0とは？**
OAuth 2.0は、第三者のサービス（Backlog）のアカウントを使って、安全にログインする仕組みです。パスワードを直接扱わないため安全です。

#### 認証フローの詳細図

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant F as Frontend<br/>(Next.js)
    participant N as Nginx<br/>(Proxy)
    participant B as Backend<br/>(FastAPI)
    participant BL as Backlog<br/>(OAuth)
    participant DB as PostgreSQL
    participant R as Redis

    U->>F: 「Backlogでログイン」クリック
    F->>N: GET /api/v1/auth/backlog/authorize
    N->>B: プロキシ転送
    
    Note over B: state生成・保存
    B->>DB: OAuthStateを保存
    B-->>F: 認証URL返却
    F->>BL: リダイレクト<br/>(認証ページへ)
    
    U->>BL: ログイン情報入力
    BL->>U: 認証確認画面
    U->>BL: 「許可」クリック
    
    BL->>N: GET /api/v1/auth/backlog/callback<br/>?code=xxx&state=yyy
    N->>B: プロキシ転送
    
    Note over B: state検証
    B->>DB: OAuthState確認
    B->>BL: POST /oauth2/token<br/>(コード→トークン交換)
    BL-->>B: アクセストークン<br/>リフレッシュトークン
    
    B->>BL: GET /api/v2/users/myself
    BL-->>B: ユーザー情報
    
    B->>DB: ユーザー作成/更新<br/>トークン保存
    Note over B: JWT生成
    B->>R: セッション情報キャッシュ
    
    B-->>F: Set-Cookie: auth_token<br/>リダイレクト
    F->>U: ダッシュボード表示
```

**認証フローの詳細**：

```
1. ユーザーが「Backlogでログイン」をクリック
   ↓
   フロントエンド：ボタンクリックイベント
   window.location.href = '/api/v1/auth/backlog/authorize'
   
2. Frontend → Backend: /api/v1/auth/backlog/authorize
   ↓
   バックエンド：認証URLを生成
   - state（CSRF対策のランダム文字列）を生成
   - Backlogの認証URLにリダイレクト
   
3. Backend → Backlog OAuth: 認証ページへリダイレクト
   ↓
   ブラウザがBacklogのログインページに移動
   URL例: https://space.backlog.jp/OAuth2/authorize?client_id=xxx&state=yyy
   
4. ユーザーがBacklogで認証承認
   ↓
   ユーザー：Backlogでログイン＆「許可」をクリック
   
5. Backlog → Backend: /api/v1/auth/backlog/callback
   ↓
   Backlog：認証コードを付けてコールバック
   URL例: /api/v1/auth/backlog/callback?code=abc123&state=yyy
   
6. Backend: JWTトークン生成、HttpOnlyクッキーに設定
   ↓
   バックエンド処理：
   - stateを検証（CSRF対策）
   - 認証コードをアクセストークンに交換
   - ユーザー情報を取得・保存
   - JWTトークンを生成
   - HttpOnlyクッキーに保存（XSS対策）
   
7. Backend → Frontend: ログイン成功、ダッシュボードへリダイレクト
   
   最終的にユーザーはログイン済み状態でダッシュボードへ
```

**セキュリティ対策の説明**：
- **state**: CSRF（クロスサイトリクエストフォージェリ）攻撃を防ぐ
- **HttpOnlyクッキー**: JavaScriptからアクセスできないため、XSS攻撃を防ぐ
- **JWT**: 署名付きトークンで、改ざんを検出可能

### APIリクエストフロー - 詳細

#### APIリクエストの処理フロー図

```mermaid
flowchart LR
    subgraph Frontend["Frontend (Next.js)"]
        C[Component]
        TQ[TanStack Query]
        AX[Axios Client]
    end
    
    subgraph Nginx["Nginx"]
        RP[Reverse Proxy]
    end
    
    subgraph Backend["Backend (FastAPI)"]
        MW[Middleware]
        AUTH[認証・認可]
        EP[Endpoint]
        SVC[Service Layer]
    end
    
    subgraph Cache["Cache Layer"]
        REDIS[(Redis)]
    end
    
    subgraph Database["Database"]
        PG[(PostgreSQL)]
    end
    
    C -->|useQuery| TQ
    TQ -->|HTTP Request| AX
    AX -->|Cookie付き| RP
    RP -->|プロキシ| MW
    MW -->|JWT検証| AUTH
    AUTH -->|権限チェック| EP
    EP -->|キャッシュ確認| REDIS
    REDIS -.->|ヒット| EP
    REDIS -->|ミス| SVC
    SVC -->|SQL| PG
    PG -->|データ| SVC
    SVC -->|キャッシュ保存| REDIS
    SVC -->|レスポンス| EP
    EP -->|JSON| RP
    RP -->|転送| TQ
    TQ -->|状態更新| C
```

#### エラーハンドリングフロー

```mermaid
flowchart TD
    REQ[APIリクエスト] --> AUTH{認証チェック}
    AUTH -->|未認証| E401[401 Unauthorized]
    AUTH -->|認証済み| PERM{権限チェック}
    PERM -->|権限なし| E403[403 Forbidden]
    PERM -->|権限あり| VALID{バリデーション}
    VALID -->|エラー| E422[422 Validation Error]
    VALID -->|成功| PROC[処理実行]
    PROC -->|DB接続エラー| E503[503 Service Unavailable]
    PROC -->|ビジネスエラー| E400[400 Bad Request]
    PROC -->|成功| R200[200 OK]
    
    E401 --> ELOG[エラーログ記録]
    E403 --> ELOG
    E422 --> ELOG
    E503 --> ELOG
    E400 --> ELOG
    
    ELOG --> RESP[エラーレスポンス]
    R200 --> SRESP[成功レスポンス]
    
    style E401 fill:#ff6b6b
    style E403 fill:#ff6b6b
    style E422 fill:#ffa06b
    style E503 fill:#ff6b6b
    style E400 fill:#ffa06b
    style R200 fill:#51cf66
```

**実際のコードでの流れ**：

```typescript
// 1. Frontend: TanStack Queryでデータ要求
const ProjectList = () => {
  const { data, isLoading } = useProjects()  // ここでAPIコール開始
}

// 2. Axios Interceptor: 認証トークンを自動付与
// src/lib/api-client.ts
axios.interceptors.request.use((config) => {
  // クッキーは自動的に送信される（credentials: 'include'）
  return config
})

// 3. Nginx: /api/* を Backend:8000 へプロキシ
// nginx.conf
location /api {
    proxy_pass http://backend:8000;  // バックエンドにプロキシ
}

// 4. Backend: 認証・権限チェック（RBAC）
@app.get("/api/v1/projects")
async def get_projects(
    current_user: User = Depends(get_current_user),  # JWT検証
    _: None = Depends(require_role("MEMBER"))        # 権限チェック
):
    # 5. Redisキャッシュ確認
    cache_key = f"projects:user:{current_user.id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)  # キャッシュヒット！
    
    # 6. PostgreSQLからデータ取得
    projects = db.query(Project).filter(
        Project.members.any(user_id=current_user.id)
    ).all()
    
    # 7. レスポンスをRedisにキャッシュ
    await redis_client.setex(
        cache_key, 
        300,  # 5分間
        json.dumps(projects)
    )
    
    # 8. JSONレスポンスを返す
    return projects

// 9. TanStack Query: データをキャッシュ、UIを更新
// フロントエンドに戻る
const ProjectList = () => {
  const { data } = useProjects()  // dataに結果が入る
  return data.map(p => <ProjectCard project={p} />)
}
```

**パフォーマンスのポイント**：
1. **多層キャッシュ**:
   - ブラウザ: TanStack Queryがメモリにキャッシュ
   - サーバー: Redisが高速キャッシュ
   - データベース: PostgreSQLのクエリキャッシュ

2. **並列処理**:
   - 複数のAPIコールを同時実行
   - 非同期処理で待ち時間を削減

3. **最適化**:
   - 必要なデータのみ取得（GraphQLではないが、同様の考え方）
   - ページネーション対応

## 🔐 セキュリティアーキテクチャ

### セキュリティレイヤー構成図

```mermaid
flowchart TB
    subgraph External["外部"]
        USER[ユーザー]
        ATTACKER[攻撃者]
    end
    
    subgraph SecurityLayers["セキュリティレイヤー"]
        subgraph L1["レイヤー1: ネットワーク"]
            HTTPS[HTTPS/TLS 1.3]
            CORS[CORS設定]
        end
        
        subgraph L2["レイヤー2: 認証"]
            OAUTH[Backlog OAuth 2.0]
            JWT[JWT (HttpOnly Cookie)]
            CSRF[CSRF Protection]
        end
        
        subgraph L3["レイヤー3: 認可"]
            RBAC[RBAC システム]
            PERM[権限チェック]
        end
        
        subgraph L4["レイヤー4: アプリケーション"]
            VALID[入力検証 (Pydantic)]
            ORM[SQLAlchemy ORM]
            XSS[XSS対策 (React)]
        end
        
        subgraph L5["レイヤー5: データ"]
            ENCRYPT[保存時暗号化]
            AUDIT[監査ログ]
        end
    end
    
    USER -->|正規アクセス| HTTPS
    ATTACKER -.->|攻撃試行| HTTPS
    HTTPS --> CORS
    CORS --> OAUTH
    OAUTH --> JWT
    JWT --> CSRF
    CSRF --> RBAC
    RBAC --> PERM
    PERM --> VALID
    VALID --> ORM
    ORM --> XSS
    XSS --> ENCRYPT
    ENCRYPT --> AUDIT
    
    style ATTACKER fill:#ff6b6b
    style USER fill:#51cf66
```

### 認証・認可

1. **OAuth 2.0**: Backlog認証によるセキュアなログイン
2. **JWT**: HttpOnlyクッキーでXSS攻撃を防止
3. **RBAC**: ロールベースアクセス制御
   - ADMIN: 全権限
   - PROJECT_LEADER: プロジェクト管理権限
   - MEMBER: 基本的な閲覧・操作権限

### セキュリティ対策

```python
# CORS設定（backend/app/main.py）
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 許可されたオリジンのみ
    allow_credentials=True,         # Cookie認証のため必須
    allow_methods=["*"],
    allow_headers=["*"],
)

# レート制限（今後実装予定）
# SQLインジェクション対策: SQLAlchemy ORM使用
# XSS対策: Reactの自動エスケープ + HttpOnlyクッキー
```

## 🏗️ インフラストラクチャ

### Docker Compose構成

```yaml
# docker-compose.yml の構造
services:
  nginx:       # リバースプロキシ
  frontend:    # Next.jsアプリ
  backend:     # FastAPI API
  postgres:    # PostgreSQL 15
  redis:       # Redis 7.0
  mailhog:     # 開発用メールサーバー
```

### 環境変数管理

- **開発環境**: `.env`ファイルで管理
- **本番環境**: 環境変数またはSecrets Manager
- **機密情報**: 絶対にコミットしない（.gitignore）

## 💡 アーキテクチャ選定のポイント

### なぜこの構成なのか？

1. **スケーラビリティ**
   - フロントエンド/バックエンドの分離で独立したスケーリングが可能
   - Redisキャッシュで負荷軽減

2. **開発効率**
   - TypeScript/Pythonの型システムでバグを事前に防止
   - 自動ドキュメント生成で開発効率向上

3. **保守性**
   - 明確な責任分離
   - 標準的な技術スタックで学習コスト低減

4. **セキュリティ**
   - 業界標準のOAuth 2.0認証
   - 多層防御のセキュリティ設計

## 📝 開発時の注意点

1. **API設計**
   - RESTfulな設計を維持
   - 適切なHTTPステータスコードを返す
   - エラーレスポンスは統一フォーマット

2. **状態管理**
   - サーバー状態: TanStack Query
   - クライアント状態: Redux（最小限）
   - ローカル状態: React useState

3. **パフォーマンス**
   - N+1問題に注意（SQLAlchemyのeager loading活用）
   - 適切なインデックス設定
   - キャッシュ戦略の検討

---

次は[FastAPIバックエンドの基本](03-backend-basics.md)で、実際のコード実装を見ていきましょう！