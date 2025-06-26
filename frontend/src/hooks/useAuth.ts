/**
 * 認証カスタムフック
 *
 * ReduxストアとReact Queryを組み合わせて
 * 認証状態を管理します。
 */

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAppSelector } from "../store/hooks";
import { useCurrentUser as useCurrentUserQuery, useLogout, useGetAuthorizationUrl } from "./queries/useAuth";

/**
 * 認証フックの戻り値の型定義
 */
interface UseAuthReturn {
  /** 現在のユーザー情報 */
  user: any;
  /** 認証済みかどうか */
  isAuthenticated: boolean;
  /** 初期化完了フラグ */
  isInitialized: boolean;
  /** ログイン処理を開始 */
  login: () => void;
  /** ログアウト処理 */
  logout: () => void;
}

/**
 * 認証カスタムフック
 *
 * @returns 認証状態とアクション
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