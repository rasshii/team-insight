# Next.jsフロントエンドの基本

**このガイドで学べること**：
- JavaScriptとTypeScriptの基本から応用まで
- Reactの基本概念とコンポーネントの作り方
- Next.js 14 App Routerの仕組みと実装方法
- Redux ToolkitとTanStack Queryによる状態管理
- 実際のコード例を通じた実装スキル

## 🌟 はじめに：フロントエンド開発の基礎

### JavaScript → TypeScript → React → Next.js

この技術スタックの関係を理解しましょう：

```
JavaScript（基礎言語）
    ↓
TypeScript（型安全なJavaScript）
    ↓
React（UIライブラリ）
    ↓
Next.js（Reactフレームワーク）
```

### JavaScriptの基本

#### 変数と型
```javascript
// 変数の宣言
let name = "田中";        // 変更可能
const age = 25;          // 変更不可
var oldStyle = "古い";   // 使用非推奨

// データ型
const string = "文字列";
const number = 123;
const boolean = true;
const array = [1, 2, 3];
const object = { name: "田中", age: 25 };
```

#### 関数の書き方
```javascript
// 従来の関数
function greet(name) {
    return "こんにちは、" + name + "さん";
}

// アロー関数（推奨）
const greet = (name) => {
    return `こんにちは、${name}さん`;  // テンプレートリテラル
};

// 短縮形
const greet = name => `こんにちは、${name}さん`;
```

#### 重要な配列メソッド
```javascript
const numbers = [1, 2, 3, 4, 5];

// map: 各要素を変換
const doubled = numbers.map(n => n * 2);  // [2, 4, 6, 8, 10]

// filter: 条件に合う要素を抽出
const evens = numbers.filter(n => n % 2 === 0);  // [2, 4]

// find: 条件に合う最初の要素
const found = numbers.find(n => n > 3);  // 4

// reduce: 集計
const sum = numbers.reduce((acc, n) => acc + n, 0);  // 15
```

### TypeScriptの基本

TypeScriptは、JavaScriptに「型」を追加した言語です。

#### なぜTypeScriptを使うのか？
```javascript
// JavaScript（エラーが実行時まで分からない）
function add(a, b) {
    return a + b;
}
add("1", 2);  // "12" (文字列結合になってしまう！)

// TypeScript（エラーがすぐ分かる）
function add(a: number, b: number): number {
    return a + b;
}
add("1", 2);  // エラー: 引数 '1' を型 'number' に割り当てることはできません
```

#### 基本的な型定義
```typescript
// 基本型
let name: string = "田中";
let age: number = 25;
let isActive: boolean = true;

// 配列
let numbers: number[] = [1, 2, 3];
let names: Array<string> = ["田中", "佐藤"];

// オブジェクト
interface User {
    id: number;
    name: string;
    age?: number;  // ? でオプショナル
}

const user: User = {
    id: 1,
    name: "田中"
    // ageは省略可能
};

// 関数の型
type GreetFunction = (name: string) => string;
const greet: GreetFunction = (name) => `こんにちは、${name}さん`;
```

### Reactの基本概念

Reactは、UIを作るためのJavaScriptライブラリです。

#### コンポーネントとは？
```typescript
// コンポーネント = UIの部品
function Button() {
    return <button>クリック</button>;
}

// 使用
function App() {
    return (
        <div>
            <Button />
            <Button />
        </div>
    );
}
```

#### JSX（JavaScript XML）
```typescript
// JSXは、HTMLのような構文でUIを記述
const element = <h1>Hello, world!</h1>;

// 実際は以下のようなJavaScriptに変換される
const element = React.createElement('h1', null, 'Hello, world!');
```

#### Props（プロパティ）
```typescript
// 親から子へデータを渡す
interface ButtonProps {
    label: string;
    onClick: () => void;
}

function Button({ label, onClick }: ButtonProps) {
    return <button onClick={onClick}>{label}</button>;
}

// 使用
<Button label="保存" onClick={() => console.log("保存")} />
```

#### State（状態）
```typescript
import { useState } from 'react';

function Counter() {
    // useStateフックで状態を管理
    const [count, setCount] = useState(0);
    
    return (
        <div>
            <p>カウント: {count}</p>
            <button onClick={() => setCount(count + 1)}>
                +1
            </button>
        </div>
    );
}
```

