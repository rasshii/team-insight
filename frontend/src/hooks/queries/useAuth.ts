/**
 * @fileoverview 認証関連のReact Queryフック
 *
 * 認証APIエンドポイントへのアクセスをReact Queryで管理するカスタムフック集です。
 * ユーザー情報の取得、ログアウト、認証URL取得、トークンリフレッシュなどの機能を提供します。
 *
 * @module useAuthQueries
 */

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
 *
 * ログイン中のユーザーの詳細情報を取得し、React Queryでキャッシュします。
 * 取得したユーザー情報はReduxストアにも自動的に保存されます。
 *
 * @returns {UseQueryResult<UserInfoResponse>} React Queryの結果オブジェクト
 *
 * @example
 * ```tsx
 * function UserProfile() {
 *   const { data: user, isLoading, error } = useCurrentUser();
 *
 *   if (isLoading) return <Spinner />;
 *   if (error) return <ErrorMessage />;
 *
 *   return <div>ようこそ、{user.name}さん</div>;
 * }
 * ```
 *
 * @remarks
 * - staleTime: 10分（データの鮮度保証期間）
 * - retry: false（認証エラーの場合はリトライしない）
 * - 未認証の場合は401エラーが返されます
 * - 取得したユーザー情報は自動的にReduxストアにも保存されます
 *
 * @see {@link authService.getCurrentUser} - ユーザー情報取得API
 * @see {@link queryKeys.auth.me} - React Queryのクエリキー
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
 *
 * ユーザーをログアウトし、全てのキャッシュとReduxストアをクリアします。
 * ログアウト完了後、ルートページに強制リダイレクトします。
 *
 * @returns {UseMutationResult<void>} React Queryのミューテーション結果オブジェクト
 *
 * @example
 * ```tsx
 * function LogoutButton() {
 *   const logoutMutation = useLogout();
 *
 *   return (
 *     <button
 *       onClick={() => logoutMutation.mutate()}
 *       disabled={logoutMutation.isPending}
 *     >
 *       {logoutMutation.isPending ? 'ログアウト中...' : 'ログアウト'}
 *     </button>
 *   );
 * }
 * ```
 *
 * @remarks
 * - 成功時の処理:
 *   1. React Queryの全キャッシュをクリア
 *   2. Reduxストアをクリア（dispatch(logoutAction())）
 *   3. トーストメッセージを表示
 *   4. window.location.href = '/' でルートページへリダイレクト
 * - window.location.hrefを使用することで、完全なページリロードを実行
 *
 * @see {@link authService.logout} - ログアウトAPI
 * @see {@link useAuth} - 認証状態管理フック
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