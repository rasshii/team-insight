/**
 * プライベートルートコンポーネント
 *
 * 認証が必要なルートを保護し、
 * 未認証ユーザーをログインページにリダイレクトします。
 */

import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

/**
 * プライベートルートのプロパティ
 */
interface PrivateRouteProps {
  children: React.ReactNode;
}

/**
 * プライベートルートコンポーネント
 *
 * 認証状態を確認し、未認証の場合はログインページにリダイレクトします。
 * ローディング中は、ローディング表示を行います。
 */
const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  /**
   * ローディング中の表示
   */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  /**
   * 未認証の場合はログインページにリダイレクト
   * 現在のパスを保存して、ログイン後に元のページに戻れるようにする
   */
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  /**
   * 認証済みの場合は子コンポーネントを表示
   */
  return <>{children}</>;
};

export default PrivateRoute;
