/**
 * 認証関連の React Query フック (Phase 0: 組織切替対応)
 *
 * Phase 6 で Backlog OAuth 関連 hook を削除済み。
 * Phase 0 で setUser に組織情報が含まれるよう変更。
 * Phase 1 でローカル認証 hook (useLogin, useAcceptInvitation 等) を追加予定。
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useToast } from '@/hooks/use-toast'
import { getApiErrorMessage } from '@/lib/api-client'
import { queryKeys } from '@/lib/react-query'
import { authService } from '@/services/auth.service'
import { useAppDispatch } from '@/store/hooks'
import {
  logout as logoutAction,
  setActiveOrganization,
  setUser,
} from '@/store/slices/authSlice'

export const useCurrentUser = () => {
  const dispatch = useAppDispatch()

  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: async () => {
      const user = await authService.getCurrentUser()
      dispatch(setUser(user))
      return user
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export const useLogout = () => {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      queryClient.clear()
      dispatch(logoutAction())
      toast({ title: 'ログアウトしました' })
      window.location.href = '/'
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}

export const useRefreshToken = () => {
  const dispatch = useAppDispatch()

  return useMutation({
    mutationFn: authService.refreshJwtToken,
    onSuccess: (data) => {
      // refresh レスポンスに user は含まれないため、active_org_id のみ更新
      if (data.active_org_id != null) {
        dispatch(setActiveOrganization(data.active_org_id))
      }
    },
  })
}

export const useSwitchOrganization = () => {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (organizationId: number) =>
      authService.switchOrganization(organizationId),
    onSuccess: (data) => {
      if (data.active_org_id != null) {
        dispatch(setActiveOrganization(data.active_org_id))
      }
      // テナント依存データを無効化
      queryClient.invalidateQueries()
      toast({ title: '組織を切り替えました' })
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}