## 📚 Next.js App Routerとは

Next.js 14のApp Routerは、ファイルシステムベースのルーティングとReact Server Componentsを活用した新しいアーキテクチャです。

### 主な特徴と利点

1. **ファイルベースルーティング**: URLとファイル構造が一致
   ```
   app/page.tsx → /
   app/about/page.tsx → /about
   app/blog/[id]/page.tsx → /blog/123
   ```

2. **Server Components**: デフォルトでサーバーで実行
   - 初期読み込みが高速
   - バンドルサイズが小さい
   - データベースに直接アクセス可能

3. **レイアウトシステム**: 共通部分を効率的に管理
   ```
   app/layout.tsx → 全ページ共通
   app/dashboard/layout.tsx → ダッシュボード配下で共通
   ```

4. **データフェッチの簡素化**: コンポーネント内で直接データ取得
   ```typescript
   async function Page() {
       const data = await fetch('/api/data');
       return <div>{data}</div>;
   }
   ```

## 🏗️ プロジェクト構造

```
frontend/
├── src/
│   ├── app/                    # App Router（ページ）
│   │   ├── layout.tsx          # ルートレイアウト
│   │   ├── page.tsx            # ホームページ
│   │   ├── auth/
│   │   │   ├── login/
│   │   │   │   └── page.tsx    # /auth/login
│   │   │   └── callback/
│   │   │       └── page.tsx    # /auth/callback
│   │   ├── dashboard/
│   │   │   ├── layout.tsx      # ダッシュボード共通レイアウト
│   │   │   └── personal/
│   │   │       └── page.tsx    # /dashboard/personal
│   │   └── admin/
│   │       └── users/
│   │           └── page.tsx    # /admin/users
│   ├── components/             # 再利用可能なコンポーネント
│   │   ├── ui/                 # shadcn/ui コンポーネント
│   │   ├── common/             # 共通コンポーネント
│   │   └── features/           # 機能別コンポーネント
│   ├── hooks/                  # カスタムフック
│   │   └── queries/            # TanStack Query フック
│   ├── store/                  # Redux ストア
│   │   ├── index.ts            # ストア設定
│   │   └── slices/             # 各スライス
│   ├── services/               # APIクライアント
│   ├── types/                  # TypeScript型定義
│   └── lib/                    # ユーティリティ関数
├── public/                     # 静的ファイル
└── package.json
```

## 🚀 Next.jsアプリケーションの構築 - ステップバイステップ

### ステップ1: ルートレイアウトの理解

レイアウトは、複数のページで共通する UI を定義します。

```tsx
// src/app/layout.tsx - すべてのページの基盤
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from '@/components/providers'
import '@/styles/globals.css'

// フォントの設定
// Next.jsは自動的にフォントを最適化
const inter = Inter({ 
  subsets: ['latin'],  // 使用する文字セット
  display: 'swap',     // フォント読み込み中の表示方法
})

// メタデータ（SEO対策）
export const metadata: Metadata = {
  title: 'Team Insight',
  description: 'Backlogデータを活用したチーム分析ツール',
  keywords: ['プロジェクト管理', '生産性', 'Backlog'],
  openGraph: {
    title: 'Team Insight',
    description: 'チームの生産性を可視化',
    type: 'website',
  },
}

// ルートレイアウトコンポーネント
export default function RootLayout({
  children,  // ページコンテンツが入る
}: {
  children: React.ReactNode  // Reactの要素なら何でも
}) {
  return (
    <html lang="ja">
      <body className={inter.className}>
        {/* ProvidersでReduxやReact Queryを設定 */}
        <Providers>
          {/* ここに各ページの内容が入る */}
          {children}
        </Providers>
      </body>
    </html>
  )
}
```

**重要なポイント**：
1. `layout.tsx`は**削除されない** - ページ遷移しても維持される
2. `children`には各ページの`page.tsx`の内容が入る
3. メタデータはSEOに重要

### ステップ2: ページの作成方法

```tsx
// src/app/page.tsx - ホームページ（/）
export default function HomePage() {
  return (
    <main className="min-h-screen">
      <h1 className="text-4xl font-bold">
        Team Insightへようこそ
      </h1>
    </main>
  )
}

// src/app/about/page.tsx - アバウトページ（/about）
export default function AboutPage() {
  return (
    <div>
      <h1>Team Insightについて</h1>
      <p>チームの生産性を可視化するツールです</p>
    </div>
  )
}
```

