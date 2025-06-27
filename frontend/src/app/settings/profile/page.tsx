"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Loader2, Mail, CheckCircle, XCircle } from "lucide-react";
import { useAppSelector } from "@/hooks/redux";
import { useRequestEmailVerification, useResendVerificationEmail } from "@/hooks/queries/useAuth";
import { toast } from "@/components/ui/use-toast";

const emailSchema = z.object({
  email: z.string().email("有効なメールアドレスを入力してください"),
});

type EmailFormData = z.infer<typeof emailSchema>;

export default function ProfileSettingsPage() {
  const user = useAppSelector((state) => state.auth.user);
  const [verificationSent, setVerificationSent] = useState(false);
  const requestEmailVerificationMutation = useRequestEmailVerification();
  const resendVerificationEmailMutation = useResendVerificationEmail();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EmailFormData>({
    resolver: zodResolver(emailSchema),
    defaultValues: {
      email: user?.email || "",
    },
  });

  const onSubmit = (data: EmailFormData) => {
    if (data.email === user?.email && user?.is_email_verified) {
      toast({
        title: "変更なし",
        description: "メールアドレスは既に検証済みです",
      });
      return;
    }

    requestEmailVerificationMutation.mutate(
      { email: data.email },
      {
        onSuccess: () => {
          setVerificationSent(true);
        },
      }
    );
  };

  if (!user) {
    return null;
  }

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">プロフィール設定</h1>

      <div className="space-y-6">
        {/* ユーザー基本情報 */}
        <Card>
          <CardHeader>
            <CardTitle>基本情報</CardTitle>
            <CardDescription>Backlogアカウントから取得した情報</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>名前</Label>
              <p className="text-sm text-muted-foreground">{user.name}</p>
            </div>
            <div>
              <Label>ユーザーID</Label>
              <p className="text-sm text-muted-foreground">{user.user_id}</p>
            </div>
            <div>
              <Label>BacklogID</Label>
              <p className="text-sm text-muted-foreground">{user.backlog_id}</p>
            </div>
          </CardContent>
        </Card>

        {/* メールアドレス設定 */}
        <Card>
          <CardHeader>
            <CardTitle>メールアドレス</CardTitle>
            <CardDescription>
              通知やレポートの送信に使用されます
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="email">メールアドレス</Label>
                  {user.is_email_verified ? (
                    <Badge variant="default" className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      検証済み
                    </Badge>
                  ) : user.email ? (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <XCircle className="h-3 w-3" />
                      未検証
                    </Badge>
                  ) : null}
                </div>
                <Input
                  id="email"
                  type="email"
                  {...register("email")}
                  placeholder="your-email@example.com"
                />
                {errors.email && (
                  <p className="text-sm text-red-500">{errors.email.message}</p>
                )}
              </div>

              {verificationSent && (
                <Alert className="border-blue-200 bg-blue-50">
                  <Mail className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-800">
                    検証メールを送信しました。メールをご確認ください。
                  </AlertDescription>
                </Alert>
              )}

              <div className="flex gap-2">
                <Button type="submit" disabled={requestEmailVerificationMutation.isPending}>
                  {requestEmailVerificationMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      送信中...
                    </>
                  ) : (
                    "メールアドレスを更新"
                  )}
                </Button>
                {user.email && !user.is_email_verified && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => resendVerificationEmailMutation.mutate()}
                    disabled={resendVerificationEmailMutation.isPending}
                  >
                    {resendVerificationEmailMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        送信中...
                      </>
                    ) : (
                      "検証メールを再送信"
                    )}
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* ロール情報 */}
        <Card>
          <CardHeader>
            <CardTitle>ロールと権限</CardTitle>
            <CardDescription>
              あなたに割り当てられているロール
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {user.user_roles.length > 0 ? (
                user.user_roles.map((userRole) => (
                  <div key={userRole.id} className="flex items-center gap-2">
                    <Badge>{userRole.role.name}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {userRole.role.description}
                    </span>
                    {userRole.project_id && (
                      <span className="text-sm text-muted-foreground">
                        (プロジェクト限定)
                      </span>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">
                  ロールが割り当てられていません
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}