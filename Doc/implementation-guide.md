# Team Insight 実装ガイド

## 目次

1. [はじめに - Team Insight とは？](#はじめに---team-insight-とは)
2. [プロジェクトの現在の実装状況](#プロジェクトの現在の実装状況)
3. [全体のアーキテクチャを理解しよう](#全体のアーキテクチャを理解しよう)
4. [ディレクトリ構造と各ファイルの役割](#ディレクトリ構造と各ファイルの役割)
5. [実装済み機能の詳細解説](#実装済み機能の詳細解説)
6. [フロントエンドアーキテクチャ詳説](#フロントエンドアーキテクチャ詳説)
7. [バックエンドアーキテクチャ詳説](#バックエンドアーキテクチャ詳説)
8. [D3.js によるデータ可視化](#d3js-によるデータ可視化)
9. [開発環境のセットアップ](#開発環境のセットアップ)
10. [今後の実装計画](#今後の実装計画)
11. [ベストプラクティス](#ベストプラクティス)
12. [トラブルシューティング](#トラブルシューティング)

---

## はじめに - Team Insight とは？

Team Insight は、開発チームの生産性を可視化し、データに基づいた意思決定を支援する Web アプリケーションです。このプロジェクトを通じて、モダンな Web アプリケーション開発の実践的なスキルを身につけることができます。

### Team Insight が解決する問題

開発現場でよくある問題を考えてみましょう。多くのチームが「なんとなく忙しい」と感じながらも、具体的にどこに時間がかかっているのか、誰の負荷が高いのか、プロジェクトは健全に進んでいるのかを把握できていません。

```mermaid
graph TB
    subgraph "よくある課題"
        A[感覚的な状況把握]
        B[ボトルネックの特定困難]
        C[個人パフォーマンス不明]
        D[改善点が見えない]
    end

    subgraph "Team Insightの解決策"
        E[データに基づく分析]
        F[自動検出と可視化]
        G[客観的な指標提供]
        H[具体的な改善提案]
    end

    A --> E
    B --> F
    C --> G
    D --> H

    E --> I[組織全体の生産性向上]
    F --> I
    G --> I
    H --> I

    style A fill:#ffccbc
    style B fill:#ffccbc
    style C fill:#ffccbc
    style D fill:#ffccbc
    style E fill:#c5e1a5
    style F fill:#c5e1a5
    style G fill:#c5e1a5
    style H fill:#c5e1a5
    style I fill:#fff9c4
```

### 3 つのユーザーロールと提供価値

Team Insight は、組織の階層に応じて異なる価値を提供します。これは、実際の開発現場では立場によって必要な情報が異なるためです。

| ロール                   | 主な利用者                     | 提供価値                                               | アクセス可能な画面                |
| ------------------------ | ------------------------------ | ------------------------------------------------------ | --------------------------------- |
| **メンバー**             | 開発者、デザイナー等           | 自身の作業効率を把握し、個人の成長を促進               | 個人ダッシュボード                |
| **プロジェクトリーダー** | チームリード、スクラムマスター | チームの健康状態を監視し、ボトルネックを早期発見       | プロジェクトダッシュボード + 個人 |
| **管理者**               | 開発マネージャー、CTO          | 組織全体のパフォーマンスを分析し、リソース配分を最適化 | すべてのダッシュボード            |

---

## プロジェクトの現在の実装状況

2024 年 12 月時点で、Team Insight の MVP（最小限の実用的な製品）開発は順調に進んでいます。ここでは、何が完成していて、何がこれからなのかを明確にします。

### ✅ 実装済み機能（もう動いている！）

以下の機能はすでに実装が完了し、動作確認済みです。コードを読む際は、これらの機能から始めることをお勧めします。

```mermaid
graph LR
    subgraph "認証システム ✅"
        A1[Backlog OAuth 2.0]
        A2[JWT認証]
        A3[Cookieセッション管理]
        A4[Middleware認証]
    end

    subgraph "基本画面 ✅"
        B1[ランディングページ]
        B2[ログインページ]
        B3[コールバックページ]
        B4[ダッシュボード基盤]
        B5[個人ダッシュボード]
    end

    subgraph "バックエンドAPI ✅"
        C1[認証エンドポイント]
        C2[ユーザー管理]
        C3[トークン管理]
        C4[セキュリティ]
    end

    subgraph "UIコンポーネント ✅"
        D1[BottleneckChart]
        D2[ThroughputChart]
        D3[KpiSummary]
        D4[FilterBar]
    end

    style A1 fill:#c5e1a5
    style A2 fill:#c5e1a5
    style A3 fill:#c5e1a5
    style A4 fill:#c5e1a5
    style B1 fill:#c5e1a5
    style B2 fill:#c5e1a5
    style B3 fill:#c5e1a5
    style B4 fill:#c5e1a5
    style B5 fill:#c5e1a5
    style C1 fill:#c5e1a5
    style C2 fill:#c5e1a5
    style C3 fill:#c5e1a5
    style C4 fill:#c5e1a5
    style D1 fill:#c5e1a5
    style D2 fill:#c5e1a5
    style D3 fill:#c5e1a5
    style D4 fill:#c5e1a5
```

### 🚧 実装中/未実装機能（これから作る！）

これから実装する機能と、その優先順位を理解しておくことで、プロジェクトの全体像が見えてきます。

| 機能                     | 優先度 | 推定作業日数 | なぜ必要？                               |
| ------------------------ | ------ | ------------ | ---------------------------------------- |
| **Backlog API 連携**     | 最高   | 3-4 日       | 実際のデータを取得・分析するため         |
| **権限管理システム**     | 高     | 3-4 日       | ロールに応じた適切な情報アクセスを実現   |
| **プロジェクト選択 UI**  | 高     | 1-2 日       | 複数プロジェクトを切り替えて分析するため |
| **D3.js 高度なチャート** | 中-高  | 3-4 日       | データを直感的に理解できるようにするため |
| **エラーハンドリング**   | 中-高  | 2-3 日       | ユーザー体験の向上とデバッグの効率化     |
| **個人別ドリルダウン**   | 中     | 2-3 日       | チームメンバー個別の詳細分析             |
| **通知システム**         | 低-中  | 3-4 日       | 重要な変化をリアルタイムで把握           |

### URL 構成と画面設計

Team Insight の画面構成を理解しましょう。✅ は実装済み、🚧 は一部実装、📋 は未実装です。

```mermaid
graph TD
    subgraph "公開エリア（誰でもアクセス可能）"
        A["/ ランディングページ ✅"]
        B["/auth/login ログインページ ✅"]
        C["/auth/callback 認証コールバック ✅"]
    end

    subgraph "認証エリア（ログイン必要）"
        D["/dashboard ホーム ✅"]
        E["/dashboard/personal 個人分析 🚧"]
        F["/dashboard/project/:id プロジェクト分析 📋"]
        G["/dashboard/organization 組織分析 📋"]
        H["/projects プロジェクト一覧 ✅"]
    end

    subgraph "管理エリア（管理者のみ）"
        I["/admin/users ユーザー管理 📋"]
        J["/admin/settings 設定 📋"]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    D --> H

    style A fill:#c5e1a5
    style B fill:#c5e1a5
    style C fill:#c5e1a5
    style D fill:#c5e1a5
    style E fill:#fff9c4
    style F fill:#ffccbc
    style G fill:#ffccbc
    style H fill:#c5e1a5
    style I fill:#ffccbc
    style J fill:#ffccbc
```

---

## 全体のアーキテクチャを理解しよう

Team Insight は、モダンな Web アプリケーションの典型的な 3 層アーキテクチャを採用しています。各層の役割と、なぜこのような構成になっているかを理解することが、効率的な開発の第一歩です。

```mermaid
graph TB
    subgraph "プレゼンテーション層（ユーザーが見る部分）"
        A[Webブラウザ]
        B[Next.js Frontend<br>React 18 + TypeScript]
        C[React Components]
        D[D3.js Charts]
    end

    subgraph "ビジネスロジック層（処理の中心）"
        E[Redux Store<br>状態管理]
        F[Custom Hooks<br>ロジックの再利用]
        G[Services<br>API通信]
        H[Middleware<br>認証制御]
    end

    subgraph "データアクセス層（データの保存と取得）"
        I[FastAPI Backend<br>Python 3.11+]
        J[PostgreSQL Database]
        K[Redis Cache<br>（将来実装）]
    end

    subgraph "外部サービス"
        L[Backlog API]
    end

    A --> B
    B --> C
    C --> D
    C --> F
    F --> E
    F --> G
    G --> I
    H --> I
    I --> J
    I --> K
    I --> L

    style A fill:#e1f5fe
    style B fill:#c5e1a5
    style E fill:#d1c4e9
    style I fill:#fff9c4
    style L fill:#ffccbc
```

### なぜこのアーキテクチャなのか？

このアーキテクチャには、以下のような利点があります。それぞれの利点について、実際のコードと照らし合わせながら理解していきましょう。

#### 1. **関心の分離（Separation of Concerns）**

各層が特定の責任を持つことで、コードが整理されます。例えば、認証処理を見てみましょう：

- **Component 層**: ログインボタンの表示のみ（`LoginContent.tsx`）
- **Service 層**: API 通信の詳細（`auth.service.ts`）
- **Store 層**: 認証状態の管理（`authSlice.ts`）
- **Hook 層**: これらをつなぐロジック（`useAuth.ts`）

#### 2. **再利用性の向上**

Services や Hooks は複数の場所で使い回せます。例えば、`authService`は複数のコンポーネントから呼び出すことができ、同じ認証ロジックを何度も書く必要がありません。

#### 3. **スケーラビリティ**

各層を独立してスケールできます。例えば、ユーザー数が増えた場合：

- フロントエンドは CDN で配信
- バックエンドは複数サーバーで負荷分散
- データベースはレプリケーション

#### 4. **保守性**

どこに何があるか明確なので、新しいメンバーも理解しやすく、バグの修正や機能追加が容易です。

---

## ディレクトリ構造と各ファイルの役割

プロジェクトの構造を理解することは、効率的な開発の第一歩です。各ディレクトリとファイルの役割を詳しく見ていきましょう。

### フロントエンド構造（詳細版）

```
frontend/
├── src/
│   ├── app/                    # Next.js 13+ App Router
│   │   ├── layout.tsx         # 全体のレイアウト定義
│   │   ├── page.tsx           # ホームページ（/）
│   │   ├── providers.tsx      # Redux等のプロバイダー設定
│   │   ├── globals.css        # グローバルスタイル
│   │   │
│   │   ├── auth/              # 認証関連のページ
│   │   │   ├── login/
│   │   │   │   ├── page.tsx              # ログインページのラッパー
│   │   │   │   └── LoginContent.tsx      # ログインページの実装
│   │   │   └── callback/
│   │   │       ├── page.tsx              # コールバックページのラッパー
│   │   │       └── AuthCallbackContent.tsx # コールバック処理の実装
│   │   │
│   │   ├── dashboard/         # ダッシュボード（認証必要）
│   │   │   ├── page.tsx       # ダッシュボードのメインページ
│   │   │   ├── personal/      # 個人分析
│   │   │   │   └── page.tsx  # 個人ダッシュボード（実装済み）
│   │   │   ├── project/       # プロジェクト分析
│   │   │   │   └── [id]/     # 動的ルーティング（未実装）
│   │   │   └── organization/  # 組織分析（未実装）
│   │   │
│   │   ├── projects/          # プロジェクト一覧
│   │   │   └── page.tsx       # プロジェクト一覧ページ
│   │   │
│   │   ├── admin/             # 管理画面（未実装）
│   │   │   ├── users/         # ユーザー管理
│   │   │   └── settings/      # 設定管理
│   │   │
│   │   └── api/               # APIルート（Next.js API Routes）
│   │       ├── config.ts      # API設定
│   │       ├── dashboard/     # ダッシュボードAPI
│   │       │   └── route.ts   # GET /api/dashboard
│   │       ├── projects/      # プロジェクトAPI
│   │       │   └── route.ts   # GET /api/projects
│   │       └── teams/         # チームAPI
│   │           └── route.ts   # GET /api/teams
│   │
│   ├── components/            # 再利用可能なコンポーネント
│   │   ├── ui/               # 基本的なUIコンポーネント（shadcn/ui）
│   │   │   ├── alert.tsx     # アラートコンポーネント
│   │   │   ├── button.tsx    # ボタンコンポーネント
│   │   │   ├── card.tsx      # カードコンポーネント
│   │   │   ├── loading-spinner.tsx # ローディング表示
│   │   │   └── ...          # その他のUIコンポーネント
│   │   │
│   │   ├── Layout.tsx        # 共通レイアウト
│   │   ├── PrivateRoute.tsx  # 認証保護ルート
│   │   │
│   │   └── dashboard/        # ダッシュボード用コンポーネント
│   │       ├── BottleneckChart.tsx     # ボトルネック分析チャート（D3.js）
│   │       ├── ThroughputChart.tsx     # スループットチャート
│   │       ├── KpiSummary.tsx          # KPIサマリー
│   │       └── FilterBar.tsx           # フィルターバー
│   │
│   ├── hooks/                # カスタムフック
│   │   ├── useAuth.ts       # 認証関連のロジック
│   │   ├── use-toast.ts     # トースト通知
│   │   ├── useProjects.ts   # プロジェクト関連（未実装）
│   │   ├── useAnalytics.ts  # 分析データ関連（未実装）
│   │   └── usePermission.ts # 権限管理（未実装）
│   │
│   ├── services/            # API通信サービス
│   │   ├── auth.service.ts  # 認証API通信
│   │   ├── project.service.ts # プロジェクトAPI（未実装）
│   │   └── analytics.service.ts # 分析API（未実装）
│   │
│   ├── store/               # Redux状態管理
│   │   ├── index.ts        # ストア設定
│   │   ├── hooks.ts        # 型付きフック
│   │   └── slices/         # 各機能のスライス
│   │       ├── authSlice.ts      # 認証状態
│   │       ├── projectSlice.ts   # プロジェクト状態（未実装）
│   │       ├── analyticsSlice.ts # 分析データ状態（未実装）
│   │       └── uiSlice.ts        # UI状態（未実装）
│   │
│   ├── lib/                # ユーティリティ
│   │   ├── utils.ts        # 汎用ユーティリティ
│   │   ├── api-client.ts   # API通信の共通処理（未実装）
│   │   └── constants.ts    # 定数定義
│   │
│   ├── types/              # TypeScript型定義
│   │   ├── period.ts       # 期間関連の型
│   │   ├── api.ts         # API関連の型（未実装）
│   │   ├── models.ts      # データモデルの型（未実装）
│   │   └── index.ts       # 型のエクスポート
│   │
│   └── middleware.ts       # Next.jsミドルウェア（認証チェック）
│
├── public/                 # 静的ファイル
│   ├── images/            # 画像ファイル
│   └── favicon.ico        # ファビコン
│
├── __tests__/             # テストファイル
│   └── components/        # コンポーネントテスト
│       └── Layout.test.tsx
│
└── package.json           # 依存関係とスクリプト
```

### バックエンド構造（詳細版）

```
backend/
├── app/
│   ├── main.py              # FastAPIアプリケーションのエントリーポイント
│   │
│   ├── api/                 # APIエンドポイント
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py      # 認証関連のエンドポイント
│   │       ├── projects.py  # プロジェクト関連（未実装）
│   │       ├── analytics.py # 分析関連（未実装）
│   │       └── users.py     # ユーザー管理（未実装）
│   │
│   ├── core/               # コア機能
│   │   ├── config.py       # アプリケーション設定
│   │   ├── security.py     # セキュリティ関連（JWT等）
│   │   ├── permissions.py  # 権限管理（未実装）
│   │   └── dependencies.py # 依存性注入
│   │
│   ├── db/                 # データベース関連
│   │   ├── base.py        # SQLAlchemyベース設定
│   │   ├── base_class.py  # ベースモデルクラス
│   │   ├── session.py     # データベースセッション
│   │   └── init_db.py     # 初期データ投入
│   │
│   ├── models/             # データベースモデル
│   │   ├── __init__.py
│   │   ├── user.py        # ユーザーモデル
│   │   ├── auth.py        # 認証関連モデル（OAuthToken, OAuthState）
│   │   ├── project.py     # プロジェクトモデル（未実装）
│   │   └── analytics.py   # 分析データモデル（未実装）
│   │
│   ├── schemas/            # Pydanticスキーマ（型定義）
│   │   ├── __init__.py
│   │   ├── auth.py        # 認証関連のリクエスト/レスポンス型
│   │   ├── user.py        # ユーザー関連の型
│   │   ├── project.py     # プロジェクト関連の型（未実装）
│   │   └── analytics.py   # 分析関連の型（未実装）
│   │
│   ├── services/           # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── backlog_oauth.py    # Backlog OAuth処理
│   │   ├── backlog_api.py      # Backlog API連携（未実装）
│   │   ├── analytics_service.py # 分析サービス（未実装）
│   │   └── notification_service.py # 通知サービス（未実装）
│   │
│   └── utils/              # ユーティリティ
│       ├── __init__.py
│       └── logging.py      # ログ設定
│
├── migrations/            # Alembicマイグレーション
│   ├── versions/          # マイグレーションファイル
│   │   ├── 5333a4ae1265_create_users_and_oauth_tables.py
│   │   ├── 758e6b2ba560_move_tables_to_team_insight_schema.py
│   │   └── 926f6717b64e_create_oauth_states_table.py
│   └── alembic.ini       # Alembic設定
│
├── tests/                 # テストコード
│   ├── conftest.py       # テスト共通設定
│   ├── test_auth.py      # 認証テスト
│   ├── test_projects.py  # プロジェクトテスト（未実装）
│   └── test_analytics.py # 分析テスト（未実装）
│
├── requirements.txt       # 本番用依存関係
├── requirements-dev.txt   # 開発用依存関係
└── .env.example          # 環境変数の例
```

### 各ファイルの役割と責任

#### フロントエンド

1. **app/**: ルーティングとページコンポーネント

   ```typescript
   // app/page.tsx - ルートページの例
   export default function HomePage() {
     // ページコンポーネントはUIの表示に専念
     return <div>Welcome to Team Insight</div>;
   }
   ```

2. **components/**: 再利用可能な UI パーツ

   ```typescript
   // components/ui/button.tsx - 再利用可能なボタン
   export function Button({ children, onClick, variant = "default" }) {
     // UIロジックのみ、ビジネスロジックは含まない
     return (
       <button className={styles[variant]} onClick={onClick}>
         {children}
       </button>
     );
   }
   ```

3. **hooks/**: ロジックの再利用

   ```typescript
   // hooks/useAuth.ts - 認証ロジックをカプセル化
   export function useAuth() {
     // 状態管理とコンポーネントの橋渡し
     // 複雑なロジックを隠蔽
   }
   ```

4. **services/**: API 通信

   ```typescript
   // services/auth.service.ts - API通信の詳細を隠蔽
   class AuthService {
     async login(credentials) {
       // HTTPリクエストの詳細
       // エラーハンドリング
     }
   }
   ```

5. **store/**: アプリケーション全体の状態
   ```typescript
   // store/slices/authSlice.ts - 認証状態の管理
   const authSlice = createSlice({
     name: "auth",
     initialState: { user: null, isAuthenticated: false },
     reducers: {
       // 状態の更新ロジック
     },
   });
   ```

#### バックエンド

1. **api/**: HTTP エンドポイント

   ```python
   # api/v1/auth.py - 認証エンドポイント
   @router.post("/login")
   async def login(credentials: LoginRequest):
       # リクエストの受付と検証
       # レスポンスの整形
   ```

2. **models/**: データベーステーブル定義

   ```python
   # models/user.py - ユーザーテーブル
   class User(BaseModel):
       __tablename__ = "users"
       # カラム定義
       # リレーション定義
   ```

3. **schemas/**: データ検証

   ```python
   # schemas/auth.py - リクエスト/レスポンスの型
   class LoginRequest(BaseModel):
       username: str
       password: str
       # Pydanticが自動的に型チェック
   ```

4. **services/**: ビジネスロジック
   ```python
   # services/backlog_oauth.py - OAuth処理
   class BacklogOAuthService:
       # 複雑な認証フローの実装
       # 外部APIとの連携
   ```

---

## 実装済み機能の詳細解説

実装済みの機能について、実際のコードを見ながら、なぜそのような実装になっているかを理解していきましょう。

### 認証システムの完全理解

認証は、アプリケーションのセキュリティの要です。Team Insight は OAuth 2.0 を使用して安全な認証を実現しています。ここでは、認証フロー全体を詳しく見ていきます。

#### なぜ OAuth 2.0 を使うのか？

従来の認証方式と OAuth 2.0 の違いを理解することで、セキュリティの重要性が分かります。

```mermaid
graph LR
    subgraph "従来の認証（危険）"
        A1[ユーザー] -->|パスワード入力| B1[Team Insight]
        B1 -->|パスワード保存| C1[データベース]
        C1 -->|漏洩リスク| D1[危険！]
    end

    subgraph "OAuth 2.0（安全）"
        A2[ユーザー] -->|Backlogで認証| B2[Backlog]
        B2 -->|トークンのみ| C2[Team Insight]
        C2 -->|トークン保存| D2[安全！]
    end

    style D1 fill:#ff6b6b
    style D2 fill:#51cf66
```

OAuth 2.0 の利点：

1. **パスワードを保存しない**: Team Insight はユーザーのパスワードを知らない
2. **権限の細分化**: 必要な権限のみを要求できる
3. **取り消し可能**: ユーザーはいつでもアクセス権を取り消せる
4. **標準化**: 多くのサービスで採用されている標準的な方法

#### 認証フローの詳細

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant F as フロントエンド
    participant B as バックエンド
    participant BL as Backlog API
    participant DB as データベース

    Note over U,DB: Step 1: ログイン開始
    U->>F: ログインボタンクリック
    F->>B: GET /api/v1/auth/backlog/authorize
    B->>DB: stateを保存（CSRF対策）
    DB-->>B: 保存完了
    B-->>F: {authorization_url, state}
    F->>U: Backlogへリダイレクト

    Note over U,DB: Step 2: Backlog認証
    U->>BL: ログイン情報入力
    BL->>U: 認証・承認画面
    U->>BL: 承認
    BL-->>F: /auth/callback?code=xxx&state=yyy

    Note over U,DB: Step 3: トークン交換
    F->>B: POST /api/v1/auth/backlog/callback
    B->>DB: state検証
    DB-->>B: state有効
    B->>BL: POST /api/v2/oauth2/token (codeを送信)
    BL-->>B: {access_token, refresh_token}
    B->>BL: GET /api/v2/users/myself
    BL-->>B: ユーザー情報
    B->>DB: ユーザー作成/更新
    B->>DB: トークン保存
    B-->>F: JWT + Set-Cookie

    Note over U,DB: Step 4: 認証完了
    F->>F: Storeに保存
    F->>U: ダッシュボードへ遷移
```

#### Step 1: 認証 URL の生成（バックエンド）

```python
# backend/app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/backlog/authorize")
async def get_authorization_url(db: Session = Depends(get_db)):
    """
    Step 1: 認証URLを生成する

    なぜこの処理が必要？
    - CSRF攻撃を防ぐためのstate parameterを生成
    - Backlogの認証画面へのURLを構築
    """
    # ランダムな文字列（state）を生成
    # これにより、悪意のある第三者からの偽装リクエストを防げる
    state = secrets.token_urlsafe(32)

    # stateをデータベースに保存（10分間有効）
    # 後でコールバック時に検証するため
    oauth_state = OAuthState(
        state=state,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(oauth_state)
    db.commit()

    # Backlogの認証URLを構築
    auth_url = (
        f"https://{settings.BACKLOG_SPACE_KEY}.backlog.jp/OAuth2AccessRequest.action"
        f"?response_type=code"
        f"&client_id={settings.BACKLOG_CLIENT_ID}"
        f"&redirect_uri={settings.BACKLOG_REDIRECT_URI}"
        f"&state={state}"
    )

    return {"authorization_url": auth_url, "state": state}
```

**セキュリティポイント：**

- **state**: ランダムな文字列で、CSRF（クロスサイトリクエストフォージェリ）攻撃を防ぐ
- **有効期限**: 10 分後に自動的に無効になり、古い state の再利用を防ぐ
- **ログ**: 問題が発生した際のデバッグのため、適切にログを残す

#### Step 1: ログインページ（フロントエンド）

```typescript
// frontend/src/app/auth/login/LoginContent.tsx

"use client";

import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

export function LoginContent() {
  const { login, isAuthenticated, isInitialized } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 既にログイン済みの場合はダッシュボードへ
  useEffect(() => {
    if (isInitialized && isAuthenticated) {
      console.log("既にログイン済み、ダッシュボードへリダイレクト");
      router.push("/dashboard");
    }
  }, [isAuthenticated, isInitialized, router]);

  const handleLogin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Step 1: 認証URLを取得してリダイレクト
      console.log("🔐 ログイン処理を開始");
      await login();
      // この時点でBacklogへリダイレクトされる
    } catch (err: any) {
      console.error("❌ ログインエラー:", err);
      setError(
        err.message || "ログインに失敗しました。もう一度お試しください。"
      );
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Team Insight にログイン
          </CardTitle>
          <CardDescription className="text-center">
            Backlog アカウントでログインしてください
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full"
            size="lg"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ログイン中...
              </>
            ) : (
              <>
                <img
                  src="/backlog-logo.svg"
                  alt="Backlog"
                  className="mr-2 h-5 w-5"
                />
                Backlog でログイン
              </>
            )}
          </Button>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>ログインすることで、以下の機能が利用できます：</p>
            <ul className="mt-2 space-y-1">
              <li>✓ チームの生産性分析</li>
              <li>✓ ボトルネックの可視化</li>
              <li>✓ 個人パフォーマンスの把握</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

**UI のポイント：**

- **ローディング状態**: ユーザーに処理中であることを明確に示す
- **エラーハンドリング**: エラーが発生した場合、ユーザーに分かりやすく表示
- **アクセシビリティ**: スクリーンリーダー対応のマークアップ

#### Step 2: Backlog 認証画面

ユーザーは Backlog の認証画面で以下の操作を行います：

1. Backlog のユーザー名とパスワードを入力
2. Team Insight へのアクセス許可を確認
3. 「承認」ボタンをクリック

この部分は Backlog 側の実装なので、Team Insight では制御できません。

#### Step 3: コールバック処理（フロントエンド）

```typescript
// frontend/src/app/auth/callback/page.tsx

"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Loader2 } from "lucide-react";

export default function AuthCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { handleCallback } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      // URLパラメータから認証コードとstateを取得
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const error = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      // エラーチェック
      if (error) {
        console.error("❌ Backlog認証エラー:", error, errorDescription);
        setError(errorDescription || "認証に失敗しました");
        return;
      }

      if (!code || !state) {
        console.error("❌ 必要なパラメータが不足");
        setError("認証情報が不正です");
        return;
      }

      try {
        console.log("🔄 認証コールバック処理中...");

        // Step 3: 認証コードをバックエンドに送信
        await handleCallback(code, state);

        console.log("✅ 認証成功！ダッシュボードへ遷移");
        // 成功したらダッシュボードへ
        router.push("/dashboard");
      } catch (err: any) {
        console.error("❌ コールバック処理エラー:", err);
        setError(err.message || "認証処理に失敗しました");
      }
    };

    processCallback();
  }, [searchParams, handleCallback, router]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">認証エラー</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push("/login")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            ログインページに戻る
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
        <p className="text-gray-600">認証処理中...</p>
      </div>
    </div>
  );
}
```

**実装のポイント：**

- **二重実行防止**: `useRef`を使用して、処理が複数回実行されないようにする
- **エラーハンドリング**: ユーザーがエラーから回復できるよう、適切なアクションを提供
- **UX**: 処理中であることを明確に示し、ユーザーの不安を軽減

#### Step 3: コールバック処理（バックエンド）

```python
# backend/app/api/v1/auth.py

@router.post("/backlog/callback")
async def handle_callback(
    request: CallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Step 3: Backlog OAuth2.0認証のコールバックを処理

    処理の流れ：
    1. stateパラメータの検証（CSRF対策）
    2. 認証コードをアクセストークンに交換
    3. Backlogからユーザー情報を取得
    4. データベースにユーザーとトークンを保存
    5. JWTトークンを生成して返す
    """
    logger.info(f"認証コールバック開始 - state: {request.state}")

    # 1. stateの検証
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == request.state
    ).first()

    if not oauth_state:
        logger.error(f"無効なstateパラメータ - state: {request.state}")
        raise HTTPException(status_code=400, detail="無効なstateパラメータです")

    if oauth_state.is_expired():
        logger.error(f"stateパラメータの有効期限切れ - state: {request.state}")
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(status_code=400, detail="stateの有効期限が切れています")

    try:
        # 2. 認証コードをアクセストークンに交換
        token_data = await backlog_oauth_service.exchange_code_for_token(request.code)

        # 3. ユーザー情報を取得
        user_info = await backlog_oauth_service.get_user_info(token_data["access_token"])

        # 4. ユーザーの作成または更新
        user = db.query(User).filter(User.backlog_id == user_info["id"]).first()
        if not user:
            # 新規ユーザーの作成
            user = User(
                backlog_id=user_info["id"],
                email=user_info.get("mailAddress"),
                name=user_info["name"],
                user_id=user_info["userId"],
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # 既存ユーザーの情報を更新
            user.name = user_info["name"]
            user.email = user_info.get("mailAddress")
            db.commit()

        # 5. トークンを保存
        oauth_token = OAuthToken(
            user_id=user.id,
            provider="backlog",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        )
        db.add(oauth_token)

        # 6. 使用済みのstateを削除
        db.delete(oauth_state)
        db.commit()

        # 7. JWTトークンを生成
        access_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"認証コールバック成功 - user_id: {user.id}")

        # 8. レスポンスを作成（HttpOnlyクッキーを設定）
        return JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "backlog_id": user.backlog_id,
                    "email": user.email,
                    "name": user.name,
                    "user_id": user.user_id
                }
            },
            headers={
                "Set-Cookie": f"auth_token={access_token}; "
                             f"Path=/; HttpOnly; SameSite=Lax; "
                             f"Max-Age=604800"  # 7日間
            }
        )

    except Exception as e:
        logger.error(f"認証処理エラー: {str(e)}", exc_info=True)
        # エラー時もstateを削除（再利用を防ぐ）
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(status_code=500, detail=f"認証処理に失敗しました: {str(e)}")
```

**セキュリティのポイント：**

1. **state 検証**: CSRF 攻撃を防ぐため、必ず検証する
2. **使用済み state の削除**: 再利用攻撃を防ぐ
3. **HttpOnly クッキー**: XSS 攻撃からトークンを守る
4. **適切なエラーハンドリング**: セキュリティ情報を漏らさない

#### Step 4: JWT 認証とセッション管理

JWT（JSON Web Token）を使用して、ユーザーのセッションを管理します。

```python
# backend/app/core/security.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    JWTトークンを生成する

    なぜJWTを使うのか？
    - ステートレス: サーバー側でセッション情報を保持する必要がない
    - スケーラブル: 複数のサーバーで認証情報を共有できる
    - 自己完結的: トークン自体に必要な情報が含まれている
    """
    to_encode = data.copy()

    # 有効期限を設定（デフォルト: 7日間）
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})

    # トークンを生成（秘密鍵で署名）
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    JWTトークンを検証する

    検証項目：
    - 署名が正しいか
    - 有効期限が切れていないか
    - 必要な情報が含まれているか
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="認証情報が無効です"
        )
```

#### Middleware による認証チェック（フロントエンド）

```typescript
// frontend/src/middleware.ts

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// 認証が必要なパス
const protectedPaths = ["/dashboard", "/projects", "/admin"];

// 認証が不要なパス
const publicPaths = ["/", "/auth/login", "/auth/callback"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 認証トークンの確認
  const authToken = request.cookies.get("auth_token");

  // 保護されたパスへのアクセス時
  if (protectedPaths.some((path) => pathname.startsWith(path))) {
    if (!authToken) {
      // 認証されていない場合はログインページへリダイレクト
      const loginUrl = new URL("/auth/login", request.url);
      // リダイレクト後に元のページに戻れるようにする
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // 認証済みユーザーがログインページにアクセスした場合
  if (publicPaths.includes(pathname) && authToken) {
    // ダッシュボードへリダイレクト
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * 以下を除くすべてのパスにマッチ:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
```

### ボトルネック分析の実装

ボトルネック分析は Team Insight の中核機能の一つです。D3.js を使用して、開発プロセスの各ステージでの滞留時間を可視化します。

```typescript
// frontend/src/components/dashboard/BottleneckChart.tsx

import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface BottleneckData {
  stage: string;
  averageTime: number;
  taskCount: number;
  isBottleneck: boolean;
}

export function BottleneckChart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [data, setData] = useState<BottleneckData[]>([]);

  useEffect(() => {
    // モックデータ（実際はAPIから取得）
    const mockData: BottleneckData[] = [
      {
        stage: "要件定義",
        averageTime: 2.5,
        taskCount: 15,
        isBottleneck: false,
      },
      { stage: "設計", averageTime: 1.8, taskCount: 12, isBottleneck: false },
      { stage: "実装", averageTime: 3.2, taskCount: 45, isBottleneck: false },
      {
        stage: "コードレビュー",
        averageTime: 4.8,
        taskCount: 38,
        isBottleneck: true,
      },
      { stage: "テスト", averageTime: 2.1, taskCount: 20, isBottleneck: false },
      {
        stage: "デプロイ",
        averageTime: 0.5,
        taskCount: 10,
        isBottleneck: false,
      },
    ];
    setData(mockData);
  }, []);

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const margin = { top: 40, right: 80, bottom: 60, left: 80 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // SVGをクリア
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // スケールの設定
    const x = d3
      .scaleBand()
      .range([0, width])
      .domain(data.map((d) => d.stage))
      .padding(0.2);

    const y = d3
      .scaleLinear()
      .range([height, 0])
      .domain([0, d3.max(data, (d) => d.averageTime) || 0]);

    // X軸
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.8em")
      .attr("dy", ".15em")
      .attr("transform", "rotate(-45)");

    // Y軸
    g.append("g")
      .call(d3.axisLeft(y))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left)
      .attr("x", 0 - height / 2)
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text("平均滞留時間（日）");

    // バーの描画
    g.selectAll(".bar")
      .data(data)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", (d) => x(d.stage) || 0)
      .attr("width", x.bandwidth())
      .attr("y", (d) => y(d.averageTime))
      .attr("height", (d) => height - y(d.averageTime))
      .attr("fill", (d) => (d.isBottleneck ? "#ef4444" : "#3b82f6"))
      .on("mouseover", function (event, d) {
        // ツールチップの表示
        const tooltip = d3
          .select("body")
          .append("div")
          .attr("class", "tooltip")
          .style("opacity", 0);

        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip
          .html(
            `<strong>${d.stage}</strong><br/>
             平均時間: ${d.averageTime}日<br/>
             タスク数: ${d.taskCount}`
          )
          .style("left", event.pageX + "px")
          .style("top", event.pageY - 28 + "px");
      })
      .on("mouseout", function () {
        d3.selectAll(".tooltip").remove();
      });

    // ボトルネックの強調
    g.selectAll(".bottleneck-label")
      .data(data.filter((d) => d.isBottleneck))
      .enter()
      .append("text")
      .attr("class", "bottleneck-label")
      .attr("x", (d) => (x(d.stage) || 0) + x.bandwidth() / 2)
      .attr("y", (d) => y(d.averageTime) - 10)
      .attr("text-anchor", "middle")
      .style("fill", "#ef4444")
      .style("font-weight", "bold")
      .text("ボトルネック");
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>ボトルネック分析</CardTitle>
      </CardHeader>
      <CardContent>
        <svg ref={svgRef}></svg>
        <div className="mt-4 text-sm text-gray-600">
          <p>
            ※
            赤いバーは平均滞留時間が長く、ボトルネックとなっている可能性があります
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## フロントエンドアーキテクチャ詳説

フロントエンドは Next.js 14 の App Router を採用し、モダンな React アプリケーションのベストプラクティスに従っています。

### Redux Store の設計思想

状態管理は Redux Toolkit を使用し、予測可能で保守しやすい設計を実現しています。

```typescript
// frontend/src/store/index.ts

import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
// import projectReducer from "./slices/projectSlice"; // 未実装
// import analyticsReducer from "./slices/analyticsSlice"; // 未実装

export const store = configureStore({
  reducer: {
    auth: authReducer,
    // project: projectReducer,
    // analytics: analyticsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Dateオブジェクトなどのシリアライズ不可能な値を許可
        ignoredActions: ["auth/setUser"],
        ignoredPaths: ["auth.user.createdAt", "auth.user.updatedAt"],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### Services パターンの実装

API 通信をサービスクラスにカプセル化し、コンポーネントから実装の詳細を隠蔽します。

```typescript
// frontend/src/services/auth.service.ts

import axios from "axios";
import { API_BASE_URL } from "@/app/api/config";

interface LoginResponse {
  authorization_url: string;
  state: string;
}

interface CallbackResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    backlog_id: number;
    email: string;
    name: string;
    user_id: string;
  };
}

class AuthService {
  private baseURL = `${API_BASE_URL}/auth`;

  async getAuthorizationUrl(): Promise<LoginResponse> {
    try {
      const response = await axios.get(`${this.baseURL}/backlog/authorize`);
      return response.data;
    } catch (error) {
      console.error("認証URL取得エラー:", error);
      throw new Error("認証URLの取得に失敗しました");
    }
  }

  async handleCallback(code: string, state: string): Promise<CallbackResponse> {
    try {
      const response = await axios.post(`${this.baseURL}/backlog/callback`, {
        code,
        state,
      });
      return response.data;
    } catch (error) {
      console.error("コールバック処理エラー:", error);
      throw new Error("認証処理に失敗しました");
    }
  }

  async logout(): Promise<void> {
    try {
      await axios.post(`${this.baseURL}/logout`);
    } catch (error) {
      console.error("ログアウトエラー:", error);
      throw new Error("ログアウトに失敗しました");
    }
  }

  async getCurrentUser() {
    try {
      const response = await axios.get(`${this.baseURL}/me`);
      return response.data;
    } catch (error) {
      console.error("ユーザー情報取得エラー:", error);
      throw new Error("ユーザー情報の取得に失敗しました");
    }
  }
}

export const authService = new AuthService();
```

### カスタム Hooks の活用

ロジックを再利用可能な形でカプセル化し、コンポーネントをシンプルに保ちます。

```typescript
// frontend/src/hooks/useAuth.ts

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setUser, clearUser, setLoading } from "@/store/slices/authSlice";
import { authService } from "@/services/auth.service";

export function useAuth() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { user, isAuthenticated, isLoading, isInitialized } = useAppSelector(
    (state) => state.auth
  );

  // 初期化時にユーザー情報を取得
  useEffect(() => {
    const initAuth = async () => {
      try {
        const userData = await authService.getCurrentUser();
        dispatch(setUser(userData));
      } catch (error) {
        // 未認証の場合はエラーを無視
        dispatch(clearUser());
      } finally {
        dispatch(setLoading(false));
      }
    };

    if (!isInitialized) {
      initAuth();
    }
  }, [dispatch, isInitialized]);

  const login = useCallback(async () => {
    try {
      const { authorization_url, state } =
        await authService.getAuthorizationUrl();

      // stateをセッションストレージに保存（コールバック時に検証用）
      sessionStorage.setItem("oauth_state", state);

      // Backlogの認証画面へリダイレクト
      window.location.href = authorization_url;
    } catch (error) {
      console.error("ログインエラー:", error);
      throw error;
    }
  }, []);

  const handleCallback = useCallback(
    async (code: string, state: string) => {
      try {
        // stateの検証
        const savedState = sessionStorage.getItem("oauth_state");
        if (state !== savedState) {
          throw new Error("不正な認証リクエストです");
        }

        // 認証コードをトークンに交換
        const response = await authService.handleCallback(code, state);

        // ユーザー情報を保存
        dispatch(setUser(response.user));

        // セッションストレージをクリア
        sessionStorage.removeItem("oauth_state");

        return response;
      } catch (error) {
        console.error("コールバックエラー:", error);
        throw error;
      }
    },
    [dispatch]
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
      dispatch(clearUser());
      router.push("/");
    } catch (error) {
      console.error("ログアウトエラー:", error);
      // エラーが発生してもローカルの状態はクリア
      dispatch(clearUser());
      router.push("/");
    }
  }, [dispatch, router]);

  return {
    user,
    isAuthenticated,
    isLoading,
    isInitialized,
    login,
    logout,
    handleCallback,
  };
}
```

---

## バックエンドアーキテクチャ詳説

バックエンドは FastAPI を使用し、高性能で型安全な API を実現しています。

### FastAPI の基礎と応用

FastAPI は Python の型ヒントを活用して、自動的にバリデーション、シリアライゼーション、ドキュメント生成を行います。

```python
# backend/app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.api.v1 import auth
from app.core.config import settings
from app.db.session import engine
from app.db import base

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベーステーブルの作成
base.Base.metadata.create_all(bind=engine)

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Team Insight API",
    description="開発チームの生産性を可視化するAPIサービス",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバルエラーハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "内部サーバーエラーが発生しました"},
    )

# APIルーターの登録
app.include_router(auth.router, prefix="/api/v1")

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """APIの稼働状況を確認"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Team Insight API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### データベース設計の詳細

SQLAlchemy を使用して、型安全でメンテナブルなデータベースモデルを定義します。

```python
# backend/app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class User(Base):
    """
    ユーザーモデル

    Backlogのユーザー情報と連携し、Team Insight内での
    権限管理やデータの紐付けに使用される
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "team_insight"}

    id = Column(Integer, primary_key=True, index=True)
    backlog_id = Column(Integer, unique=True, nullable=False, index=True)
    user_id = Column(String, unique=True, nullable=False)  # BacklogのユーザーID
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, default="member")  # member, leader, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    oauth_tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"

    @property
    def is_admin(self):
        """管理者権限を持っているか"""
        return self.role == "admin"

    @property
    def is_leader(self):
        """リーダー権限以上を持っているか"""
        return self.role in ["leader", "admin"]
```

```python
# backend/app/models/auth.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class OAuthToken(Base):
    """
    OAuthトークンモデル

    Backlog APIアクセス用のトークンを保存
    """
    __tablename__ = "oauth_tokens"
    __table_args__ = {"schema": "team_insight"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)
    provider = Column(String, default="backlog")
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    user = relationship("User", back_populates="oauth_tokens")

    @property
    def is_expired(self):
        """トークンの有効期限が切れているか"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

class OAuthState(Base):
    """
    OAuth認証のstateパラメータ

    CSRF攻撃を防ぐための一時的なトークン
    """
    __tablename__ = "oauth_states"
    __table_args__ = {"schema": "team_insight"}

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def is_expired(self):
        """stateの有効期限が切れているか"""
        return datetime.utcnow() > self.expires_at
```

### セキュリティ実装の完全理解

```python
# backend/app/core/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.db.session import get_db
from app.core.security import verify_token
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    現在のユーザーを取得する依存性注入

    JWTトークンを検証し、データベースからユーザー情報を取得
    """
    token = credentials.credentials

    try:
        # トークンを検証
        payload = verify_token(token)
        user_id: int = int(payload.get("sub"))

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効な認証情報です"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証情報の検証に失敗しました"
        )

    # ユーザーを取得
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なユーザーです"
        )

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """アクティブなユーザーのみを許可"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="無効なユーザーです")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """管理者権限を持つユーザーのみを許可"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    return current_user
```

---

## D3.js によるデータ可視化

D3.js を使用して、インタラクティブで美しいデータビジュアライゼーションを実現します。

### ボトルネックチャートの実装

```typescript
// frontend/src/components/dashboard/BottleneckChart.tsx の詳細実装

import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

interface BottleneckData {
  stage: string;
  averageTime: number;
  taskCount: number;
  trend: "up" | "down" | "stable";
  details: {
    minTime: number;
    maxTime: number;
    median: number;
  };
}

export function BottleneckChart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<BottleneckData[]>([]);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  // レスポンシブ対応
  useEffect(() => {
    const handleResize = () => {
      if (svgRef.current && containerRef.current) {
        drawChart();
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [data]);

  const drawChart = () => {
    if (!svgRef.current || !containerRef.current || data.length === 0) return;

    const containerWidth = containerRef.current.clientWidth;
    const margin = { top: 40, right: 120, bottom: 80, left: 80 };
    const width = containerWidth - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // SVGをクリア
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", containerWidth)
      .attr("height", height + margin.top + margin.bottom);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // グラデーションの定義
    const defs = svg.append("defs");

    // 通常のバーのグラデーション
    const normalGradient = defs
      .append("linearGradient")
      .attr("id", "normal-gradient")
      .attr("x1", "0%")
      .attr("y1", "0%")
      .attr("x2", "0%")
      .attr("y2", "100%");

    normalGradient
      .append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#60a5fa")
      .attr("stop-opacity", 1);

    normalGradient
      .append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#3b82f6")
      .attr("stop-opacity", 1);

    // ボトルネックのグラデーション
    const bottleneckGradient = defs
      .append("linearGradient")
      .attr("id", "bottleneck-gradient")
      .attr("x1", "0%")
      .attr("y1", "0%")
      .attr("x2", "0%")
      .attr("y2", "100%");

    bottleneckGradient
      .append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#f87171")
      .attr("stop-opacity", 1);

    bottleneckGradient
      .append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#ef4444")
      .attr("stop-opacity", 1);

    // スケールの設定
    const x = d3
      .scaleBand()
      .range([0, width])
      .domain(data.map((d) => d.stage))
      .padding(0.3);

    const y = d3
      .scaleLinear()
      .range([height, 0])
      .domain([0, d3.max(data, (d) => d.averageTime) || 0])
      .nice();

    // 背景グリッドの追加
    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(
        d3
          .axisBottom(x)
          .tickSize(-height)
          .tickFormat(() => "")
      )
      .style("stroke-dasharray", "3,3")
      .style("opacity", 0.3);

    g.append("g")
      .attr("class", "grid")
      .call(
        d3
          .axisLeft(y)
          .tickSize(-width)
          .tickFormat(() => "")
      )
      .style("stroke-dasharray", "3,3")
      .style("opacity", 0.3);

    // X軸
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.8em")
      .attr("dy", ".15em")
      .attr("transform", "rotate(-45)")
      .style("font-size", "12px");

    // Y軸
    const yAxis = g.append("g").call(d3.axisLeft(y));

    yAxis
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left + 20)
      .attr("x", 0 - height / 2)
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .style("fill", "#666")
      .style("font-size", "14px")
      .text("平均滞留時間（日）");

    // ボトルネックの閾値ライン
    const threshold = d3.mean(data, (d) => d.averageTime) || 0;

    g.append("line")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", y(threshold * 1.5))
      .attr("y2", y(threshold * 1.5))
      .attr("stroke", "#ef4444")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "5,5")
      .style("opacity", 0.7);

    g.append("text")
      .attr("x", width - 5)
      .attr("y", y(threshold * 1.5) - 5)
      .attr("text-anchor", "end")
      .style("fill", "#ef4444")
      .style("font-size", "12px")
      .text("ボトルネック閾値");

    // バーの描画（アニメーション付き）
    const bars = g
      .selectAll(".bar")
      .data(data)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", (d) => x(d.stage) || 0)
      .attr("width", x.bandwidth())
      .attr("y", height)
      .attr("height", 0)
      .attr("fill", (d) =>
        d.averageTime > threshold * 1.5
          ? "url(#bottleneck-gradient)"
          : "url(#normal-gradient)"
      )
      .attr("rx", 4)
      .attr("ry", 4)
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        setSelectedStage(d.stage === selectedStage ? null : d.stage);
      });

    // アニメーション
    bars
      .transition()
      .duration(800)
      .delay((d, i) => i * 100)
      .attr("y", (d) => y(d.averageTime))
      .attr("height", (d) => height - y(d.averageTime));

    // 値ラベルの追加
    g.selectAll(".value-label")
      .data(data)
      .enter()
      .append("text")
      .attr("class", "value-label")
      .attr("x", (d) => (x(d.stage) || 0) + x.bandwidth() / 2)
      .attr("y", (d) => y(d.averageTime) - 5)
      .attr("text-anchor", "middle")
      .style("font-size", "12px")
      .style("font-weight", "bold")
      .style("opacity", 0)
      .text((d) => `${d.averageTime}日`)
      .transition()
      .duration(800)
      .delay((d, i) => i * 100 + 400)
      .style("opacity", 1);

    // トレンドインジケーター
    g.selectAll(".trend-indicator")
      .data(data)
      .enter()
      .append("text")
      .attr("class", "trend-indicator")
      .attr("x", (d) => (x(d.stage) || 0) + x.bandwidth() - 10)
      .attr("y", 20)
      .attr("text-anchor", "middle")
      .style("font-size", "16px")
      .text((d) => {
        if (d.trend === "up") return "↑";
        if (d.trend === "down") return "↓";
        return "→";
      })
      .style("fill", (d) => {
        if (d.trend === "up") return "#ef4444";
        if (d.trend === "down") return "#10b981";
        return "#6b7280";
      });

    // ツールチップ
    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("padding", "12px")
      .style("background", "rgba(0, 0, 0, 0.9)")
      .style("color", "white")
      .style("border-radius", "8px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("opacity", 0)
      .style("z-index", 1000);

    bars
      .on("mouseover", function (event, d) {
        d3.select(this).style("opacity", 0.8);

        tooltip.transition().duration(200).style("opacity", 1);
        tooltip
          .html(
            `<strong>${d.stage}</strong><br/>
             平均時間: ${d.averageTime}日<br/>
             タスク数: ${d.taskCount}<br/>
             最短: ${d.details.minTime}日<br/>
             最長: ${d.details.maxTime}日<br/>
             中央値: ${d.details.median}日`
          )
          .style("left", event.pageX + 10 + "px")
          .style("top", event.pageY - 10 + "px");
      })
      .on("mouseout", function () {
        d3.select(this).style("opacity", 1);
        tooltip.transition().duration(200).style("opacity", 0);
      });

    // クリーンアップ
    return () => {
      tooltip.remove();
    };
  };

  useEffect(() => {
    // APIからデータを取得（現在はモックデータ）
    const mockData: BottleneckData[] = [
      {
        stage: "要件定義",
        averageTime: 2.5,
        taskCount: 15,
        trend: "stable",
        details: { minTime: 1, maxTime: 5, median: 2.3 },
      },
      {
        stage: "設計",
        averageTime: 1.8,
        taskCount: 12,
        trend: "down",
        details: { minTime: 0.5, maxTime: 3, median: 1.7 },
      },
      {
        stage: "実装",
        averageTime: 3.2,
        taskCount: 45,
        trend: "stable",
        details: { minTime: 1, maxTime: 8, median: 3.0 },
      },
      {
        stage: "コードレビュー",
        averageTime: 4.8,
        taskCount: 38,
        trend: "up",
        details: { minTime: 2, maxTime: 10, median: 4.5 },
      },
      {
        stage: "テスト",
        averageTime: 2.1,
        taskCount: 20,
        trend: "down",
        details: { minTime: 1, maxTime: 4, median: 2.0 },
      },
      {
        stage: "デプロイ",
        averageTime: 0.5,
        taskCount: 10,
        trend: "stable",
        details: { minTime: 0.2, maxTime: 1, median: 0.5 },
      },
    ];
    setData(mockData);
  }, []);

  useEffect(() => {
    drawChart();
  }, [data]);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>ボトルネック分析</CardTitle>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <AlertCircle className="h-4 w-4" />
            <span>クリックして詳細を表示</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div ref={containerRef} className="w-full">
          <svg ref={svgRef}></svg>
        </div>

        {selectedStage && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold mb-2">{selectedStage}の詳細分析</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">改善案：</p>
                <ul className="list-disc list-inside mt-1">
                  <li>レビュアーの増員を検討</li>
                  <li>自動レビューツールの導入</li>
                  <li>レビュー基準の明確化</li>
                </ul>
              </div>
              <div>
                <p className="text-gray-600">関連メトリクス：</p>
                <ul className="mt-1">
                  <li>平均レビューコメント数: 12件</li>
                  <li>再レビュー率: 35%</li>
                  <li>レビュアー数: 3名</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="mt-4 flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded"
              style={{ background: "linear-gradient(#60a5fa, #3b82f6)" }}
            ></div>
            <span>正常</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded"
              style={{ background: "linear-gradient(#f87171, #ef4444)" }}
            ></div>
            <span>ボトルネック</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-red-500">↑</span>
            <span>悪化傾向</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-500">↓</span>
            <span>改善傾向</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 健康度メトリクスゲージの実装

```typescript
// frontend/src/components/dashboard/HealthGauge.tsx

import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

interface HealthGaugeProps {
  value: number; // 0-100
  title: string;
  thresholds: {
    critical: number;
    warning: number;
    good: number;
  };
}

export function HealthGauge({ value, title, thresholds }: HealthGaugeProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 200;
    const height = 160;
    const radius = Math.min(width, height) / 2 - 20;

    // SVGをクリア
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    const g = svg
      .append("g")
      .attr("transform", `translate(${width / 2},${height - 20})`);

    // 角度スケール
    const angleScale = d3
      .scaleLinear()
      .domain([0, 100])
      .range([-Math.PI / 2, Math.PI / 2]);

    // 背景アーク
    const backgroundArc = d3
      .arc()
      .innerRadius(radius - 20)
      .outerRadius(radius)
      .startAngle(-Math.PI / 2)
      .endAngle(Math.PI / 2);

    g.append("path").attr("d", backgroundArc).style("fill", "#e5e7eb");

    // カラースケール
    const colorScale = d3
      .scaleThreshold()
      .domain([thresholds.critical, thresholds.warning, thresholds.good])
      .range(["#ef4444", "#f59e0b", "#eab308", "#10b981"]);

    // 値のアーク
    const valueArc = d3
      .arc()
      .innerRadius(radius - 20)
      .outerRadius(radius)
      .startAngle(-Math.PI / 2)
      .endAngle(angleScale(0));

    const valuePath = g
      .append("path")
      .datum({ endAngle: angleScale(0) })
      .attr("d", valueArc)
      .style("fill", colorScale(value));

    // アニメーション
    valuePath
      .transition()
      .duration(1000)
      .attrTween("d", function (d) {
        const interpolate = d3.interpolate(d.endAngle, angleScale(value));
        return function (t) {
          d.endAngle = interpolate(t);
          return valueArc(d);
        };
      });

    // 目盛り
    const ticks = [0, 25, 50, 75, 100];

    g.selectAll(".tick")
      .data(ticks)
      .enter()
      .append("line")
      .attr("class", "tick")
      .attr("x1", (d) => Math.cos(angleScale(d)) * (radius - 25))
      .attr("y1", (d) => Math.sin(angleScale(d)) * (radius - 25))
      .attr("x2", (d) => Math.cos(angleScale(d)) * (radius - 30))
      .attr("y2", (d) => Math.sin(angleScale(d)) * (radius - 30))
      .style("stroke", "#9ca3af")
      .style("stroke-width", 2);

    // 目盛りラベル
    g.selectAll(".tick-label")
      .data(ticks)
      .enter()
      .append("text")
      .attr("class", "tick-label")
      .attr("x", (d) => Math.cos(angleScale(d)) * (radius - 40))
      .attr("y", (d) => Math.sin(angleScale(d)) * (radius - 40) + 5)
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .style("fill", "#6b7280")
      .text((d) => d);

    // 針
    const needle = g
      .append("line")
      .attr("x1", 0)
      .attr("y1", 0)
      .attr("x2", 0)
      .attr("y2", -radius + 30)
      .style("stroke", "#374151")
      .style("stroke-width", 3)
      .attr("transform", `rotate(${-90})`);

    needle
      .transition()
      .duration(1000)
      .attr("transform", `rotate(${angleScale(value) * (180 / Math.PI) - 90})`);

    // 中心の円
    g.append("circle").attr("r", 5).style("fill", "#374151");

    // 値のテキスト
    const valueText = g
      .append("text")
      .attr("y", -20)
      .attr("text-anchor", "middle")
      .style("font-size", "24px")
      .style("font-weight", "bold")
      .style("fill", colorScale(value))
      .text("0");

    valueText
      .transition()
      .duration(1000)
      .tween("text", function () {
        const interpolate = d3.interpolate(0, value);
        return function (t) {
          this.textContent = Math.round(interpolate(t)).toString();
        };
      });

    // タイトル
    g.append("text")
      .attr("y", 15)
      .attr("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#4b5563")
      .text(title);
  }, [value, title, thresholds]);

  return <svg ref={svgRef}></svg>;
}
```

---

## 開発環境のセットアップ

Team Insight の開発環境を構築する手順を詳しく説明します。

### 前提条件

開発を始める前に、以下のツールがインストールされていることを確認してください：

- **Node.js** (v18.0.0 以上)
- **Python** (v3.11 以上)
- **PostgreSQL** (v14 以上)
- **Git**
- **Docker** (オプション、推奨)

### Step 1: リポジトリのクローン

```bash
# リポジトリをクローン
git clone https://github.com/your-org/team-insight.git
cd team-insight
```

### Step 2: 環境変数の設定

#### バックエンド環境変数

```bash
# backend/.envファイルを作成
cd backend
cp .env.example .env
```

`.env`ファイルを編集：

```env
# データベース設定
DATABASE_URL=postgresql://teaminsight:password@localhost:5432/teaminsight

# Backlog OAuth設定
BACKLOG_SPACE_KEY=your-space-key
BACKLOG_CLIENT_ID=your-client-id
BACKLOG_CLIENT_SECRET=your-client-secret
BACKLOG_REDIRECT_URI=http://localhost:3000/auth/callback

# JWT設定
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7日間

# CORS設定
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# 環境
ENVIRONMENT=development
```

#### フロントエンド環境変数

```bash
# frontend/.env.localファイルを作成
cd ../frontend
```

`.env.local`ファイルを作成：

```env
# API設定
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# アプリケーション設定
NEXT_PUBLIC_APP_NAME=Team Insight
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Step 3: データベースのセットアップ

#### PostgreSQL の起動（Docker を使用する場合）

```bash
# プロジェクトルートで実行
docker-compose up -d postgres
```

#### データベースとスキーマの作成

```sql
-- PostgreSQLに接続
psql -U postgres

-- データベースを作成
CREATE DATABASE teaminsight;

-- teaminsightデータベースに接続
\c teaminsight

-- スキーマを作成
CREATE SCHEMA team_insight;

-- ユーザーを作成（必要に応じて）
CREATE USER teaminsight WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE teaminsight TO teaminsight;
GRANT ALL ON SCHEMA team_insight TO teaminsight;
```

### Step 4: バックエンドのセットアップ

```bash
cd backend

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# データベースマイグレーションを実行
alembic upgrade head

# 開発サーバーを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: フロントエンドのセットアップ

```bash
cd frontend

# 依存関係をインストール
npm install
# または
yarn install

# 開発サーバーを起動
npm run dev
# または
yarn dev
```

### Step 6: 動作確認

1. ブラウザで http://localhost:3000 にアクセス
2. 「Backlog でログイン」ボタンをクリック
3. Backlog の認証画面でログイン
4. ダッシュボードが表示されることを確認

### Docker を使用した開発環境

すべてのサービスを Docker で起動する場合：

```bash
# プロジェクトルートで実行
docker-compose up -d

# ログを確認
docker-compose logs -f

# サービスを停止
docker-compose down
```

### トラブルシューティング

#### データベース接続エラー

```bash
# PostgreSQLが起動しているか確認
docker-compose ps

# データベースに接続できるか確認
psql -h localhost -U teaminsight -d teaminsight
```

#### CORS エラー

バックエンドの`.env`ファイルで`BACKEND_CORS_ORIGINS`にフロントエンドの URL が含まれているか確認。

#### 認証エラー

1. Backlog のアプリケーション設定でリダイレクト URI が正しいか確認
2. 環境変数の`BACKLOG_CLIENT_ID`と`BACKLOG_CLIENT_SECRET`が正しいか確認

---

## 今後の実装計画

MVP 完成に向けて、以下の機能を段階的に実装していきます。

### フェーズ 1: Backlog API 連携（優先度: 最高）

#### 1.1 Backlog API クライアントの実装

```python
# backend/app/services/backlog_api.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx
from app.core.config import settings
from app.models.user import User
from app.models.auth import OAuthToken

class BacklogAPIClient:
    """
    Backlog APIとの通信を管理するクライアント
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = f"https://{settings.BACKLOG_SPACE_KEY}.backlog.jp/api/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def get_projects(self) -> List[Dict]:
        """プロジェクト一覧を取得"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_issues(
        self,
        project_id: int,
        status_id: Optional[List[int]] = None,
        assigned_to_id: Optional[List[int]] = None,
        created_since: Optional[datetime] = None,
        updated_since: Optional[datetime] = None
    ) -> List[Dict]:
        """課題一覧を取得"""
        params = {"projectId[]": project_id}

        if status_id:
            params["statusId[]"] = status_id
        if assigned_to_id:
            params["assigneeId[]"] = assigned_to_id
        if created_since:
            params["createdSince"] = created_since.isoformat()
        if updated_since:
            params["updatedSince"] = updated_since.isoformat()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/issues",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_issue_statuses(self, project_id: int) -> List[Dict]:
        """プロジェクトの課題ステータス一覧を取得"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/statuses",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
```

#### 1.2 データ同期サービスの実装

```python
# backend/app/services/data_sync_service.py

from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from app.services.backlog_api import BacklogAPIClient
from app.models.project import Project, Issue, IssueStatusHistory
from app.models.user import User
from app.models.auth import OAuthToken
import logging

logger = logging.getLogger(__name__)

class DataSyncService:
    """
    Backlogからデータを同期するサービス
    """

    def __init__(self, db: Session):
        self.db = db

    async def sync_user_data(self, user: User):
        """ユーザーのデータを同期"""
        # OAuthトークンを取得
        token = self.db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id
        ).first()

        if not token:
            raise ValueError("OAuthトークンが見つかりません")

        # トークンの有効期限をチェック
        if token.is_expired:
            # TODO: リフレッシュトークンで更新
            raise ValueError("アクセストークンの有効期限が切れています")

        client = BacklogAPIClient(token.access_token)

        # プロジェクトを同期
        await self._sync_projects(client, user)

        # 各プロジェクトの課題を同期
        projects = self.db.query(Project).filter(
            Project.user_id == user.id
        ).all()

        for project in projects:
            await self._sync_project_issues(client, project)

    async def _sync_projects(self, client: BacklogAPIClient, user: User):
        """プロジェクトを同期"""
        try:
            projects_data = await client.get_projects()

            for project_data in projects_data:
                # 既存のプロジェクトを検索
                project = self.db.query(Project).filter(
                    Project.backlog_id == project_data["id"],
                    Project.user_id == user.id
                ).first()

                if not project:
                    # 新規プロジェクトを作成
                    project = Project(
                        backlog_id=project_data["id"],
                        user_id=user.id,
                        name=project_data["name"],
                        key=project_data["projectKey"],
                        description=project_data.get("description"),
                        is_archived=project_data.get("archived", False)
                    )
                    self.db.add(project)
                else:
                    # 既存プロジェクトを更新
                    project.name = project_data["name"]
                    project.description = project_data.get("description")
                    project.is_archived = project_data.get("archived", False)

            self.db.commit()
            logger.info(f"プロジェクト同期完了: {len(projects_data)}件")

        except Exception as e:
            logger.error(f"プロジェクト同期エラー: {str(e)}")
            self.db.rollback()
            raise
```

### フェーズ 2: 権限管理システム（優先度: 高）

#### 2.1 ロールベースアクセス制御（RBAC）の実装

```python
# backend/app/core/permissions.py

from enum import Enum
from typing import List
from fastapi import HTTPException, status
from app.models.user import User

class Role(str, Enum):
    ADMIN = "admin"
    LEADER = "leader"
    MEMBER = "member"

class Permission(str, Enum):
    # 個人ダッシュボード
    VIEW_OWN_DASHBOARD = "view_own_dashboard"

    # プロジェクトダッシュボード
    VIEW_PROJECT_DASHBOARD = "view_project_dashboard"
    MANAGE_PROJECT_SETTINGS = "manage_project_settings"

    # 組織ダッシュボード
    VIEW_ORGANIZATION_DASHBOARD = "view_organization_dashboard"

    # ユーザー管理
    MANAGE_USERS = "manage_users"

    # システム設定
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"

# ロールと権限のマッピング
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.VIEW_OWN_DASHBOARD,
        Permission.VIEW_PROJECT_DASHBOARD,
        Permission.MANAGE_PROJECT_SETTINGS,
        Permission.VIEW_ORGANIZATION_DASHBOARD,
        Permission.MANAGE_USERS,
        Permission.MANAGE_SYSTEM_SETTINGS,
    ],
    Role.LEADER: [
        Permission.VIEW_OWN_DASHBOARD,
        Permission.VIEW_PROJECT_DASHBOARD,
        Permission.MANAGE_PROJECT_SETTINGS,
    ],
    Role.MEMBER: [
        Permission.VIEW_OWN_DASHBOARD,
    ],
}

def check_permission(user: User, permission: Permission) -> bool:
    """ユーザーが特定の権限を持っているかチェック"""
    user_permissions = ROLE_PERMISSIONS.get(Role(user.role), [])
    return permission in user_permissions

def require_permission(permission: Permission):
    """権限チェックデコレータ"""
    def decorator(func):
        async def wrapper(*args, current_user: User, **kwargs):
            if not check_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"この操作には{permission}権限が必要です"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### フェーズ 3: 高度な分析機能（優先度: 中）

#### 3.1 ボトルネック検出アルゴリズム

```python
# backend/app/services/analytics_service.py

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.project import Issue, IssueStatusHistory
import numpy as np

class AnalyticsService:
    """
    分析機能を提供するサービス
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_bottlenecks(
        self,
        project_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        ボトルネックを分析

        各ステータスでの平均滞留時間を計算し、
        異常に長い滞留時間のステータスを特定
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # ステータス履歴を取得
        status_histories = self.db.query(
            IssueStatusHistory.status_name,
            func.avg(
                func.extract('epoch', IssueStatusHistory.exited_at - IssueStatusHistory.entered_at)
            ).label('avg_duration'),
            func.count(IssueStatusHistory.id).label('count')
        ).filter(
            IssueStatusHistory.project_id == project_id,
            IssueStatusHistory.entered_at >= start_date,
            IssueStatusHistory.entered_at <= end_date,
            IssueStatusHistory.exited_at.isnot(None)
        ).group_by(
            IssueStatusHistory.status_name
        ).all()

        # 結果を整形
        results = []
        durations = []

        for history in status_histories:
            avg_days = history.avg_duration / 86400 if history.avg_duration else 0
            durations.append(avg_days)

            results.append({
                "stage": history.status_name,
                "averageTime": round(avg_days, 2),
                "taskCount": history.count,
                "isBottleneck": False  # 後で判定
            })

        # ボトルネックの判定（平均 + 1.5 * 標準偏差を超える場合）
        if durations:
            mean = np.mean(durations)
            std = np.std(durations)
            threshold = mean + 1.5 * std

            for result in results:
                if result["averageTime"] > threshold:
                    result["isBottleneck"] = True

        return results

    def calculate_velocity(
        self,
        project_id: int,
        sprint_duration_days: int = 14
    ) -> List[Dict]:
        """
        ベロシティ（完了したタスクのストーリーポイント合計）を計算
        """
        # スプリントごとの完了タスク数を集計
        sprints = []
        current_date = datetime.utcnow()

        for i in range(6):  # 過去6スプリント
            sprint_end = current_date - timedelta(days=i * sprint_duration_days)
            sprint_start = sprint_end - timedelta(days=sprint_duration_days)

            completed_count = self.db.query(func.count(Issue.id)).filter(
                Issue.project_id == project_id,
                Issue.completed_at >= sprint_start,
                Issue.completed_at < sprint_end
            ).scalar()

            sprints.append({
                "sprint": f"Sprint {6-i}",
                "startDate": sprint_start.isoformat(),
                "endDate": sprint_end.isoformat(),
                "completedTasks": completed_count,
                "velocity": completed_count * 3  # 仮のストーリーポイント
            })

        return sprints

    def calculate_cycle_time(
        self,
        project_id: int,
        days: int = 30
    ) -> Dict:
        """
        サイクルタイム（着手から完了までの時間）を計算
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 期間内に完了したタスクのサイクルタイムを取得
        issues = self.db.query(
            Issue.id,
            Issue.started_at,
            Issue.completed_at
        ).filter(
            Issue.project_id == project_id,
            Issue.completed_at >= start_date,
            Issue.completed_at <= end_date,
            Issue.started_at.isnot(None)
        ).all()

        cycle_times = []
        for issue in issues:
            cycle_time = (issue.completed_at - issue.started_at).days
            cycle_times.append(cycle_time)

        if cycle_times:
            return {
                "average": round(np.mean(cycle_times), 2),
                "median": round(np.median(cycle_times), 2),
                "p75": round(np.percentile(cycle_times, 75), 2),
                "p90": round(np.percentile(cycle_times, 90), 2),
                "count": len(cycle_times)
            }
        else:
            return {
                "average": 0,
                "median": 0,
                "p75": 0,
                "p90": 0,
                "count": 0
            }
```

### フェーズ 4: UI/UX の改善（優先度: 中）

#### 4.1 ダークモード対応

```typescript
// frontend/src/contexts/ThemeContext.tsx

import React, { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    // ローカルストレージから設定を読み込み
    const savedTheme = localStorage.getItem("theme") as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
    } else {
      // システムの設定を確認
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)"
      ).matches;
      setTheme(prefersDark ? "dark" : "light");
    }
  }, []);

  useEffect(() => {
    // テーマを適用
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
```

---

## ベストプラクティス

### コーディング規約

#### TypeScript/React

1. **コンポーネントの命名**

   - PascalCase を使用: `UserProfile.tsx`
   - 1 ファイル 1 コンポーネント

2. **型定義**
   - `interface` を優先的に使用
   - Props の型は必ず定義

```typescript
// Good
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  // ...
}
```

3. **状態管理**
   - ローカル状態は `useState`
   - グローバル状態は Redux
   - サーバー状態は React Query（将来実装）

#### Python/FastAPI

1. **型ヒントの使用**
   - すべての関数に型ヒントを追加
   - Pydantic モデルで自動バリデーション

```python
# Good
async def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()
```

2. **エラーハンドリング**
   - 適切な HTTP ステータスコードを返す
   - エラーメッセージは具体的に

```python
# Good
if not user:
    raise HTTPException(
        status_code=404,
        detail=f"ID {user_id} のユーザーが見つかりません"
    )
```

### セキュリティ

1. **認証トークンの取り扱い**

   - フロントエンド: HttpOnly Cookie で保存
   - バックエンド: 環境変数で秘密鍵を管理

2. **入力検証**

   - フロントエンド: 基本的な検証
   - バックエンド: 完全な検証（信頼境界）

3. **SQL インジェクション対策**
   - SQLAlchemy の ORM を使用
   - 生の SQL は避ける

### パフォーマンス

1. **データベースクエリの最適化**
   - N+1 問題を避ける
   - 必要なカラムのみ取得

```python
# Good - Eager Loading
users = db.query(User).options(
    joinedload(User.oauth_tokens)
).all()
```

2. **フロントエンドの最適化**
   - コンポーネントの適切な分割
   - `useMemo` と `useCallback` の活用
   - 画像の遅延読み込み

### テスト戦略

1. **単体テスト**

   - ビジネスロジックは必ずテスト
   - モックを活用

2. **統合テスト**

   - API エンドポイントのテスト
   - 認証フローのテスト

3. **E2E テスト**
   - 重要なユーザーフローをカバー
   - Cypress や Playwright を使用（将来実装）

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. CORS エラー

**症状**: ブラウザコンソールに CORS エラーが表示される

**解決方法**:

```python
# backend/app/core/config.py を確認
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",  # 別ポートで動かす場合
]
```

#### 2. データベース接続エラー

**症状**: `sqlalchemy.exc.OperationalError`

**解決方法**:

```bash
# PostgreSQLが起動しているか確認
sudo systemctl status postgresql

# 接続情報を確認
psql -h localhost -U teaminsight -d teaminsight
```

#### 3. JWT 認証エラー

**症状**: 401 Unauthorized エラー

**解決方法**:

1. ブラウザの開発者ツールで Cookie を確認
2. `auth_token` が存在するか確認
3. トークンの有効期限を確認

#### 4. Backlog API エラー

**症状**: Backlog API からエラーレスポンス

**解決方法**:

1. API キーの権限を確認
2. レート制限に達していないか確認
3. Backlog のメンテナンス情報を確認

### デバッグ Tips

1. **ログの活用**

```python
# バックエンド
import logging
logger = logging.getLogger(__name__)
logger.info("デバッグ情報")

# フロントエンド
console.log("🔍 デバッグ:", data);
```

2. **ブラウザ拡張機能**

   - React Developer Tools
   - Redux DevTools

3. **API テストツール**
   - FastAPI の自動ドキュメント: http://localhost:8000/api/docs
   - Postman や Insomnia

---

これで Team Insight の実装ガイドは完成です。このガイドを参考に、効率的で保守性の高いコードを書いていきましょう！

何か質問があれば、遠慮なく聞いてください。Happy Coding! 🚀
