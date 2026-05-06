/**
 * @fileoverview 認証関連のReact Queryフック
 *
 * Phase 6 で Backlog OAuth 関連 hook (useGetAuthorizationUrl, useHandleAuthCallback) を削除。
 * Phase 1 でローカル認証 hook (useLogin, useAcceptInvitation 等) を追加予定。
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/hooks/use-toast'
import { getApiErrorMessage } from '@/lib/api-client'
import { queryKeys } from '@/lib/react-query'
import { authService } from '@/services/auth.service'
import { useAppDispatch } from '@/store/hooks'
import { logout as logoutAction, setUser } from '@/store/slices/authSlice'

/**
 * 現在のユーザー情報を取得するフック
 */
export const useCurrentUser = () => {
  const dispatch = useAppDispatch()

  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: async () => {
      const user = await authService.getCurrentUser()
      dispatch(setUser(user))
      return user
    },
    staleTime: 5 * 60 * 1000, // 5 分 (アクセストークン 15 分以内に refetch)
    retry: false,
  })
}

/**
 * ログアウト処理のミューテーションフック
 */
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

/**
 * トークンリフレッシュのミューテーションフック
 */
export const useRefreshToken = () => {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()

  return useMutation({
    mutationFn: authService.refreshJwtToken,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.auth.me, data.user)
      dispatch(setUser(data.user))
    },
  })
}
