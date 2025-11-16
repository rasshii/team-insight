import { QueryClient } from '@tanstack/react-query'
import { TIMING_CONSTANTS, calculateRetryDelay } from './constants/timing'

/**
 * React Queryのグローバル設定
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // データの再取得設定
      staleTime: TIMING_CONSTANTS.QUERY_STALE_TIME_MS,
      gcTime: TIMING_CONSTANTS.QUERY_GC_TIME_MS,

      // エラーハンドリング
      retry: (failureCount, error: unknown) => {
        // 認証エラー（401）とバリデーションエラー（400）はリトライしない
        const errorWithResponse = error as { response?: { status?: number } }
        if (errorWithResponse?.response?.status === 401 || errorWithResponse?.response?.status === 400) {
          return false
        }
        // 最大3回までリトライ
        return failureCount < 3
      },
      retryDelay: calculateRetryDelay,
      
      // リフォーカス時の再取得
      refetchOnWindowFocus: false, // ウィンドウフォーカス時の自動再取得を無効化
      refetchOnReconnect: true, // ネットワーク再接続時は再取得
    },
    mutations: {
      // ミューテーションのエラーハンドリング
      retry: false, // ミューテーションはリトライしない
    },
  },
})

/**
 * クエリキーの定数
 * 
 * 一貫性のあるクエリキー管理のため、定数として定義
 */
export const queryKeys = {
  // 認証関連
  auth: {
    me: ['auth', 'me'] as const,
    verify: (token: string) => ['auth', 'verify', token] as const,
  },
  
  // プロジェクト関連
  projects: {
    all: ['projects'] as const,
    list: (filters?: Record<string, unknown>) => ['projects', 'list', filters] as const,
    detail: (id: string | number) => ['projects', 'detail', id] as const,
    members: (id: string | number) => ['projects', id, 'members'] as const,
  },

  // タスク関連
  tasks: {
    all: ['tasks'] as const,
    list: (filters?: Record<string, unknown>) => ['tasks', 'list', filters] as const,
    detail: (id: string | number) => ['tasks', 'detail', id] as const,
    byProject: (projectId: string | number) => ['tasks', 'byProject', projectId] as const,
    byUser: (userId: string | number) => ['tasks', 'byUser', userId] as const,
  },

  // 同期関連
  sync: {
    status: ['sync', 'status'] as const,
    history: (filters?: Record<string, unknown>) => ['sync', 'history', filters] as const,
  },

  // 分析関連
  analytics: {
    all: ['analytics'] as const,
    dashboard: (type: 'personal' | 'project' | 'organization', id?: string | number) =>
      ['analytics', 'dashboard', type, id] as const,
    bottlenecks: (projectId: string | number, period?: string) =>
      ['analytics', 'bottlenecks', projectId, period] as const,
    throughput: (projectId: string | number, period?: string) =>
      ['analytics', 'throughput', projectId, period] as const,
  },

  // ユーザー管理
  users: {
    all: ['users'] as const,
    list: (filters?: Record<string, unknown>) => ['users', 'list', filters] as const,
    detail: (id: string | number) => ['users', 'detail', id] as const,
    roles: (id: string | number) => ['users', id, 'roles'] as const,
  },
  
  // Backlog連携
  backlog: {
    all: ['backlog'] as const,
    connection: ['backlog', 'connection'] as const,
  },
} as const

/**
 * エラーハンドリングユーティリティ
 */
export const handleQueryError = (error: unknown): string => {
  const errorWithResponse = error as {
    response?: {
      data?: { detail?: string }
      status?: number
    }
    message?: string
  }

  if (errorWithResponse?.response?.data?.detail) {
    return errorWithResponse.response.data.detail
  }

  if (errorWithResponse?.response?.status === 401) {
    return '認証が必要です'
  }

  if (errorWithResponse?.response?.status === 403) {
    return 'アクセス権限がありません'
  }

  if (errorWithResponse?.response?.status === 404) {
    return 'リソースが見つかりません'
  }

  if (errorWithResponse?.response?.status && errorWithResponse.response.status >= 500) {
    return 'サーバーエラーが発生しました'
  }

  return errorWithResponse?.message || 'エラーが発生しました'
}