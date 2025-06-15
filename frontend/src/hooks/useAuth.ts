/**
 * 認証カスタムフック
 *
 * Reduxストアから認証状態を取得し、
 * 認証関連のアクションを提供します。
 */

import { useCallback } from "react";
import type { RootState } from "../store";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import {
  clearError,
  getAuthorizationUrl,
  handleAuthCallback,
  logout as logoutAction,
  refreshAuthToken,
} from "../store/slices/authSlice";

/**
 * 認証フックの戻り値の型定義
 */
interface UseAuthReturn {
  /** 現在のユーザー情報 */
  user: RootState["auth"]["user"];
  /** ローディング状態 */
  loading: boolean;
  /** エラー情報 */
  error: string | null;
  /** 認証済みかどうか */
  isAuthenticated: boolean;
  /** 初期化完了フラグ */
  isInitialized: boolean;
  /** ログイン処理を開始 */
  login: () => Promise<void>;
  /** ログアウト処理 */
  logout: () => void;
  /** 認証コールバックを処理 */
  handleCallback: (code: string, state: string) => Promise<void>;
  /** トークンをリフレッシュ */
  refreshToken: () => Promise<void>;
  /** エラーをクリア */
  clearAuthError: () => void;
}

/**
 * 認証カスタムフック
 *
 * @returns 認証状態とアクション
 */
export const useAuth = (): UseAuthReturn => {
  const dispatch = useAppDispatch();
  const { user, loading, error, isAuthenticated, isInitialized } =
    useAppSelector((state) => state.auth);

  /**
   * ログイン処理を開始
   * Backlogの認証ページにリダイレクトします
   */
  const login = useCallback(async () => {
    try {
      console.log("ログイン処理開始");
      const result = await dispatch(getAuthorizationUrl()).unwrap();
      console.log("認証URL取得成功:", result);
      console.log("認証URLへリダイレクト:", result.authorization_url);
      // Backlogの認証ページにリダイレクト
      window.location.href = result.authorization_url;
    } catch (error) {
      console.error("ログイン処理の開始に失敗しました:", error);
      throw error;
    }
  }, [dispatch]);

  /**
   * ログアウト処理
   */
  const logout = useCallback(() => {
    console.log("ログアウト処理開始");
    dispatch(logoutAction());
    console.log("ホームページへリダイレクト");
    // ホームページにリダイレクト
    window.location.href = "/";
  }, [dispatch]);

  /**
   * 認証コールバックを処理
   */
  const handleCallback = useCallback(
    async (code: string, state: string) => {
      try {
        console.log("認証コールバック処理開始 - useAuth");
        console.log("code:", code);
        console.log("state:", state);
        await dispatch(handleAuthCallback({ code, state })).unwrap();
        console.log("認証コールバック処理成功 - useAuth");
      } catch (error) {
        console.error("認証コールバックの処理に失敗しました - useAuth:", error);
        throw error;
      }
    },
    [dispatch]
  );

  /**
   * トークンをリフレッシュ
   */
  const refreshToken = useCallback(async () => {
    try {
      await dispatch(refreshAuthToken()).unwrap();
    } catch (error) {
      console.error("トークンのリフレッシュに失敗しました:", error);
      throw error;
    }
  }, [dispatch]);

  /**
   * エラーをクリア
   */
  const clearAuthError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  return {
    user,
    loading,
    error,
    isAuthenticated,
    isInitialized,
    login,
    logout,
    handleCallback,
    refreshToken,
    clearAuthError,
  };
};