### ステップ3: 動的ルートの作成

```tsx
// src/app/projects/[id]/page.tsx
// URLパラメータを受け取るページ

interface Props {
  params: { id: string }  // [id]の部分が入る
}

export default function ProjectDetailPage({ params }: Props) {
  // /projects/123 → params.id = "123"
  return (
    <div>
      <h1>プロジェクトID: {params.id}</h1>
    </div>
  )
}

// さらに複雑な例
// src/app/projects/[projectId]/tasks/[taskId]/page.tsx
interface Props {
  params: {
    projectId: string
    taskId: string
  }
}

export default function TaskDetailPage({ params }: Props) {
  // /projects/123/tasks/456
  // params.projectId = "123"
  // params.taskId = "456"
  return (
    <div>
      <h1>プロジェクト {params.projectId} のタスク {params.taskId}</h1>
    </div>
  )
}
```

### ステップ4: Providersコンポーネントの理解

Providersは、アプリ全体で使う機能を提供する重要なコンポーネントです。

```tsx
// src/components/providers.tsx
'use client'  // クライアントコンポーネントの宣言

import { Provider as ReduxProvider } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { store } from '@/store'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  // QueryClientの設定
  // useStateを使う理由：Next.jsのSSR/CSRで同じインスタンスを使うため
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // データが「新鮮」とみなされる時間
            staleTime: 60 * 1000, // 1分間はキャッシュを使用
            
            // ウィンドウにフォーカスが戻った時の再取得
            refetchOnWindowFocus: false,
            
            // エラー時のリトライ回数
            retry: 3,
            
            // リトライの待機時間
            retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
          },
        },
      })
  )

  return (
    // Redux Storeを提供
    <ReduxProvider store={store}>
      {/* React Queryクライアントを提供 */}
      <QueryClientProvider client={queryClient}>
        {children}
        {/* 開発環境でのデバッグツール */}
        <ReactQueryDevtools 
          initialIsOpen={false}  // 初期状態は閉じている
          position="bottom-right" // 表示位置
        />
      </QueryClientProvider>
    </ReduxProvider>
  )
}
```

**なぜ'use client'が必要？**
- Server Components（デフォルト）ではブラウザ機能が使えない
- Redux/React QueryはブラウザのStateを扱うため、Client Componentにする必要がある

## 📄 コンポーネントの作成 - 実践編

### Server Component vs Client Component

Next.js 14では、コンポーネントは2種類あります：

| 種類 | Server Component | Client Component |
|------|-----------------|------------------|
| デフォルト | ✅ | 'use client'が必要 |
| 実行場所 | サーバー | ブラウザ |
| useState/useEffect | ❌ 使えない | ✅ 使える |
| イベントハンドラ | ❌ 使えない | ✅ 使える |
| データ取得 | 直接可能 | useEffectやReact Query |
| パフォーマンス | 高速（HTML送信） | インタラクティブ |

### 基本的なページ（Server Component）

```tsx
// src/app/projects/page.tsx
import { ProjectList } from '@/components/features/projects/ProjectList'

// async/awaitが使える！
async function getProjectsCount() {
  const res = await fetch('http://localhost:8000/api/v1/projects/count')
  return res.json()
}

export default async function ProjectsPage() {
  // サーバーで実行される
  const count = await getProjectsCount()
  
  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">
          プロジェクト一覧 ({count}件)
        </h1>
        {/* Client Componentを埋め込む */}
        <CreateProjectButton />
      </div>
      <ProjectList />
    </div>
  )
}
```

### インタラクティブなコンポーネント（Client Component）

