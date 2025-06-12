/**
 * 認証コールバックページ
 *
 * Backlogからの認証コールバックを処理し、
 * トークンの取得とユーザー情報の保存を行います。
 */

import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

/**
 * 認証コールバックページコンポーネント
 *
 * URLパラメータから認証コードとstateを取得し、
 * バックエンドAPIを通じてトークンを取得します。
 */
const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { handleCallback } = useAuth();

  useEffect(() => {
    const processCallback = async () => {
      try {
        // URLパラメータから認証コードとstateを取得
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        if (!code || !state) {
          throw new Error("認証コードまたはstateが見つかりません");
        }

        // 認証コールバックを処理
        await handleCallback(code, state);

        // 認証成功後、ダッシュボードにリダイレクト
        navigate("/dashboard");
      } catch (error) {
        console.error("認証エラー:", error);
        setError(
          error instanceof Error
            ? error.message
            : "認証処理中にエラーが発生しました"
        );

        // エラー時は3秒後にホームページにリダイレクト
        setTimeout(() => {
          navigate("/");
        }, 3000);
      } finally {
        setLoading(false);
      }
    };

    processCallback();
  }, [navigate, searchParams, handleCallback]);

  /**
   * ローディング表示
   */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">認証処理中...</p>
        </div>
      </div>
    );
  }

  /**
   * エラー表示
   */
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              認証エラー
            </h2>
            <p className="mt-2 text-gray-600">{error}</p>
            <p className="mt-4 text-sm text-gray-500">
              3秒後にホームページにリダイレクトします...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default AuthCallback;
