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
 * Backlog OAuth2.0認証フローの全機能を提供します。
 * JWTトークンはHttpOnlyクッキーで管理されるため、フロントエンドでの
 * トークン管理や保存処理は不要です。
 *
 * ## 認証フロー
 * 1. getAuthorizationUrl() - Backlog認証ページのURLを取得
 * 2. ユーザーがBacklogでログイン・認証
 * 3. handleCallback() - 認証コードを受け取りトークンを取得
 * 4. getCurrentUser() - ログイン中のユーザー情報を取得
 *
 * ## セキュリティ
 * - OAuth stateパラメータによるCSRF攻撃対策
 * - JWTトークンはHttpOnlyクッキーで保存（XSS攻撃対策）
 * - トークンリフレッシュ機能（自動的にセッションを延長）
 *
 * @see {@link apiClient} - 全APIリクエストで使用する共通クライアント
 */
export const authService = {
  /**
   * Backlog認証URLを取得
   *
   * Backlog OAuth2.0認証フローの開始点です。
   * 取得したURLにユーザーをリダイレクトすることで、Backlogログイン画面に遷移します。
   *
   * @param {boolean} [forceAccountSelection=false] - アカウント選択を強制するかどうか
   * @returns {Promise<AuthorizationResponse>} 認証URLとstateパラメータを含むレスポンス
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * const { authorization_url, state } = await authService.getAuthorizationUrl();
   * authService.saveOAuthState(state); // stateを保存してCSRF対策
   * window.location.href = authorization_url; // Backlogログイン画面へリダイレクト
   * ```
   *
   * @see {@link saveOAuthState} - OAuth stateを保存してセキュリティを確保
   */
  async getAuthorizationUrl(forceAccountSelection: boolean = false): Promise<AuthorizationResponse> {
    const params = forceAccountSelection ? { force_account_selection: true } : {}
    return await apiClient.get('/api/v1/auth/backlog/authorize', { params })
  },

  /**
   * 認証コールバック処理
   *
   * Backlogから返された認証コードを使用してアクセストークンを取得します。
   * 取得したトークンはHttpOnlyクッキーに保存され、以降のAPIリクエストで自動的に使用されます。
   *
   * @param {CallbackRequest} params - 認証コードとstateパラメータ
   * @param {string} params.code - Backlogから返された認証コード
   * @param {string} params.state - CSRF対策用のstateパラメータ
   * @returns {Promise<TokenResponse>} アクセストークンとユーザー情報
   * @throws {AxiosError} APIリクエストが失敗した場合、またはstateが一致しない場合
   *
   * @example
   * ```typescript
   * // URLパラメータから認証コードとstateを取得
   * const code = searchParams.get('code');
   * const state = searchParams.get('state');
   *
   * // 保存したstateと比較（CSRF対策）
   * const savedState = authService.getOAuthState();
   * if (state !== savedState) {
   *   throw new Error('Invalid state parameter');
   * }
   *
   * // トークンを取得
   * const { user } = await authService.handleCallback({ code, state });
   * console.log('ログイン成功:', user.name);
   * ```
   *
   * @see {@link getOAuthState} - 保存したstateパラメータを取得
   * @see {@link clearOAuthState} - 認証完了後にstateをクリア
   */
  async handleCallback(params: CallbackRequest): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/backlog/callback', params)
  },

  /**
   * ログアウト
   *
   * サーバー側のセッションを無効化し、HttpOnlyクッキーをクリアします。
   * ログアウト後は認証が必要なAPIエンドポイントにアクセスできなくなります。
   *
   * @returns {Promise<void>}
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * await authService.logout();
   * // Reduxストアやキャッシュのクリアを実行
   * window.location.href = '/'; // ログインページへリダイレクト
   * ```
   *
   * @remarks
   * この関数は単にサーバー側のセッションを無効化するだけです。
   * フロントエンド側のReduxストアやReact Queryキャッシュのクリアは
   * 呼び出し側で実装する必要があります。
   */
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout')
  },

  /**
   * 現在のユーザー情報を取得
   *
   * ログイン中のユーザーの詳細情報を取得します。
   * JWTトークン（HttpOnlyクッキー）による認証が必要です。
   *
   * @returns {Promise<UserInfoResponse>} ユーザー情報オブジェクト
   * @throws {AxiosError} APIリクエストが失敗した場合、または未認証の場合（401エラー）
   *
   * @example
   * ```typescript
   * try {
   *   const user = await authService.getCurrentUser();
   *   console.log(`ようこそ、${user.name}さん`);
   *   console.log('ロール:', user.user_roles.map(r => r.role.name));
   * } catch (error) {
   *   if (error.response?.status === 401) {
   *     console.log('未認証です。ログインしてください。');
   *   }
   * }
   * ```
   *
   * @remarks
   * このエンドポイントは認証済みユーザーのみアクセス可能です。
   * 未認証の場合は401エラーが返されます。
   *
   * @see {@link UserInfoResponse} - レスポンスの型定義
   */
  async getCurrentUser(): Promise<UserInfoResponse> {
    return await apiClient.get('/api/v1/auth/me')
  },

  /**
   * Backlogトークンをリフレッシュ
   *
   * Backlog APIアクセストークンの有効期限が切れた場合、
   * リフレッシュトークンを使用して新しいアクセストークンを取得します。
   *
   * @returns {Promise<TokenResponse>} 新しいアクセストークンとユーザー情報
   * @throws {AxiosError} リフレッシュに失敗した場合（トークン期限切れなど）
   *
   * @example
   * ```typescript
   * try {
   *   const { user } = await authService.refreshBacklogToken();
   *   console.log('Backlogトークンをリフレッシュしました');
   * } catch (error) {
   *   console.error('リフレッシュ失敗。再ログインが必要です。');
   * }
   * ```
   *
   * @remarks
   * この関数は通常、Backlog APIからのエラーレスポンスを受け取った際に
   * 自動的に呼び出されます。手動で呼び出す必要はほとんどありません。
   */
  async refreshBacklogToken(): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/backlog/refresh')
  },

  /**
   * JWTトークンをリフレッシュ
   *
   * Team InsightのJWTトークンの有効期限が切れた場合、
   * リフレッシュトークンを使用して新しいJWTトークンを取得します。
   *
   * @returns {Promise<TokenResponse>} 新しいJWTトークンとユーザー情報
   * @throws {AxiosError} リフレッシュに失敗した場合（トークン期限切れなど）
   *
   * @example
   * ```typescript
   * try {
   *   const { user } = await authService.refreshJwtToken();
   *   console.log('JWTトークンをリフレッシュしました');
   * } catch (error) {
   *   console.error('リフレッシュ失敗。再ログインが必要です。');
   * }
   * ```
   *
   * @remarks
   * この関数は通常、APIクライアントのインターセプターで
   * 401エラーを受け取った際に自動的に呼び出されます。
   * 手動で呼び出す必要はほとんどありません。
   *
   * @see {@link apiClient} - 自動リフレッシュ機能を持つAPIクライアント
   */
  async refreshJwtToken(): Promise<TokenResponse> {
    return await apiClient.post('/api/v1/auth/refresh')
  },

  /**
   * OAuth stateパラメータを保存
   *
   * CSRF攻撃対策のため、認証フロー開始時に発行されたstateパラメータを
   * セッションストレージに保存します。コールバック時にこの値を検証することで、
   * 正規の認証フローであることを確認します。
   *
   * @param {string} state - 保存するstateパラメータ
   *
   * @example
   * ```typescript
   * const { authorization_url, state } = await authService.getAuthorizationUrl();
   * authService.saveOAuthState(state); // stateを保存
   * window.location.href = authorization_url;
   * ```
   *
   * @remarks
   * セッションストレージを使用するため、ブラウザタブを閉じると自動的にクリアされます。
   * サーバーサイドレンダリング（SSR）環境では動作しません（window オブジェクトが必要）。
   *
   * @see {@link getOAuthState} - 保存したstateを取得
   * @see {@link clearOAuthState} - stateをクリア
   */
  saveOAuthState(state: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('oauth_state', state)
    }
  },

  /**
   * 保存されたOAuth stateパラメータを取得
   *
   * 認証コールバック時に、保存されたstateパラメータを取得して検証します。
   *
   * @returns {string | null} 保存されたstateパラメータ、または存在しない場合はnull
   *
   * @example
   * ```typescript
   * // 認証コールバック時
   * const savedState = authService.getOAuthState();
   * const receivedState = searchParams.get('state');
   *
   * if (savedState !== receivedState) {
   *   throw new Error('State mismatch - possible CSRF attack');
   * }
   * ```
   *
   * @see {@link saveOAuthState} - stateを保存
   */
  getOAuthState(): string | null {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem('oauth_state')
    }
    return null
  },

  /**
   * 保存されたOAuth stateパラメータをクリア
   *
   * 認証フローが完了した後、セッションストレージから
   * stateパラメータを削除します。
   *
   * @example
   * ```typescript
   * // 認証成功後
   * await authService.handleCallback({ code, state });
   * authService.clearOAuthState(); // stateをクリア
   * router.push('/dashboard');
   * ```
   *
   * @remarks
   * 認証が成功した場合も失敗した場合も、必ずstateをクリアしてください。
   * stateの再利用はセキュリティリスクになります。
   *
   * @see {@link saveOAuthState} - stateを保存
   */
  clearOAuthState(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('oauth_state')
    }
  },
}