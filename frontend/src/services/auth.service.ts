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
  user_roles: UserRole[]
}

export interface CallbackRequest {
  code: string
  state: string
}

export interface EmailVerificationRequest {
  email: string
}

export interface EmailVerificationConfirmRequest {
  token: string
}

export interface EmailVerificationResponse {
  message: string
  email?: string
  user?: UserInfoResponse
}

/**
 * 認証関連のAPIサービス
 * 
 * React Queryと組み合わせて使用するためのシンプルな関数群
 * JWTトークンはHttpOnlyクッキーで管理されるため、
 * フロントエンドでのトークン管理は不要
 */
export const authService = {
  /**
   * 認証URLを取得
   */
  async getAuthorizationUrl(): Promise<AuthorizationResponse> {
    return await apiClient.get('/api/v1/auth/backlog/authorize')
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
    return await apiClient.post('/api/v1/auth/logout')
  },

  /**
   * 現在のユーザー情報を取得
   */
  async getCurrentUser(): Promise<UserInfoResponse> {
    return await apiClient.get('/api/v1/auth/me')
  },

  /**
   * トークンをリフレッシュ
   */
  async refreshToken(): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/backlog/refresh')
  },

  /**
   * メール認証リクエスト
   */
  async requestEmailVerification(data: EmailVerificationRequest): Promise<EmailVerificationResponse> {
    return await apiClient.post('/api/v1/auth/verify-email', data)
  },

  /**
   * メール認証確認
   */
  async confirmEmailVerification(data: EmailVerificationConfirmRequest): Promise<EmailVerificationResponse> {
    return await apiClient.post('/api/v1/auth/verify-email/confirm', data)
  },

  /**
   * 検証メールを再送信
   */
  async resendVerificationEmail(): Promise<EmailVerificationResponse> {
    return await apiClient.post('/api/v1/auth/email/verify/resend')
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