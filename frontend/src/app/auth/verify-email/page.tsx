"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle2, XCircle, Loader2, Mail } from "lucide-react";
import { authService } from "@/services/auth.service";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");
  
  const [verificationStatus, setVerificationStatus] = useState<"verifying" | "success" | "error" | "no-token">("verifying");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setVerificationStatus("no-token");
        return;
      }

      try {
        const response = await authService.confirmEmailVerification(token);
        setVerificationStatus("success");
        setMessage(response.message);
        
        // 3秒後にダッシュボードにリダイレクト
        setTimeout(() => {
          router.push("/dashboard");
        }, 3000);
      } catch (error: any) {
        setVerificationStatus("error");
        setMessage(
          error.response?.data?.detail || 
          "メールアドレスの検証に失敗しました。"
        );
      }
    };

    verifyEmail();
  }, [token, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">メールアドレスの検証</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {verificationStatus === "verifying" && (
            <div className="text-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin mx-auto text-blue-600" />
              <p className="text-gray-600">メールアドレスを検証しています...</p>
            </div>
          )}

          {verificationStatus === "success" && (
            <div className="text-center space-y-4">
              <CheckCircle2 className="h-12 w-12 mx-auto text-green-600" />
              <Alert className="border-green-200 bg-green-50">
                <AlertDescription className="text-green-800">
                  {message}
                </AlertDescription>
              </Alert>
              <p className="text-sm text-gray-600">
                3秒後にダッシュボードにリダイレクトします...
              </p>
            </div>
          )}

          {verificationStatus === "error" && (
            <div className="text-center space-y-4">
              <XCircle className="h-12 w-12 mx-auto text-red-600" />
              <Alert className="border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">
                  {message}
                </AlertDescription>
              </Alert>
              <div className="space-y-2">
                <Button 
                  onClick={() => router.push("/dashboard")}
                  className="w-full"
                >
                  ダッシュボードに戻る
                </Button>
                <Button 
                  onClick={() => router.push("/settings/profile")}
                  variant="outline"
                  className="w-full"
                >
                  プロフィール設定へ
                </Button>
              </div>
            </div>
          )}

          {verificationStatus === "no-token" && (
            <div className="text-center space-y-4">
              <Mail className="h-12 w-12 mx-auto text-gray-400" />
              <Alert>
                <AlertDescription>
                  検証トークンが見つかりません。メールのリンクから再度アクセスしてください。
                </AlertDescription>
              </Alert>
              <Button 
                onClick={() => router.push("/dashboard")}
                className="w-full"
              >
                ダッシュボードに戻る
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}