import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter, useSearchParams } from 'next/navigation'
import { queryKeys } from '@/lib/react-query'
import { authService, type UserInfoResponse } from '@/services/auth.service'
import { useAppDispatch } from '@/store/hooks'
import { setUser, logout as logoutAction } from '@/store/slices/authSlice'
import { useToast } from '@/hooks/use-toast'
import { getApiErrorMessage } from '@/lib/api-client'

/**
 * 現在のユーザー情報を取得するフック
 */
export const useCurrentUser = () => {
  const dispatch = useAppDispatch()

  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: async () => {
      const user = await authService.getCurrentUser()
      // Reduxストアも更新（互換性のため）
      dispatch(setUser(user))
      return user
    },
    staleTime: 10 * 60 * 1000, // 10分
    retry: false, // 認証エラーの場合はリトライしない
  })
}

/**
 * ログアウト処理のミューテーションフック
 */
export const useLogout = () => {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()
  const router = useRouter()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      // すべてのキャッシュをクリア
      queryClient.clear()
      
      // Reduxストアをクリア
      dispatch(logoutAction())
      
      toast({
        title: 'ログアウトしました',
      })
      
      // ページをリロードしてクッキーとキャッシュを完全にクリア
      // window.location.hrefを使うことで、React Routerを経由せずに完全なリロードを実行
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
 * 認証URLを取得するフック
 */
export const useGetAuthorizationUrl = () => {
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => authService.getAuthorizationUrl(),
    onSuccess: (data) => {
      // OAuth stateを保存
      authService.saveOAuthState(data.state)
      
      // Backlog認証ページへリダイレクト
      window.location.href = data.authorization_url
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
 * 認証コールバック処理のミューテーションフック
 */
export const useHandleAuthCallback = () => {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()
  const router = useRouter()
  const { toast } = useToast()

  return useMutation({
    mutationFn: authService.handleCallback,
    onSuccess: (data) => {
      // ユーザー情報をキャッシュ
      queryClient.setQueryData(queryKeys.auth.me, data.user)
      
      // Reduxストアを更新
      dispatch(setUser(data.user))
      
      // OAuth stateをクリア
      authService.clearOAuthState()
      
      // ダッシュボードへリダイレクト
      router.push('/dashboard/personal')
      
      toast({
        title: 'ログインしました',
        description: `ようこそ、${data.user.name}さん`,
      })
    },
    onError: (error: any) => {
      // OAuth stateをクリア
      authService.clearOAuthState()
      
      // エラーの詳細を解析
      const errorDetail = error.response?.data?.error?.detail || error.response?.data?.detail || ''
      const errorField = error.response?.data?.error?.field || ''
      let errorType = 'auth_failed'
      let errorMessage = getApiErrorMessage(error)
      
      // スペースアクセスエラーの判定
      if (errorField === 'space' || errorDetail.includes('スペース') || errorDetail.includes('space')) {
        errorType = 'space_not_allowed'
        errorMessage = 'このBacklogスペースへのアクセス権限がありません。nulab-examスペースのメンバーアカウントでログインしてください。'
      }
      // ドメイン制限エラーの判定
      else if (errorField === 'email' || errorDetail.includes('ドメイン') || errorDetail.includes('domain')) {
        errorType = 'domain_not_allowed'
        errorMessage = errorDetail || '組織外のメールアドレスではアクセスできません。'
      }
      
      toast({
        title: '認証エラー',
        description: errorMessage,
        variant: 'destructive',
      })
      
      // エラータイプを含めてログインページへリダイレクト
      router.push(`/auth/login?error=${errorType}`)
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
      // ユーザー情報を更新
      queryClient.setQueryData(queryKeys.auth.me, data.user)
      dispatch(setUser(data.user))
    },
  })
}