```tsx
// src/components/features/projects/ProjectList.tsx
'use client'  // これがClient Componentの印

import { useState } from 'react'
import { useProjects } from '@/hooks/queries/useProjects'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Search } from 'lucide-react'  // アイコンライブラリ

export function ProjectList() {
  // Client Componentではフックが使える
  const [searchTerm, setSearchTerm] = useState('')
  const { data, isLoading, error } = useProjects()

  // ローディング状態の表示
  if (isLoading) {
    return <ProjectListSkeleton />
  }

  // エラー状態の表示
  if (error) {
    return <ProjectListError error={error} />
  }

  // 検索フィルタリング
  const filteredProjects = data?.projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-4">
      {/* 検索ボックス */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <input
          type="text"
          placeholder="プロジェクトを検索..."
          className="pl-10 pr-4 py-2 w-full border rounded-lg"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* プロジェクト一覧 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredProjects?.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>

      {/* 検索結果が0件の場合 */}
      {filteredProjects?.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          「{searchTerm}」に一致するプロジェクトが見つかりません
        </div>
      )}
    </div>
  )
}

// プロジェクトカードコンポーネント
function ProjectCard({ project }: { project: Project }) {
  const [isHovered, setIsHovered] = useState(false)
  
  return (
    <Card 
      className="transition-shadow hover:shadow-lg cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          {project.name}
          {isHovered && <span className="text-sm">→</span>}
        </CardTitle>
        <CardDescription>{project.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex justify-between text-sm text-gray-600">
          <span>メンバー: {project.member_count}名</span>
          <span>タスク: {project.task_count}件</span>
        </div>
      </CardContent>
    </Card>
  )
}

// スケルトンローディング
function ProjectListSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {[...Array(6)].map((_, i) => (
        <Skeleton key={i} className="h-32" />
      ))}
    </div>
  )
}

// エラー表示
function ProjectListError({ error }: { error: Error }) {
  return (
    <div className="text-center py-8">
      <p className="text-red-500 mb-4">
        エラーが発生しました: {error.message}
      </p>
      <Button onClick={() => window.location.reload()}>
        再読み込み
      </Button>
    </div>
  )
}
```

### コンポーネント設計のベストプラクティス

1. **単一責任の原則**
   ```tsx
   // ❌ 悪い例：1つのコンポーネントで全部やる
   function ProjectPage() {
     // データ取得、表示、編集、削除...全部
   }

   // ✅ 良い例：責任を分割
   function ProjectPage() {
     return (
       <>
         <ProjectList />
         <CreateProjectButton />
       </>
     )
   }
   ```

2. **Props の型定義**
   ```tsx
   // 必ず型を定義する
   interface ProjectCardProps {
     project: Project
     onEdit?: (id: string) => void
     onDelete?: (id: string) => void
   }

   function ProjectCard({ project, onEdit, onDelete }: ProjectCardProps) {
     // ...
   }
   ```

3. **カスタムフックの活用**
   ```tsx
   // ロジックをカスタムフックに抽出
   function useProjectSearch(projects: Project[]) {
     const [searchTerm, setSearchTerm] = useState('')
     
     const filteredProjects = useMemo(
       () => projects.filter(p => 
         p.name.toLowerCase().includes(searchTerm.toLowerCase())
       ),
       [projects, searchTerm]
     )
     
     return { searchTerm, setSearchTerm, filteredProjects }
   }
   ```

## 🔄 状態管理の詳細解説

### なぜ2つの状態管理ツールを使うのか？

Team Insightでは、状態の性質によって使い分けています：

1. **Redux Toolkit** → クライアント状態（アプリ内の状態）
   - ユーザー情報、テーマ、言語設定など
   - ページをまたいで保持したい情報

2. **TanStack Query** → サーバー状態（APIのデータ）
   - プロジェクト一覧、タスク情報など
   - キャッシュや同期が重要なデータ

### Redux Toolkit - ステップバイステップ

#### ステップ1: Sliceの作成

```tsx
// src/store/slices/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { User } from '@/types/user'

// 1. 状態の型を定義
interface AuthState {
  user: User | null           // ログインユーザー情報
  isAuthenticated: boolean    // ログイン済みか
  loading: boolean           // 認証確認中か
}

// 2. 初期状態を定義
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  loading: true,  // 最初は確認中
}

// 3. Sliceを作成（状態とアクションをまとめたもの）
const authSlice = createSlice({
  name: 'auth',  // スライスの名前
  initialState,  // 初期状態
  reducers: {    // 状態を更新する関数たち
    // ユーザー情報をセット
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload
      state.isAuthenticated = !!action.payload  // nullならfalse
      state.loading = false
    },
    
    // ログアウト
    logout: (state) => {
      state.user = null
      state.isAuthenticated = false
    },
    
    // ローディング状態を設定
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    }
  },
})

// 4. アクションとリデューサーをエクスポート
export const { setUser, logout, setLoading } = authSlice.actions
export default authSlice.reducer
```

