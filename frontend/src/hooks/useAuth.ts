/**
 * @fileoverview 認証カスタムフック
 *
 * ReduxストアとReact Queryを組み合わせて認証状態を一元管理するカスタムフックです。
 * ログイン、ログアウト、ユーザー情報の取得などの認証関連機能を提供します。
 *
 * @module useAuth
 */

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAppSelector } from "../store/hooks";
import { useCurrentUser as useCurrentUserQuery, useLogout, useGetAuthorizationUrl } from "./queries/useAuth";

/**
 * 認証フックの戻り値の型定義
 *
 * useAuth フックが返すオブジェクトの型を定義します。
 */
interface UseAuthReturn {
  /** 現在のユーザー情報（未認証の場合はnull） */
  user: any;
  /** 認証済みかどうか */
  isAuthenticated: boolean;
  /** 初期化完了フラグ（初回のユーザー情報取得が完了したか） */
  isInitialized: boolean;
  /** ログイン処理を開始（Backlog認証ページへリダイレクト） */
  login: () => void;
  /** ログアウト処理 */
  logout: () => void;
}

/**
 * 認証状態と認証関連の操作を提供するカスタムフック
 *
 * ## 提供する機能
 * - 現在のユーザー情報の取得
 * - ログイン状態の判定
 * - ログイン処理の開始（Backlog OAuth2.0認証）
 * - ログアウト処理
 *
 * ## 状態管理
 * - Redux（グローバル状態）とReact Query（サーバー状態）を組み合わせて使用
 * - ユーザー情報はReduxストアとReact Queryの両方で管理（互換性のため）
 * - 認証状態（isAuthenticated）はReduxで管理
 *
 * ## 認証フロー
 * 1. login() - Backlog認証URLを取得してリダイレクト
 * 2. ユーザーがBacklogでログイン
 * 3. コールバックURLに戻る（useHandleAuthCallbackで処理）
 * 4. ユーザー情報を取得してReduxとReact Queryに保存
 *
 * @returns {UseAuthReturn} 認証関連の状態とメソッド
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { user, isAuthenticated, login, logout } = useAuth();
 *
 *   if (!isAuthenticated) {
 *     return <button onClick={login}>ログイン</button>;
 *   }
 *
 *   return (
 *     <div>
 *       <p>ようこそ、{user?.name}さん</p>
 *       <button onClick={logout}>ログアウト</button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @remarks
 * - このフックはアプリケーション全体で使用される中核的なフックです
 * - PrivateRouteコンポーネントなど、認証ガードで広く使用されます
 * - ログアウト時はReduxストアとReact Queryキャッシュの両方がクリアされます
 *
 * @see {@link useCurrentUserQuery} - ユーザー情報取得のReact Queryフック
 * @see {@link useLogout} - ログアウトミューテーションフック
 * @see {@link useGetAuthorizationUrl} - 認証URL取得ミューテーションフック
 */
export const useAuth = (): UseAuthReturn => {
  const router = useRouter();
  const { user, isAuthenticated, isInitialized } = useAppSelector((state) => state.auth);
  
  // React Queryのミューテーション
  const logoutMutation = useLogout();
  const getAuthUrlMutation = useGetAuthorizationUrl();

  /**
   * ログイン処理を開始
   * Backlogの認証ページにリダイレクトします
   */
  const login = useCallback(() => {
    getAuthUrlMutation.mutate();
  }, [getAuthUrlMutation]);

  /**
   * ログアウト処理
   */
  const logout = useCallback(() => {
    logoutMutation.mutate();
  }, [logoutMutation]);

  return {
    user,
    isAuthenticated,
    isInitialized,
    login,
    logout,
  };
};