/**
 * @fileoverview 認証カスタムフック
 *
 * ReduxストアとReact Queryを組み合わせて認証状態を一元管理するカスタムフックです。
 * Phase 6 で Backlog OAuth ログイン (login()) を削除済み。
 * Phase 1 でローカルログイン (useLogin) を実装した後、本フックの login() を再導入する。
 */

import { useCallback } from 'react'
import { useAppSelector } from '../store/hooks'
import { useLogout } from './queries/useAuth'
import type { UserInfoResponse } from '@/services/auth.service'

interface UseAuthReturn {
  user: UserInfoResponse | null
  isAuthenticated: boolean
  isInitialized: boolean
  logout: () => void
}

export const useAuth = (): UseAuthReturn => {
  const { user, isAuthenticated, isInitialized } = useAppSelector((state) => state.auth)
  const logoutMutation = useLogout()

  const logout = useCallback(() => {
    logoutMutation.mutate()
  }, [logoutMutation])

  return {
    user,
    isAuthenticated,
    isInitialized,
    logout,
  }
}