#### ステップ2: Storeの設定

```tsx
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'

// Storeを作成
export const store = configureStore({
  reducer: {
    auth: authReducer,
    // 他のスライスもここに追加
  },
})

// TypeScript用の型定義
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// 型付きフックを作成（TypeScriptで使いやすくするため）
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector
```

#### ステップ3: コンポーネントでの使用

```tsx
// src/components/common/UserMenu.tsx
'use client'

import { useAppSelector, useAppDispatch } from '@/store'
import { logout } from '@/store/slices/authSlice'
import { useRouter } from 'next/navigation'

export function UserMenu() {
  // 状態を取得
  const { user, isAuthenticated } = useAppSelector(state => state.auth)
  
  // アクションを実行する関数を取得
  const dispatch = useAppDispatch()
  const router = useRouter()
  
  const handleLogout = async () => {
    // APIを呼んでログアウト
    await fetch('/api/v1/auth/logout', { method: 'POST' })
    
    // Redux状態を更新
    dispatch(logout())
    
    // ログインページへリダイレクト
    router.push('/auth/login')
  }
  
  if (!isAuthenticated) {
    return <LoginButton />
  }
  
  return (
    <div className="flex items-center gap-4">
      <span>こんにちは、{user?.name}さん</span>
      <button onClick={handleLogout}>ログアウト</button>
    </div>
  )
}
```

### TanStack Query - APIデータ管理の詳細

#### 基本概念

TanStack Query（旧React Query）は、サーバー状態を管理するための強力なライブラリです。

**主な機能**：
- 自動的なデータキャッシュ
- バックグラウンドでの再取得
- 楽観的更新
- 並列・依存クエリ
- エラーハンドリング

#### ステップ1: APIサービスの作成

```tsx
// src/services/projectService.ts
import { apiClient } from '@/lib/api-client'
import { Project, ProjectCreate, ProjectUpdate } from '@/types/project'

export const projectService = {
  // プロジェクト一覧取得
  async getProjects(): Promise<{ projects: Project[] }> {
    const response = await apiClient.get('/api/v1/projects')
    return response.data
  },

  // プロジェクト詳細取得
  async getProject(id: string): Promise<Project> {
    const response = await apiClient.get(`/api/v1/projects/${id}`)
    return response.data
  },

  // プロジェクト作成
  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await apiClient.post('/api/v1/projects', data)
    return response.data
  },

  // プロジェクト更新
  async updateProject(id: string, data: ProjectUpdate): Promise<Project> {
    const response = await apiClient.put(`/api/v1/projects/${id}`, data)
    return response.data
  },

  // プロジェクト削除
  async deleteProject(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/projects/${id}`)
  },
}
```

#### ステップ2: カスタムフックの作成

```tsx
// src/hooks/queries/useProjects.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectService } from '@/services/projectService'
import { ProjectCreate, ProjectUpdate } from '@/types/project'
import { toast } from '@/components/ui/use-toast'

// 1. プロジェクト一覧取得
export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],  // キャッシュのキー
    queryFn: projectService.getProjects,  // データ取得関数
    staleTime: 5 * 60 * 1000,  // 5分間は「新鮮」とみなす
    gcTime: 10 * 60 * 1000,    // 10分後にガベージコレクション（旧cacheTime）
    refetchOnMount: 'always',   // マウント時に常に再取得
  })
}

// 2. 特定のプロジェクト取得
export const useProject = (projectId: string) => {
  return useQuery({
    queryKey: ['projects', projectId],  // プロジェクトIDを含める
    queryFn: () => projectService.getProject(projectId),
    enabled: !!projectId,  // projectIdがある時のみ実行
  })
}

