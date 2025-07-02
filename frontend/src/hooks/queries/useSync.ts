import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { syncService } from '@/services/sync.service'
import { useToast } from '@/hooks/use-toast'

/**
 * 接続状態を取得するフック
 */
export const useConnectionStatus = () => {
  return useQuery({
    queryKey: queryKeys.sync.status,
    queryFn: () => syncService.getConnectionStatus(),
    staleTime: 30 * 1000, // 30秒
    refetchInterval: 60 * 1000, // 1分ごとに自動更新
  })
}

/**
 * 同期履歴を取得するフック
 */
export const useSyncHistory = (params?: {
  sync_type?: string
  status?: string
  days?: number
  limit?: number
  offset?: number
}) => {
  return useQuery({
    queryKey: queryKeys.sync.history(params),
    queryFn: () => syncService.getSyncHistory(params),
    staleTime: 60 * 1000, // 1分
  })
}

/**
 * ユーザータスクを同期するミューテーションフック
 */
export const useSyncUserTasks = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => syncService.syncUserTasks(),
    onSuccess: (data) => {
      // 同期履歴を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.sync.history() })
      
      // タスク一覧を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      
      toast({
        title: '同期完了',
        description: `${data.items_created || 0}件作成、${data.items_updated || 0}件更新されました`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || '同期に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * プロジェクトタスクを同期するミューテーションフック
 */
export const useSyncProjectTasks = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (projectId: number) => syncService.syncProjectTasks(projectId),
    onSuccess: (data, projectId) => {
      // 同期履歴を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.sync.history() })
      
      // プロジェクトのタスクを再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.byProject(projectId) })
      
      toast({
        title: '同期完了',
        description: `${data.items_created || 0}件作成、${data.items_updated || 0}件更新されました`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || '同期に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * 全プロジェクトを同期するミューテーションフック
 */
export const useSyncAllProjects = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => syncService.syncAllProjects(),
    onSuccess: (data) => {
      // 同期履歴を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.sync.history() })
      
      // プロジェクト一覧を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      
      toast({
        title: '同期完了',
        description: `${data.items_created || 0}件作成、${data.items_updated || 0}件更新されました`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || '同期に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * 単一の課題を同期するミューテーションフック
 */
export const useSyncSingleIssue = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (issueId: number) => syncService.syncSingleIssue(issueId),
    onSuccess: (data, issueId) => {
      // 同期履歴を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.sync.history() })
      
      // タスク詳細を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.detail(issueId) })
      
      toast({
        title: '同期完了',
        description: '課題が同期されました',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || '同期に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Backlogユーザーをインポートするミューテーションフック
 */
export const useImportBacklogUsers = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (params?: { mode?: 'all' | 'active_only'; assignDefaultRole?: boolean }) => 
      syncService.importBacklogUsers(params),
    onSuccess: (data) => {
      // ユーザー一覧を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all })
      
      // 同期履歴を再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.sync.history() })
      
      const message = `${data.created}名の新規ユーザーを作成、${data.updated}名のユーザー情報を更新しました`
      
      toast({
        title: 'インポート完了',
        description: message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'ユーザーのインポートに失敗しました',
        variant: 'destructive',
      })
    },
  })
}