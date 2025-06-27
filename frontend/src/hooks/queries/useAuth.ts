import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { queryKeys } from '@/lib/react-query'
import { authService, type UserInfoResponse } from '@/services/auth.service'
import { useAppDispatch } from '@/store/hooks'
import { setUser, logout as logoutAction } from '@/store/slices/authSlice'
import { useToast } from '@/hooks/use-toast'

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
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: 'ログアウトに失敗しました。',
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
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: '認証URLの取得に失敗しました。',
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
      
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || '認証に失敗しました。',
        variant: 'destructive',
      })
      
      // ログインページへリダイレクト
      router.push('/auth/login')
    },
  })
}

/**
 * メール認証リクエストのミューテーションフック
 */
export const useRequestEmailVerification = () => {
  const { toast } = useToast()

  return useMutation({
    mutationFn: authService.requestEmailVerification,
    onSuccess: (data) => {
      toast({
        title: '確認メールを送信しました',
        description: data.message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'メールの送信に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * メール認証確認のミューテーションフック
 */
export const useConfirmEmailVerification = () => {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()
  const router = useRouter()
  const { toast } = useToast()

  return useMutation({
    mutationFn: authService.confirmEmailVerification,
    onSuccess: (data) => {
      // ユーザー情報を更新
      if (data.user) {
        queryClient.setQueryData(queryKeys.auth.me, data.user)
        dispatch(setUser(data.user))
      }
      
      toast({
        title: 'メールアドレスが確認されました',
        description: data.message,
      })
      
      // ダッシュボードへリダイレクト
      router.push('/dashboard/personal')
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'メールアドレスの確認に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * 検証メール再送信のミューテーションフック
 */
export const useResendVerificationEmail = () => {
  const { toast } = useToast()

  return useMutation({
    mutationFn: authService.resendVerificationEmail,
    onSuccess: (data) => {
      toast({
        title: '検証メールを再送信しました',
        description: data.message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'メールの送信に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * トークンリフレッシュのミューテーションフック
 * （通常は自動的に処理されるため、手動での使用は稀）
 */
export const useRefreshToken = () => {
  const queryClient = useQueryClient()
  const dispatch = useAppDispatch()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => authService.refreshToken(),
    onSuccess: (data) => {
      // ユーザー情報を更新
      queryClient.setQueryData(queryKeys.auth.me, data.user)
      dispatch(setUser(data.user))
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: 'トークンの更新に失敗しました。再度ログインしてください。',
        variant: 'destructive',
      })
    },
  })
}