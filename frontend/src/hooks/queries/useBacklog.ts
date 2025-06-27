import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { backlogService } from '@/services/backlog.service'
import { useToast } from '@/hooks/use-toast'
import { useApiMutation } from '@/hooks/useApiMutation'
import { apiClient } from '@/lib/api-client'

/**
 * Backlog連携情報を取得するフック
 */
export const useBacklogConnection = () => {
  return useQuery({
    queryKey: queryKeys.backlog.connection,
    queryFn: () => backlogService.getConnection(),
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * APIキーでBacklog連携するミューテーションフック
 */
export const useConnectBacklogApiKey = () => {
  const queryClient = useQueryClient()
  
  return useApiMutation(
    backlogService.connectWithApiKey,
    {
      successMessage: 'Backlog連携を設定しました',
      errorMessage: 'Backlog連携の設定に失敗しました',
      onSuccessCallback: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.backlog.all })
      },
    }
  )
}

/**
 * OAuthでBacklog連携するミューテーションフック
 */
export const useConnectBacklogOAuth = () => {
  const queryClient = useQueryClient()
  
  return useApiMutation(
    backlogService.connectWithOAuth,
    {
      successMessage: 'OAuth認証ページへリダイレクトします',
      errorMessage: 'OAuth認証の開始に失敗しました',
      onSuccessCallback: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.backlog.all })
      },
    }
  )
}

/**
 * Backlog連携をテストするミューテーションフック
 */
export const useTestBacklogConnection = () => {
  return useApiMutation(
    backlogService.testConnection,
    {
      successMessage: (data) => `Backlog連携テスト成功: ${data.user_info?.name}として接続されています`,
      errorMessage: 'Backlog連携テストに失敗しました',
    }
  )
}

/**
 * Backlog連携を解除するミューテーションフック
 */
export const useDisconnectBacklog = () => {
  const queryClient = useQueryClient()
  
  return useApiMutation(
    backlogService.disconnect,
    {
      successMessage: 'Backlog連携を解除しました',
      errorMessage: 'Backlog連携の解除に失敗しました',
      onSuccessCallback: () => {
        queryClient.setQueryData(queryKeys.backlog.connection, null)
        queryClient.invalidateQueries({ queryKey: queryKeys.backlog.all })
      },
    }
  )
}

/**
 * プロジェクトを同期するミューテーションフック
 */
export const useSyncBacklogProjects = () => {
  const queryClient = useQueryClient()
  
  return useApiMutation(
    backlogService.syncProjects,
    {
      successMessage: (data) => `${data.synced}件のプロジェクトを同期しました`,
      errorMessage: 'プロジェクトの同期に失敗しました',
      onSuccessCallback: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      },
    }
  )
}

/**
 * タスクを同期するミューテーションフック
 */
export const useSyncBacklogTasks = () => {
  const queryClient = useQueryClient()
  
  return useApiMutation(
    (projectId: string | number) => backlogService.syncTasks(projectId),
    {
      successMessage: (data) => `${data.synced}件のタスクを同期しました`,
      errorMessage: 'タスクの同期に失敗しました',
      onSuccessCallback: (_, projectId) => {
        queryClient.invalidateQueries({ queryKey: queryKeys.tasks.byProject(projectId) })
      },
    }
  )
}