// 3. プロジェクト作成
export const useCreateProject = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProjectCreate) => 
      projectService.createProject(data),
    
    // 成功時の処理
    onSuccess: (newProject) => {
      // プロジェクト一覧のキャッシュを無効化（再取得）
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      
      // 新しいプロジェクトをキャッシュに追加（即座に表示）
      queryClient.setQueryData(['projects', newProject.id], newProject)
      
      // 成功通知
      toast({
        title: '成功',
        description: 'プロジェクトを作成しました',
      })
    },
    
    // エラー時の処理
    onError: (error: Error) => {
      toast({
        title: 'エラー',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

// 4. プロジェクト更新（楽観的更新の例）
export const useUpdateProject = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProjectUpdate }) =>
      projectService.updateProject(id, data),
    
    // 楽観的更新：サーバーレスポンスを待たずにUIを更新
    onMutate: async ({ id, data }) => {
      // 進行中の再取得をキャンセル
      await queryClient.cancelQueries({ queryKey: ['projects', id] })
      
      // 現在のデータを保存（エラー時のロールバック用）
      const previousProject = queryClient.getQueryData(['projects', id])
      
      // 楽観的にキャッシュを更新
      queryClient.setQueryData(['projects', id], (old: any) => ({
        ...old,
        ...data,
      }))
      
      // ロールバック用のデータを返す
      return { previousProject }
    },
    
    // エラー時：元のデータに戻す
    onError: (err, variables, context) => {
      if (context?.previousProject) {
        queryClient.setQueryData(
          ['projects', variables.id],
          context.previousProject
        )
      }
      toast({
        title: 'エラー',
        description: '更新に失敗しました',
        variant: 'destructive',
      })
    },
    
    // 成功時：サーバーデータで確定
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects', variables.id] })
    },
  })
}

// 5. 並列クエリの例
export const useProjectsWithTasks = (projectIds: string[]) => {
  const results = useQueries({
    queries: projectIds.map(id => ({
      queryKey: ['projects', id, 'with-tasks'],
      queryFn: async () => {
        const project = await projectService.getProject(id)
        const tasks = await taskService.getProjectTasks(id)
        return { project, tasks }
      },
    })),
  })
  
  return results
}
```

#### ステップ3: コンポーネントでの使用例

```tsx
// src/components/features/projects/CreateProjectDialog.tsx
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useCreateProject } from '@/hooks/queries/useProjects'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function CreateProjectDialog() {
  const [open, setOpen] = useState(false)
  const createMutation = useCreateProject()
  const { register, handleSubmit, reset, formState: { errors } } = useForm()

  const onSubmit = async (data: any) => {
    // mutateAsync を使うと Promise が返る
    try {
      await createMutation.mutateAsync(data)
      setOpen(false)
      reset()
    } catch (error) {
      // エラーハンドリングはuseMutationで設定済み
    }
  }

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        新規プロジェクト
      </Button>
      
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>プロジェクトを作成</DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="name">プロジェクト名</Label>
              <Input
                id="name"
                {...register('name', { required: '必須項目です' })}
                disabled={createMutation.isPending}
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>
            
            <Button 
              type="submit" 
              disabled={createMutation.isPending}
              className="w-full"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  作成中...
                </>
              ) : (
                '作成'
              )}
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}
```

**TanStack Queryのベストプラクティス**：

1. **queryKeyの設計**
   ```typescript
   // 階層的なキー構造
   ['projects']                    // 全プロジェクト
   ['projects', projectId]         // 特定のプロジェクト
   ['projects', projectId, 'tasks'] // プロジェクトのタスク
   ```

2. **エラーバウンダリーとの組み合わせ**
   ```typescript
   // グローバルエラーハンドリング
   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         throwOnError: true,  // エラーバウンダリーでキャッチ
       },
     },
   })
   ```

3. **データの事前取得**
   ```typescript
   // ホバー時に事前取得
   const prefetchProject = (id: string) => {
     queryClient.prefetchQuery({
       queryKey: ['projects', id],
       queryFn: () => projectService.getProject(id),
     })
   }
   ```

## 🎨 UIコンポーネント（shadcn/ui）- 詳細解説

### shadcn/uiとは？

shadcn/uiは、Radix UIとTailwind CSSを使った、コピー＆ペースト可能なUIコンポーネントライブラリです。

**特徴**：
- コンポーネントのソースコードを直接プロジェクトに追加
- カスタマイズが簡単
- アクセシビリティ対応（Radix UI）
- Tailwind CSSでスタイリング

### Tailwind CSSの基本

Tailwind CSSは、クラス名でスタイリングするユーティリティファーストのCSSフレームワークです。

```tsx
// 従来のCSS
<div style={{ padding: '16px', margin: '8px', backgroundColor: '#3B82F6' }}>
  <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>タイトル</h1>
</div>

// Tailwind CSS
<div className="p-4 m-2 bg-blue-500">
  <h1 className="text-2xl font-bold">タイトル</h1>
