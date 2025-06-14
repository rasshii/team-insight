"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { AlertCircle, Home, RefreshCw } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export function AuthCallbackContent() {
  const { handleCallback, isAuthenticated } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const processedRef = useRef(false);

  useEffect(() => {
    const processCallback = async () => {
      // 既に処理済みまたは処理中の場合はスキップ
      if (processedRef.current || isProcessing) {
        console.log("既に処理済みまたは処理中のためスキップ");
        return;
      }

      const code = searchParams?.get("code");
      const state = searchParams?.get("state");

      if (!code || !state) {
        setError("認証パラメータが不足しています");
        return;
      }

      // 処理開始
      setIsProcessing(true);
      processedRef.current = true;

      try {
        console.log("認証コールバック処理開始", { code, state });
        await handleCallback(code, state);
        console.log("認証コールバック処理成功");
        // 成功したらダッシュボードにリダイレクト
        router.replace("/dashboard");
      } catch (err: any) {
        console.error("認証コールバックの処理に失敗しました:", err);
        const errorMessage =
          err?.response?.data?.detail ||
          err?.message ||
          "認証処理に失敗しました";
        setError(errorMessage);
        setIsProcessing(false);
        // エラー時は再試行しない
      }
    };

    // 認証済みの場合はダッシュボードにリダイレクト
    if (isAuthenticated) {
      router.replace("/dashboard");
      return;
    }

    processCallback();
  }, [searchParams, handleCallback, router, isAuthenticated, isProcessing]);

  // エラー表示
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center text-red-600">
              認証エラー
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>エラーが発生しました</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>

            <div className="flex flex-col gap-2">
              <Button
                onClick={() => router.push("/auth/login")}
                variant="default"
                className="w-full"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                もう一度ログインする
              </Button>
              <Button
                onClick={() => router.push("/")}
                variant="outline"
                className="w-full"
              >
                <Home className="mr-2 h-4 w-4" />
                ホームに戻る
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 処理中の表示
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <svg
              className="animate-spin h-8 w-8 text-blue-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          </div>
        </div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          認証処理中...
        </h2>
        <p className="text-gray-600">
          Backlogアカウントの認証を行っています。
          <br />
          しばらくお待ちください。
        </p>
      </div>
    </div>
  );
}
