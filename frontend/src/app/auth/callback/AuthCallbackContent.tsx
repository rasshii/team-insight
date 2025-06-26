"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHandleAuthCallback } from "@/hooks/queries/useAuth";
import { AlertCircle, Home, RefreshCw } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";

export function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const processedRef = useRef(false);
  
  // 認証コールバック処理のミューテーション
  const authCallbackMutation = useHandleAuthCallback();

  useEffect(() => {
    const processCallback = async () => {
      // 既に処理済みの場合はスキップ
      if (processedRef.current) {
        return;
      }

      const code = searchParams?.get("code");
      const state = searchParams?.get("state");

      if (!code || !state) {
        return;
      }

      // 処理済みフラグを立てる
      processedRef.current = true;

      // 認証コールバック処理を実行
      authCallbackMutation.mutate({ code, state });
    };

    processCallback();
  }, [searchParams, authCallbackMutation]);

  // エラー状態
  if (authCallbackMutation.isError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Card className="w-[400px]">
          <CardHeader>
            <CardTitle className="flex items-center text-red-600">
              <AlertCircle className="mr-2 h-5 w-5" />
              認証エラー
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>エラーが発生しました</AlertTitle>
              <AlertDescription>
                {authCallbackMutation.error instanceof Error 
                  ? authCallbackMutation.error.message 
                  : "認証処理中にエラーが発生しました"}
              </AlertDescription>
            </Alert>
            <div className="flex flex-col gap-2">
              <Button
                onClick={() => router.push("/auth/login")}
                variant="outline"
                className="w-full"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                もう一度ログイン
              </Button>
              <Button
                onClick={() => router.push("/")}
                variant="ghost"
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

  // 成功時はミューテーション内でリダイレクトされるため、
  // ここではローディング状態のみ表示
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-[400px]">
        <CardHeader>
          <CardTitle>認証処理中...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-500" />
          </div>
          <p className="text-center text-sm text-gray-500">
            Backlogアカウントの認証を処理しています...
          </p>
        </CardContent>
      </Card>
    </div>
  );
}