</div>
```

**よく使うクラス**：
```tsx
// スペーシング
p-4      // padding: 1rem (16px)
m-2      // margin: 0.5rem (8px)
mt-4     // margin-top: 1rem
px-6     // padding-left/right: 1.5rem

// テキスト
text-sm   // font-size: 0.875rem
text-2xl  // font-size: 1.5rem
font-bold // font-weight: 700
text-gray-600 // color: rgb(75 85 99)

// レイアウト
flex      // display: flex
grid      // display: grid
grid-cols-3 // 3列のグリッド
gap-4     // gap: 1rem

// レスポンシブ
md:flex   // 768px以上でflex
lg:grid-cols-4 // 1024px以上で4列
```

### コンポーネントの追加と使用

```bash
# shadcn/uiコンポーネントを追加
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
npx shadcn-ui@latest add select
npx shadcn-ui@latest add toast
```

追加されたコンポーネントは`src/components/ui/`に配置されます。

### 実践例：完全なフォームコンポーネント

shadcn/ui、React Hook Form、Zodを組み合わせた実装例を詳しく解説します。

```tsx
// src/components/features/projects/CreateProjectDialog.tsx
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
// shadcn/uiコンポーネント
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { useCreateProject } from '@/hooks/queries/useProjects'
import { PlusCircle, Loader2 } from 'lucide-react'

// ステップ1: バリデーションスキーマの定義（Zod）
const formSchema = z.object({
  name: z
    .string()
    .min(1, 'プロジェクト名は必須です')
    .max(100, '100文字以内で入力してください'),
  
  description: z
    .string()
    .max(1000, '1000文字以内で入力してください')
    .optional(),
  
  backlogProjectKey: z
    .string()
    .regex(/^[A-Z][A-Z0-9_]*$/, 'プロジェクトキーは大文字英数字とアンダースコアのみ')
    .optional()
    .or(z.literal('')),  // 空文字も許可
  
  visibility: z.enum(['public', 'private']),
  
  autoSync: z.boolean().default(false),
})

// 型を自動生成
type FormData = z.infer<typeof formSchema>

