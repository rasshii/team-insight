/**
 * 認証コンテキスト
 *
 * アプリケーション全体で認証状態を管理するための
 * Reactコンテキストを提供します。
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, UserInfo } from '../services/auth.service';

/**
 * 認証コンテキストの型定義
 */
interface AuthContextType {
  /** 現在のユーザー情報 */
  user: UserInfo | null;
  /** ローディング状態 */
  loading: boolean;
  /** 認証済みかどうか */
  isAuthenticated: boolean;
  /** ログイン処理を開始 */
  login: () => Promise<void>;
  /** ログアウト処理 */
  logout: () => void;
  /** トークンをリフレッシュ */
  refreshToken: () => Promise<void>;
}

// 認証コンテキストの作成
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * 認証プロバイダーのプロパティ
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * 認証プロバイダーコンポーネント
 *
 * アプリケーション全体で認証状態を提供します。
 * 初期化時に保存されたトークンの確認と、
 * 認証状態の管理を行います。
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  /**
   * 初期化処理
   * 保存されたトークンがある場合は、ユーザー情報を取得
   */
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // 認証サービスを初期化
        authService.initialize();

        // 保存されたユーザー情報を取得
        const savedUser = authService.getUser();

        if (authService.isAuthenticated() && savedUser) {
          // トークンが存在する場合は、最新のユーザー情報を取得
          try {
            const currentUser = await authService.getCurrentUser();
            setUser(currentUser);
          } catch (error) {
            // ユーザー情報の取得に失敗した場合は、保存された情報を使用
            setUser(savedUser);
          }
        }
      } catch (error) {
        console.error('認証の初期化に失敗しました:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  /**
   * ログイン処理を開始
   * Backlogの認証ページにリダイレクトします
   */
  const login = async () => {
    try {
      const { authorization_url } = await authService.getAuthorizationUrl();
      // Backlogの認証ページにリダイレクト
      window.location.href = authorization_url;
    } catch (error) {
      console.error('ログイン処理の開始に失敗しました:', error);
      throw error;
    }
  };

  /**
   * ログアウト処理
   */
  const logout = () => {
    authService.logout();
    setUser(null);
    // ホームページにリダイレクト
    window.location.href = '/';
  };

  /**
   * トークンをリフレッシュ
   */
  const refreshToken = async () => {
    try {
      const response = await authService.refreshToken();
      setUser(response.user);
    } catch (error) {
      console.error('トークンのリフレッシュに失敗しました:', error);
      // リフレッシュに失敗した場合はログアウト
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * 認証コンテキストを使用するカスタムフック
 *
 * @returns 認証コンテキスト
 * @throws コンテキストがプロバイダー外で使用された場合
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
