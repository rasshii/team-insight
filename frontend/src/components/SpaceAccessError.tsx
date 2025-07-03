"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Home, LogIn } from "lucide-react";
import { useRouter } from "next/navigation";

interface SpaceAccessErrorProps {
  requiredSpace: string;
  userSpace?: string;
}

export function SpaceAccessError({ requiredSpace, userSpace }: SpaceAccessErrorProps) {
  const router = useRouter();
  
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-[500px]">
        <CardHeader>
          <CardTitle className="flex items-center text-red-600">
            <AlertCircle className="mr-2 h-5 w-5" />
            アクセス権限エラー
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>このアプリケーションにアクセスできません</AlertTitle>
            <AlertDescription className="space-y-2 mt-2">
              <p>
                このアプリケーションは <strong>{requiredSpace}</strong> スペースの
                メンバー専用です。
              </p>
              {userSpace && (
                <p className="text-sm">
                  現在のアカウントは <strong>{userSpace}</strong> スペースに
                  所属しています。
                </p>
              )}
            </AlertDescription>
          </Alert>
          
          <div className="bg-muted p-4 rounded-lg space-y-2">
            <p className="font-semibold">アクセスするには：</p>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>{requiredSpace} スペースのメンバーである必要があります</li>
              <li>正しいBacklogアカウントでログインしてください</li>
              <li>アクセス権限について管理者にお問い合わせください</li>
            </ol>
          </div>
          
          <div className="flex flex-col gap-2">
            <Button
              onClick={() => {
                // Backlogからログアウトして再ログイン
                window.open(`https://${requiredSpace}.backlog.jp/Logout.action`, '_blank');
                router.push("/auth/login");
              }}
              className="w-full"
            >
              <LogIn className="mr-2 h-4 w-4" />
              別のアカウントでログイン
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