"use client";

import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Mail, X, Loader2 } from "lucide-react";
import { useAppSelector } from "@/store/hooks";
import { authService } from "@/services/auth.service";
import { toast } from "@/components/ui/use-toast";

export function EmailVerificationBanner() {
  const user = useAppSelector((state) => state.auth.user);
  const [isLoading, setIsLoading] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  // バナーを表示しない条件
  if (!user || user.is_email_verified || !user.email || isDismissed) {
    return null;
  }

  const handleResendVerification = async () => {
    setIsLoading(true);
    try {
      const response = await authService.resendVerificationEmail();
      toast({
        title: "検証メールを送信しました",
        description: response.message,
      });
    } catch (error: any) {
      toast({
        title: "エラー",
        description: error.response?.data?.detail || "メールの送信に失敗しました",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Alert className="border-yellow-200 bg-yellow-50 relative">
      <Mail className="h-4 w-4 text-yellow-600" />
      <AlertDescription className="ml-2 pr-8">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <span className="text-yellow-800 font-medium">
              メールアドレスの確認が必要です
            </span>
            <p className="text-sm text-yellow-700 mt-1">
              {user.email} に確認メールを送信しました。メールをご確認ください。
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleResendVerification}
            disabled={isLoading}
            className="ml-4 border-yellow-600 text-yellow-600 hover:bg-yellow-100"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                送信中...
              </>
            ) : (
              "確認メールを再送信"
            )}
          </Button>
        </div>
      </AlertDescription>
      <button
        onClick={() => setIsDismissed(true)}
        className="absolute top-2 right-2 text-yellow-600 hover:text-yellow-800"
        aria-label="閉じる"
      >
        <X className="h-4 w-4" />
      </button>
    </Alert>
  );
}