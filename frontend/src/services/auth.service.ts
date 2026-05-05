/**
 * 認証サービス (Phase 6 で Backlog OAuth 関連を削除済み)
 *
 * このモジュールは JWT ベースの認証 API クライアントを提供します。
 * ローカルログイン (login / accept-invitation / forgot-password / reset-password) は Phase 1 で追加します。
 */

import { apiClient } from '@/lib/api-client'

export interface Role {
  id: number
  name: string
  description: string
}

export interface UserRole {
  id: number
  role_id: number
  project_id: number | null
  role: Role
}

export interface UserInfoResponse {
  id: number
  email?: string
  name: string
  is_active: boolean
  user_roles: UserRole[]
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserInfoResponse
}

/**
 * 認証 API クライアント
 *
 * Phase 6 時点では JWT ベースの最小機能のみ提供:
 * - getCurrentUser: ログイン中のユーザー情報取得
 * - logout: ログアウト
 * - refreshJwtToken: アクセストークン更新
 *
 * Phase 1 でローカル認証メソッド (login, acceptInvitation 等) を追加予定
 */
export const authService = {
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout')
  },

  async getCurrentUser(): Promise<UserInfoResponse> {
    return await apiClient.get('/api/v1/auth/me')
  },

  async refreshJwtToken(): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/refresh')
  },
}
