"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { AlertCircle, LogIn } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export function LoginContent() {
  const { isAuthenticated, login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (isAuthenticated) {
      const from = searchParams?.get("from") || "/dashboard/personal";
      router.replace(from);
    }
  }, [isAuthenticated, router, searchParams]);

  const error = searchParams?.get("error");

  const handleLogin = () => {
    login();
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-[400px]">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl">Team Insightにログイン</CardTitle>
          <CardDescription>
            Backlogアカウントを使用してログインします
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>エラー</AlertTitle>
              <AlertDescription>
                {error === "auth_failed"
                  ? "認証に失敗しました。もう一度お試しください。"
                  : "エラーが発生しました。"}
              </AlertDescription>
            </Alert>
          )}
          <Button
            onClick={handleLogin}
            className="w-full"
            size="lg"
          >
            <LogIn className="mr-2 h-4 w-4" />
            Backlogでログイン
          </Button>
          <p className="text-center text-sm text-gray-500">
            ログインすることで、利用規約とプライバシーポリシーに同意したものとみなされます。
          </p>
        </CardContent>
      </Card>
    </div>
  );
}