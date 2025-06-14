"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export function AuthCallbackContent() {
  const { handleCallback } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      try {
        // URLパラメータから認証コードとstateを取得
        const code = searchParams?.get("code");
        const state = searchParams?.get("state");

        if (!code || !state) {
          throw new Error("認証パラメータが不足しています");
        }

        // 認証コールバックを処理
        await handleCallback(code, state);

        // 認証成功後、ダッシュボードにリダイレクト
        router.replace("/dashboard");
      } catch (err) {
        console.error("認証コールバックの処理に失敗しました:", err);
        setError("認証に失敗しました。もう一度お試しください。");
      }
    };

    processCallback();
  }, [handleCallback, router, searchParams]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-6 shadow-lg">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600">エラー</h2>
            <p className="mt-2 text-gray-600">{error}</p>
            <button
              onClick={() => router.push("/auth/login")}
              className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              ログインページに戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">認証を処理中...</p>
      </div>
    </div>
  );
}
