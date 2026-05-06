/**
 * @fileoverview 認証カスタムフック (Redux selector + logout wrapper)
 *
 * UI コンポーネントが現在の認証状態 (Redux store) を簡便に読むためのフック。
 * `user`, `isAuthenticated`, `isInitialized`, `logout` を一括で返す。
 *
 * - Redux 由来の状態を読みたい時は本フック (`@/hooks/useAuth`) を使う
 * - API 操作 (login / logout / refresh など TanStack Query Mutation) を直接呼びたい時は
 *   {@link import('./queries/useAuth')} を使う
 *
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
