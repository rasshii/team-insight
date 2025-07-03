/**
 * 認証サービス
 *
 * このモジュールは、Backlog OAuth2.0認証フローの
 * フロントエンド側の処理を提供します。
 */

import { apiClient } from '@/lib/api-client'

// 認証関連の型定義
export interface AuthorizationResponse {
  authorization_url: string
  state: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfoResponse
}

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
  backlog_id: number
  email?: string
  name: string
  user_id: string
  is_email_verified: boolean
  is_active: boolean
  backlog_space_key?: string
  user_roles: UserRole[]
}

export interface CallbackRequest {
  code: string
  state: string
}

/**
 * 認証関連のAPIサービス
 * 
 * Backlog OAuth2.0認証フローのためのシンプルな関数群
 * JWTトークンはHttpOnlyクッキーで管理されるため、
 * フロントエンドでのトークン管理は不要
 */
export const authService = {
  /**
   * 認証URLを取得
   * @param forceAccountSelection - アカウント選択を強制するかどうか
   */
  async getAuthorizationUrl(forceAccountSelection: boolean = false): Promise<AuthorizationResponse> {
    const params = forceAccountSelection ? { force_account_selection: true } : {}
    return await apiClient.get('/api/v1/auth/backlog/authorize', { params })
  },

  /**
   * 認証コールバック処理
   */
  async handleCallback(params: CallbackRequest): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/backlog/callback', params)
  },

  /**
   * ログアウト
   */
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout')
  },

  /**
   * 現在のユーザー情報を取得
   */
  async getCurrentUser(): Promise<UserInfoResponse> {
    return await apiClient.get('/api/v1/auth/me')
  },

  /**
   * Backlogトークンをリフレッシュ
   */
  async refreshBacklogToken(): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/backlog/refresh')
  },

  /**
   * JWTトークンをリフレッシュ
   */
  async refreshJwtToken(): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/refresh')
  },

  /**
   * OAuth stateの検証（セキュリティ用）
   * セッションストレージを使用してstateを一時的に保存
   */
  saveOAuthState(state: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('oauth_state', state)
    }
  },

  getOAuthState(): string | null {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem('oauth_state')
    }
    return null
  },

  clearOAuthState(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('oauth_state')
    }
  },
}