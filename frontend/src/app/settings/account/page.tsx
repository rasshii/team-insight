"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useUserSettings, useUpdateUserSettings } from "@/hooks/queries/useUserSettings";
import { TIMEZONES, LOCALES, DATE_FORMATS, REPORT_FREQUENCIES } from "@/types/user-settings";
import { useState, useEffect } from "react";
import { User, Mail, Globe, Calendar, Bell, AlertCircle } from "lucide-react";

export default function AccountSettingsPage() {
  const { data: userSettings, isLoading, error } = useUserSettings();
  const updateSettingsMutation = useUpdateUserSettings();

  const [formData, setFormData] = useState({
    name: "",
    timezone: "Asia/Tokyo",
    locale: "ja",
    date_format: "YYYY-MM-DD",
    email_notifications: true,
    report_frequency: "weekly",
    notification_email: "",
  });

  useEffect(() => {
    if (userSettings) {
      setFormData({
        name: userSettings.name || "",
        timezone: userSettings.timezone,
        locale: userSettings.locale,
        date_format: userSettings.date_format,
        email_notifications: userSettings.preferences?.email_notifications ?? true,
        report_frequency: userSettings.preferences?.report_frequency || "weekly",
        notification_email: userSettings.preferences?.notification_email || "",
      });
    }
  }, [userSettings]);

  const handleSubmit = () => {
    updateSettingsMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">アカウント設定</h2>
          <p className="text-muted-foreground">
            アカウント情報と通知設定を管理します
          </p>
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-96 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !userSettings) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">アカウント設定</h2>
          <p className="text-muted-foreground">
            アカウント情報と通知設定を管理します
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            設定の読み込みに失敗しました。再度お試しください。
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">アカウント設定</h2>
        <p className="text-muted-foreground">
          アカウント情報と通知設定を管理します
        </p>
      </div>

      {/* 基本情報 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            基本情報
          </CardTitle>
          <CardDescription>
            表示名やメールアドレスの確認・変更ができます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">表示名</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="山田 太郎"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">メールアドレス</Label>
            <Input
              id="email"
              type="email"
              value={userSettings.email || ""}
              disabled
              className="bg-muted"
            />
            <p className="text-sm text-muted-foreground">
              メールアドレスはBacklogアカウントから取得されます
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="backlog-id">Backlog ID</Label>
            <Input
              id="backlog-id"
              value={userSettings.backlog_id?.toString() || "未設定"}
              disabled
              className="bg-muted"
            />
          </div>
        </CardContent>
      </Card>

      {/* 地域と言語 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            地域と言語
          </CardTitle>
          <CardDescription>
            タイムゾーンと表示言語の設定
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="timezone">タイムゾーン</Label>
            <Select
              value={formData.timezone}
              onValueChange={(value) => setFormData({ ...formData, timezone: value })}
            >
              <SelectTrigger id="timezone">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="locale">言語</Label>
            <Select
              value={formData.locale}
              onValueChange={(value) => setFormData({ ...formData, locale: value })}
            >
              <SelectTrigger id="locale">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LOCALES.map((locale) => (
                  <SelectItem key={locale.value} value={locale.value}>
                    {locale.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="date-format">日付フォーマット</Label>
            <Select
              value={formData.date_format}
              onValueChange={(value) => setFormData({ ...formData, date_format: value })}
            >
              <SelectTrigger id="date-format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DATE_FORMATS.map((format) => (
                  <SelectItem key={format.value} value={format.value}>
                    {format.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 通知設定 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            通知設定
          </CardTitle>
          <CardDescription>
            メール通知とレポート配信の設定
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="email-notifications">メール通知</Label>
              <p className="text-sm text-muted-foreground">
                重要な更新やレポートをメールで受信します
              </p>
            </div>
            <Switch
              id="email-notifications"
              checked={formData.email_notifications}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, email_notifications: checked })
              }
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label htmlFor="report-frequency">レポート配信頻度</Label>
            <Select
              value={formData.report_frequency}
              onValueChange={(value) =>
                setFormData({ ...formData, report_frequency: value })
              }
              disabled={!formData.email_notifications}
            >
              <SelectTrigger id="report-frequency">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {REPORT_FREQUENCIES.map((freq) => (
                  <SelectItem key={freq.value} value={freq.value}>
                    {freq.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notification-email">通知先メールアドレス</Label>
            <Input
              id="notification-email"
              type="email"
              value={formData.notification_email}
              onChange={(e) =>
                setFormData({ ...formData, notification_email: e.target.value })
              }
              placeholder="通知を受け取るメールアドレス（空欄の場合はメインアドレス）"
              disabled={!formData.email_notifications}
            />
          </div>
        </CardContent>
      </Card>

      {/* 保存ボタン */}
      <div className="flex justify-end">
        <Button
          onClick={handleSubmit}
          disabled={updateSettingsMutation.isPending}
        >
          {updateSettingsMutation.isPending ? "保存中..." : "変更を保存"}
        </Button>
      </div>
    </div>
  );
}