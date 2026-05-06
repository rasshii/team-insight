/**
 * 認証スライス (Phase 0: activeOrganizationId 対応)
 *
 * グローバルな認証状態 + アクティブ組織を管理する。データフェッチは React Query 側で行う。
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { UserInfoResponse } from '@/services/auth.service'

interface AuthState {
  user: UserInfoResponse | null
  isAuthenticated: boolean
  isInitialized: boolean
  /** 現在アクティブにしている組織 ID (組織切替時に変更) */
  activeOrganizationId: number | null
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  activeOrganizationId: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<UserInfoResponse>) => {
      state.user = action.payload
      state.isAuthenticated = true
      state.isInitialized = true

      // 既存の active 組織が新しい organizations に含まれない場合は最初の組織に切替
      const orgIds = action.payload.organizations.map((m) => m.organization_id)
      if (
        state.activeOrganizationId === null ||
        !orgIds.includes(state.activeOrganizationId)
      ) {
        state.activeOrganizationId = orgIds[0] ?? null
      }
    },

    setActiveOrganization: (
      state,
      action: PayloadAction<number | null>
    ) => {
      state.activeOrganizationId = action.payload
    },

    initializeAuth: (state) => {
      state.isInitialized = true
    },

    logout: (state) => {
      state.user = null
      state.isAuthenticated = false
      state.activeOrganizationId = null
    },
  },
})

export const { setUser, setActiveOrganization, initializeAuth, logout } =
  authSlice.actions

export const selectCurrentUser = (state: { auth: AuthState }) => state.auth.user
export const selectIsAuthenticated = (state: { auth: AuthState }) =>
  state.auth.isAuthenticated
export const selectIsInitialized = (state: { auth: AuthState }) =>
  state.auth.isInitialized
export const selectActiveOrganizationId = (state: { auth: AuthState }) =>
  state.auth.activeOrganizationId
export const selectActiveOrganization = (state: { auth: AuthState }) => {
  const id = state.auth.activeOrganizationId
  if (id === null || !state.auth.user) return null
  return (
    state.auth.user.organizations.find((m) => m.organization_id === id) ?? null
  )
}

export default authSlice.reducer
