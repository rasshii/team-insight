/**
 * 認証サービス
 *
 * このモジュールは、Backlog OAuth2.0認証フローの
 * フロントエンド側の処理を提供します。
 */

import axios from "axios";

// APIのベースURL
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// 認証関連の型定義
export interface AuthorizationResponse {
  authorization_url: string;
  state: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserInfo {
  id: number;
  backlog_id: number;
  email?: string;
  name: string;
  user_id: string;
}

export interface CallbackRequest {
  code: string;
  state: string;
}

/**
 * 認証サービスクラス
 *
 * Backlog OAuth2.0認証フローを管理し、
 * トークンの保存・取得・削除を行います。
 */
class AuthService {
  private readonly TOKEN_KEY = "team_insight_token";
  private readonly USER_KEY = "team_insight_user";
  private readonly STATE_KEY = "team_insight_oauth_state";

  /**
   * 認証URLを取得します
   *
   * @returns 認証URLとstateを含むレスポンス
   */
  async getAuthorizationUrl(): Promise<AuthorizationResponse> {
    try {
      const response = await axios.get<AuthorizationResponse>(
        `${API_BASE_URL}/api/v1/auth/backlog/authorize`
      );

      // stateをローカルストレージに保存（CSRF対策）
      localStorage.setItem(this.STATE_KEY, response.data.state);

      return response.data;
    } catch (error) {
      console.error("認証URLの取得に失敗しました:", error);
      throw error;
    }
  }

  /**
   * 認証コールバックを処理します
   *
   * @param code - Backlogから受け取った認証コード
   * @param state - CSRF対策用のstate
   * @returns トークンとユーザー情報
   */
  async handleCallback(code: string, state: string): Promise<TokenResponse> {
    try {
      // 保存されたstateと比較（CSRF対策）
      const savedState = localStorage.getItem(this.STATE_KEY);
      if (savedState !== state) {
        throw new Error("無効なstateパラメータです");
      }

      // stateをクリア
      localStorage.removeItem(this.STATE_KEY);

      // コールバックAPIを呼び出し
      const response = await axios.post<TokenResponse>(
        `${API_BASE_URL}/api/v1/auth/backlog/callback`,
        { code, state } as CallbackRequest
      );

      // トークンとユーザー情報を保存
      this.saveToken(response.data.access_token);
      this.saveUser(response.data.user);

      // Axiosのデフォルトヘッダーに認証トークンを設定
      this.setAuthHeader(response.data.access_token);

      return response.data;
    } catch (error) {
      console.error("認証コールバックの処理に失敗しました:", error);
      throw error;
    }
  }

  /**
   * トークンをリフレッシュします
   *
   * @returns 新しいトークンとユーザー情報
   */
  async refreshToken(): Promise<TokenResponse> {
    try {
      const response = await axios.post<TokenResponse>(
        `${API_BASE_URL}/api/v1/auth/backlog/refresh`
      );

      // 新しいトークンを保存
      this.saveToken(response.data.access_token);
      this.setAuthHeader(response.data.access_token);

      return response.data;
    } catch (error) {
      console.error("トークンのリフレッシュに失敗しました:", error);
      // リフレッシュに失敗した場合はログアウト
      this.logout();
      throw error;
    }
  }

  /**
   * 現在のユーザー情報を取得します
   *
   * @returns ユーザー情報
   */
  async getCurrentUser(): Promise<UserInfo> {
    try {
      const response = await axios.get<UserInfo>(
        `${API_BASE_URL}/api/v1/auth/me`
      );
      return response.data;
    } catch (error) {
      console.error("ユーザー情報の取得に失敗しました:", error);
      throw error;
    }
  }

  /**
   * トークンを保存します
   *
   * @param token - アクセストークン
   */
  private saveToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * ユーザー情報を保存します
   *
   * @param user - ユーザー情報
   */
  private saveUser(user: UserInfo): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  /**
   * 保存されたトークンを取得します
   *
   * @returns アクセストークン（存在しない場合はnull）
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * 保存されたユーザー情報を取得します
   *
   * @returns ユーザー情報（存在しない場合はnull）
   */
  getUser(): UserInfo | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  /**
   * 認証済みかどうかを確認します
   *
   * @returns 認証済みの場合true
   */
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  /**
   * Axiosのデフォルトヘッダーに認証トークンを設定します
   *
   * @param token - アクセストークン
   */
  private setAuthHeader(token: string): void {
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  }

  /**
   * 認証ヘッダーをクリアします
   */
  private clearAuthHeader(): void {
    delete axios.defaults.headers.common["Authorization"];
  }

  /**
   * ログアウト処理を行います
   */
  logout(): void {
    // ローカルストレージをクリア
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.STATE_KEY);

    // 認証ヘッダーをクリア
    this.clearAuthHeader();
  }

  /**
   * 初期化処理
   * アプリケーション起動時に呼び出し、保存されたトークンがあれば設定します
   */
  initialize(): void {
    const token = this.getToken();
    if (token) {
      this.setAuthHeader(token);
    }
  }
}

// シングルトンインスタンスをエクスポート
export const authService = new AuthService();
