/**
 * 認証サービス
 *
 * このモジュールは、Backlog OAuth2.0認証フローの
 * フロントエンド側の処理を提供します。
 */

import axios from "axios";

// APIのベースURL
// 開発環境ではNginxを経由するため、ポート番号なしでアクセス
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost";

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
   * localStorageが使用可能かチェック
   */
  private isLocalStorageAvailable(): boolean {
    return (
      typeof window !== "undefined" &&
      typeof window.localStorage !== "undefined"
    );
  }

  /**
   * 認証URLを取得します
   *
   * @returns 認証URLとstateを含むレスポンス
   */
  async getAuthorizationUrl(): Promise<AuthorizationResponse> {
    try {
      console.log("認証URL取得開始");
      const response = await axios.get<AuthorizationResponse>(
        `${API_BASE_URL}/api/v1/auth/backlog/authorize`
      );
      console.log("認証URL取得レスポンス:", response.data);

      // stateをローカルストレージに保存（CSRF対策）
      if (this.isLocalStorageAvailable()) {
        console.log("localStorage利用可能 - state保存開始");
        localStorage.setItem(this.STATE_KEY, response.data.state);
        console.log("保存したstate:", response.data.state);
        // 保存されたことを確認
        const savedState = localStorage.getItem(this.STATE_KEY);
        console.log("保存確認 - state:", savedState);
      } else {
        console.warn("localStorageが利用できません");
      }

      console.log("認証URL取得成功:", response.data.authorization_url);
      return response.data;
    } catch (error: any) {
      console.error("認証URLの取得に失敗しました:", error);
      console.error("エラー詳細:", error.response?.data);
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
      console.log("認証コールバック処理開始");
      console.log("受信したcode:", code);
      console.log("受信したstate:", state);

      // 保存されたstateと比較（CSRF対策）
      let savedState: string | null = null;
      if (this.isLocalStorageAvailable()) {
        console.log("localStorage利用可能 - state取得開始");
        savedState = localStorage.getItem(this.STATE_KEY);
        console.log("保存されたstate:", savedState);
      } else {
        console.warn("localStorageが利用できません");
      }

      // stateが既にクリアされている場合は、処理をスキップ
      if (!savedState && !state) {
        console.error("認証状態が見つかりません");
        throw new Error("認証状態が見つかりません");
      }

      // savedStateがnullでない場合のみ検証
      if (savedState && savedState !== state) {
        console.error("State不一致 - 保存:", savedState, "受信:", state);
        throw new Error("無効なstateパラメータです");
      }

      // stateをクリア（既にクリアされていても問題ない）
      if (this.isLocalStorageAvailable() && savedState) {
        console.log("stateをクリア");
        localStorage.removeItem(this.STATE_KEY);
      }

      // コールバックAPIを呼び出し
      console.log("コールバックAPI呼び出し開始");
      const response = await axios.post<TokenResponse>(
        `${API_BASE_URL}/api/v1/auth/backlog/callback`,
        { code, state } as CallbackRequest
      );
      console.log("コールバックAPI呼び出し成功");

      // トークンとユーザー情報を保存
      console.log("トークンとユーザー情報を保存開始");
      if (response.data.access_token) {
        this.saveToken(response.data.access_token);
        // クッキーにも保存（セキュリティ要件に応じてSecure/HttpOnly/Path/Expiresを調整）
        document.cookie = `auth_token=${response.data.access_token}; path=/; max-age=604800; SameSite=Lax`;
      } else {
        console.error("トークンが含まれていません");
      }

      if (response.data.user) {
        this.saveUser(response.data.user);
      } else {
        console.error("ユーザー情報が含まれていません");
      }
      console.log("トークンとユーザー情報の保存完了");

      // Axiosのデフォルトヘッダーに認証トークンを設定
      console.log("認証ヘッダーを設定");
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
    console.log("トークン保存開始");
    if (this.isLocalStorageAvailable()) {
      localStorage.setItem(this.TOKEN_KEY, token);
      console.log("トークン保存完了");
      // 保存確認
      const savedToken = localStorage.getItem(this.TOKEN_KEY);
      console.log("保存されたトークン:", savedToken ? "あり" : "なし");
    } else {
      console.warn("localStorageが利用できないため、トークンを保存できません");
    }
  }

  /**
   * ユーザー情報を保存します
   *
   * @param user - ユーザー情報
   */
  private saveUser(user: UserInfo): void {
    console.log("ユーザー情報保存開始");
    if (this.isLocalStorageAvailable()) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      console.log("ユーザー情報保存完了");
      // 保存確認
      const savedUser = localStorage.getItem(this.USER_KEY);
      console.log("保存されたユーザー情報:", savedUser ? "あり" : "なし");
    } else {
      console.warn(
        "localStorageが利用できないため、ユーザー情報を保存できません"
      );
    }
  }

  /**
   * 保存されたトークンを取得します
   *
   * @returns アクセストークン（存在しない場合はnull）
   */
  getToken(): string | null {
    console.log("トークン取得開始");
    if (this.isLocalStorageAvailable()) {
      const token = localStorage.getItem(this.TOKEN_KEY);
      console.log("取得したトークン:", token ? "あり" : "なし");
      return token;
    }
    console.warn("localStorageが利用できないため、トークンを取得できません");
    return null;
  }

  /**
   * 保存されたユーザー情報を取得します
   *
   * @returns ユーザー情報（存在しない場合はnull）
   */
  getUser(): UserInfo | null {
    console.log("ユーザー情報取得開始");
    if (!this.isLocalStorageAvailable()) {
      console.warn(
        "localStorageが利用できないため、ユーザー情報を取得できません"
      );
      return null;
    }

    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) {
      console.log("保存されたユーザー情報なし");
      return null;
    }

    try {
      const user = JSON.parse(userStr);
      console.log("取得したユーザー情報:", user);
      return user;
    } catch (error) {
      console.error("ユーザー情報のパースに失敗:", error);
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
    if (this.isLocalStorageAvailable()) {
      localStorage.removeItem(this.TOKEN_KEY);
      localStorage.removeItem(this.USER_KEY);
      localStorage.removeItem(this.STATE_KEY);
    }

    // 認証ヘッダーをクリア
    this.clearAuthHeader();
  }

  /**
   * 認証サービスを初期化します
   */
  async initialize(): Promise<void> {
    console.log("認証サービス初期化開始");
    if (!this.isLocalStorageAvailable()) {
      console.warn("localStorageが利用できないため、初期化をスキップします");
      return;
    }

    try {
      const token = this.getToken();
      const user = this.getUser();
      console.log("初期化時のトークン状態:", token ? "あり" : "なし");
      console.log("初期化時のユーザー情報:", user ? "あり" : "なし");

      if (token && user) {
        console.log("保存されたトークンを使用して認証ヘッダーを設定");
        this.setAuthHeader(token);
      } else {
        console.log("保存されたトークンまたはユーザー情報なし");
        this.clearAuthHeader();
        // ローカルストレージをクリア
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
      }
    } catch (error) {
      console.error("認証サービスの初期化中にエラーが発生:", error);
      this.clearAuthHeader();
      // エラー時はローカルストレージをクリア
      localStorage.removeItem(this.TOKEN_KEY);
      localStorage.removeItem(this.USER_KEY);
    }
  }
}

// シングルトンインスタンスをエクスポート
export const authService = new AuthService();