export function CreateProjectDialog() {
  const [open, setOpen] = useState(false)
  const createMutation = useCreateProject()

  // ステップ2: React Hook Formの設定
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),  // Zodスキーマと連携
    defaultValues: {
      name: '',
      description: '',
      backlogProjectKey: '',
      visibility: 'private',
      autoSync: false,
    },
  })

  // ステップ3: 送信処理
  const onSubmit = async (data: FormData) => {
    try {
      await createMutation.mutateAsync(data)
      setOpen(false)
      form.reset()  // フォームをリセット
    } catch (error) {
      // エラーはTanStack QueryのonErrorで処理
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <PlusCircle className="mr-2 h-4 w-4" />
          新規プロジェクト
        </Button>
      </DialogTrigger>
      
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>プロジェクトを作成</DialogTitle>
          <DialogDescription>
            新しいプロジェクトを作成します。Backlogと連携する場合はプロジェクトキーを入力してください。
          </DialogDescription>
        </DialogHeader>
        
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* プロジェクト名 */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    プロジェクト名 <span className="text-red-500">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="新規プロジェクト" 
                      {...field} 
                      disabled={createMutation.isPending}
                    />
                  </FormControl>
                  <FormDescription>
                    プロジェクトの表示名を入力してください
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            {/* 説明 */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>説明</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="プロジェクトの目的や概要を記載"
                      className="resize-none"
                      rows={4}
                      {...field}
                      disabled={createMutation.isPending}
                    />
                  </FormControl>
                  <FormDescription>
                    最大1000文字まで入力できます
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            {/* Backlogプロジェクトキー */}
            <FormField
              control={form.control}
              name="backlogProjectKey"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Backlogプロジェクトキー</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="PROJ123" 
                      {...field}
                      disabled={createMutation.isPending}
                    />
                  </FormControl>
                  <FormDescription>
                    Backlogと連携する場合のプロジェクトキー
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            {/* 公開設定 */}
            <FormField
              control={form.control}
              name="visibility"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>公開設定</FormLabel>
                  <Select 
                    onValueChange={field.onChange} 
                    defaultValue={field.value}
                    disabled={createMutation.isPending}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="公開設定を選択" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="private">
                        <div className="flex items-center">
                          <span>🔒 プライベート</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="public">
                        <div className="flex items-center">
                          <span>🌍 パブリック</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    プロジェクトの公開範囲を設定します
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            {/* 自動同期 */}
            <FormField
              control={form.control}
              name="autoSync"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      disabled={createMutation.isPending}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel>
                      Backlogと自動同期
                    </FormLabel>
                    <FormDescription>
                      有効にすると、Backlogのデータを定期的に同期します
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />
            
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setOpen(false)}
                disabled={createMutation.isPending}
              >
                キャンセル
              </Button>
              <Button 
                type="submit" 
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    作成中...
                  </>
                ) : (
                  '作成'
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

**重要なポイント**：

1. **Zodによるバリデーション**
   - 型安全なバリデーション
   - エラーメッセージのカスタマイズ
   - 複雑な条件も表現可能

2. **React Hook Form**
   - パフォーマンスの最適化（再レンダリング最小化）
   - フォーム状態の一元管理
   - バリデーションエラーの自動表示

3. **shadcn/uiの活用**
   - アクセシブルなUIコンポーネント
   - 一貫したデザイン
   - カスタマイズが容易

4. **ユーザビリティ**
   - ローディング状態の表示
   - 必須項目の明示
   - ヘルプテキストの提供
   - 適切なエラーメッセージ

## 🔒 型安全性

TypeScriptを活用して、型安全な開発を実現しています。

### API レスポンス型

```tsx
// src/types/api/response.ts
export interface ApiResponse<T> {
  success: boolean
  data: T
  error?: {
    code: string
    message: string
  }
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}
```

### 型ガード関数

```tsx
// src/lib/type-guards.ts
import { User } from '@/types/user'

export function isUser(obj: any): obj is User {
  return (
    obj &&
    typeof obj.id === 'string' &&
    typeof obj.email === 'string' &&
    typeof obj.name === 'string'
  )
}

// 使用例
const data = await fetchData()
if (isUser(data)) {
  // dataはUser型として扱われる
  console.log(data.email)
}
```

## 🛠️ 開発のベストプラクティス

### 1. ファイル構成の一貫性

```tsx
// コンポーネントファイルの基本構造
// 1. インポート
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

// 2. 型定義
interface Props {
  title: string
  onSubmit: (data: FormData) => void
}

// 3. コンポーネント定義
export function MyComponent({ title, onSubmit }: Props) {
  // 4. フック
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  // 5. ハンドラー関数
  const handleSubmit = async () => {
    // 処理
  }

  // 6. レンダリング
  return <div>{/* JSX */}</div>
}
```

### 2. エラーハンドリング

```tsx
// src/components/common/ErrorBoundary.tsx
'use client'

import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="text-center p-8">
            <h2 className="text-xl font-bold text-red-600">
              エラーが発生しました
            </h2>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
            >
              再試行
            </button>
          </div>
        )
      )
    }

    return this.props.children
  }
}
```

### 3. パフォーマンス最適化

```tsx
// メモ化による再レンダリング防止
import { memo, useMemo, useCallback } from 'react'

const ExpensiveList = memo(({ items }: { items: Item[] }) => {
  // 重い計算はuseMemoでメモ化
  const sortedItems = useMemo(
    () => items.sort((a, b) => b.score - a.score),
    [items]
  )

  // 関数はuseCallbackでメモ化
  const handleClick = useCallback((id: string) => {
    console.log('Clicked:', id)
  }, [])

  return (
    <ul>
      {sortedItems.map((item) => (
        <li key={item.id} onClick={() => handleClick(item.id)}>
          {item.name}
        </li>
      ))}
    </ul>
  )
})
```

## 🔍 デバッグのコツ

1. **React Developer Tools**
   - コンポーネントツリーの確認
   - Props/Stateの検査
   - パフォーマンスプロファイリング

2. **Console.logの活用**
   ```tsx
   // グループ化してログを見やすく
   console.group('User Data')
   console.log('User:', user)
   console.log('Permissions:', permissions)
   console.groupEnd()
   ```

3. **ネットワークタブ**
   - APIリクエスト/レスポンスの確認
   - タイミングの分析
   - エラーレスポンスの詳細確認

---

次は[認証システムの詳細](05-authentication.md)で、Team Insightの認証フローを詳しく学びましょう！