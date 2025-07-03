/**
 * ユーザー設定関連のカスタムフック
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { userSettingsService } from '@/services/user-settings.service'
import { UserSettingsUpdate } from '@/types/user-settings'
import { toast } from '@/components/ui/use-toast'

const QUERY_KEYS = {
  settings: ['user', 'settings'],
  loginHistory: (page: number) => ['user', 'login-history', page],
  activityLogs: (page: number, action?: string) => ['user', 'activity-logs', page, action],
  sessions: ['user', 'sessions'],
}

/**
 * ユーザー設定を取得するフック
 */
export const useUserSettings = () => {
  return useQuery({
    queryKey: QUERY_KEYS.settings,
    queryFn: () => userSettingsService.getMySettings(),
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * ユーザー設定を更新するミューテーション
 */
export const useUpdateUserSettings = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (settings: UserSettingsUpdate) =>
      userSettingsService.updateMySettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(QUERY_KEYS.settings, data)
      queryClient.invalidateQueries({ queryKey: ['user'] })
      toast({
        title: '設定を更新しました',
        variant: 'default',
      })
    },
    onError: (error: any) => {
      toast({
        title: '設定の更新に失敗しました',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      })
    },
  })
}

/**
 * ログイン履歴を取得するフック
 */
export const useLoginHistory = (page: number = 1, pageSize: number = 20) => {
  return useQuery({
    queryKey: QUERY_KEYS.loginHistory(page),
    queryFn: () => userSettingsService.getLoginHistory(page, pageSize),
    keepPreviousData: true,
  })
}

/**
 * アクティビティログを取得するフック
 */
export const useActivityLogs = (page: number = 1, pageSize: number = 50, action?: string) => {
  return useQuery({
    queryKey: QUERY_KEYS.activityLogs(page, action),
    queryFn: () => userSettingsService.getActivityLogs(page, pageSize, action),
    keepPreviousData: true,
  })
}

/**
 * セッション一覧を取得するフック
 */
export const useSessions = () => {
  return useQuery({
    queryKey: QUERY_KEYS.sessions,
    queryFn: () => userSettingsService.getSessions(),
    refetchInterval: 30 * 1000, // 30秒ごとに更新
  })
}

/**
 * セッションを終了するミューテーション
 */
export const useTerminateSession = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) =>
      userSettingsService.terminateSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sessions })
      toast({
        title: 'セッションを終了しました',
        variant: 'default',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'セッションの終了に失敗しました',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      })
    },
  })
}