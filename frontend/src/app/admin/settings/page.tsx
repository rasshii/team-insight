"use client";

import { Layout } from "@/components/Layout";
import { PrivateRoute } from "@/components/PrivateRoute";
import { AdminOnly } from "@/components/auth/AdminOnly";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Settings,
  Mail,
  Database,
  Shield,
  RefreshCw,
  Save,
  Info,
  Server,
  Link2,
  Clock,
  FileText,
  AlertCircle,
} from "lucide-react";
import { useState, useEffect } from 'react';
import { toast } from '@/components/ui/use-toast';
import { useSettings, useUpdateSettings } from '@/hooks/queries/useSettings';
import { AllSettings } from '@/types/settings';

export default function AdminSettingsPage() {
  const { data: settingsData, isLoading, error } = useSettings();
  const updateSettingsMutation = useUpdateSettings();
  
  const [settings, setSettings] = useState<AllSettings | null>(null);

  // APIから取得したデータで初期化
  useEffect(() => {
    if (settingsData) {
      setSettings(settingsData);
    }
  }, [settingsData]);

  const handleSave = () => {
    if (!settings) return;
    
    updateSettingsMutation.mutate(settings);
  };

  if (isLoading) {
    return (
      <PrivateRoute>
        <AdminOnly>
          <Layout>
            <div className="container mx-auto p-6 space-y-6">
              <Skeleton className="h-12 w-64" />
              <Skeleton className="h-96 w-full" />
              <Skeleton className="h-96 w-full" />
              <Skeleton className="h-96 w-full" />
            </div>
          </Layout>
        </AdminOnly>
      </PrivateRoute>
    );
  }

  if (error || !settings) {
    return (
      <PrivateRoute>
        <AdminOnly>
          <Layout>
            <div className="container mx-auto p-6">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  設定の読み込みに失敗しました。再度お試しください。
                </AlertDescription>
              </Alert>
            </div>
          </Layout>
        </AdminOnly>
      </PrivateRoute>
    );
  }

  return (
    <PrivateRoute>
      <AdminOnly>
        <Layout>
          <div className="container mx-auto p-6 space-y-6">
            {/* ヘッダー */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                  <Settings className="h-8 w-8" />
                  システム設定
                </h1>
                <p className="text-muted-foreground mt-1">
                  システム全体の設定を管理します
                </p>
              </div>
              <Button 
                onClick={handleSave}
                disabled={updateSettingsMutation.isPending}
              >
                <Save className="mr-2 h-4 w-4" />
                {updateSettingsMutation.isPending ? '保存中...' : '設定を保存'}
              </Button>
            </div>

            {/* メール設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  メール設定
                </CardTitle>
                <CardDescription>
                  メール送信と認証に関する設定
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="email-enabled">メール機能</Label>
                    <p className="text-sm text-muted-foreground">
                      メール送信機能を有効にします
                    </p>
                  </div>
                  <Switch
                    id="email-enabled"
                    disabled={true}
                    checked={true}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="email-verification">メール認証必須</Label>
                    <p className="text-sm text-muted-foreground">
                      新規ユーザーのメールアドレス認証を必須にします
                    </p>
                  </div>
                  <Switch
                    id="email-verification"
                    disabled={true}
                    checked={true}
                  />
                </div>
                
                <Separator />
                
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="email-from">送信元メールアドレス</Label>
                    <Input
                      id="email-from"
                      type="email"
                      value={settings.email.email_from}
                      onChange={(e) => 
                        setSettings({ 
                          ...settings, 
                          email: { ...settings.email, email_from: e.target.value }
                        })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email-from-name">送信者名</Label>
                    <Input
                      id="email-from-name"
                      value={settings.email.email_from_name}
                      onChange={(e) => 
                        setSettings({ 
                          ...settings, 
                          email: { ...settings.email, email_from_name: e.target.value }
                        })
                      }
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* セキュリティ設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  セキュリティ設定
                </CardTitle>
                <CardDescription>
                  セキュリティとパスワードポリシーに関する設定
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="session-timeout">セッションタイムアウト（分）</Label>
                  <Input
                    id="session-timeout"
                    type="number"
                    value={settings.security.session_timeout}
                    onChange={(e) => 
                      setSettings({ 
                        ...settings, 
                        security: { ...settings.security, session_timeout: parseInt(e.target.value) || 0 }
                      })
                    }
                  />
                  <p className="text-sm text-muted-foreground">
                    無操作時に自動的にログアウトするまでの時間
                  </p>
                </div>
                
                <Separator />
                
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">パスワードポリシー</h4>
                  
                  <div className="space-y-2">
                    <Label htmlFor="password-length">最小文字数</Label>
                    <Input
                      id="password-length"
                      type="number"
                      value={settings.security.password_min_length}
                      onChange={(e) => 
                        setSettings({ 
                          ...settings, 
                          security: { ...settings.security, password_min_length: parseInt(e.target.value) || 0 }
                        })
                      }
                    />
                  </div>
                  
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      パスワードは以下の条件を満たす必要があります：
                      <ul className="list-disc list-inside mt-2">
                        <li>大文字を含む</li>
                        <li>小文字を含む</li>
                        <li>数字を含む</li>
                        <li>特殊文字を含む</li>
                      </ul>
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>

            {/* Backlog連携設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Link2 className="h-5 w-5" />
                  Backlog連携設定
                </CardTitle>
                <CardDescription>
                  Backlog APIとの連携に関する設定
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="sync-interval">自動同期間隔（分）</Label>
                  <Input
                    id="sync-interval"
                    type="number"
                    value={settings.sync.backlog_sync_interval}
                    onChange={(e) => 
                      setSettings({ 
                        ...settings, 
                        sync: { ...settings.sync, backlog_sync_interval: parseInt(e.target.value) || 0 }
                      })
                    }
                  />
                  <p className="text-sm text-muted-foreground">
                    Backlogデータを自動的に同期する間隔
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="cache-timeout">キャッシュ有効期限（秒）</Label>
                  <Input
                    id="cache-timeout"
                    type="number"
                    value={settings.sync.backlog_cache_timeout}
                    onChange={(e) => 
                      setSettings({ 
                        ...settings, 
                        sync: { ...settings.sync, backlog_cache_timeout: parseInt(e.target.value) || 0 }
                      })
                    }
                  />
                  <p className="text-sm text-muted-foreground">
                    APIレスポンスのキャッシュ保持時間
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* システム設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  システム設定
                </CardTitle>
                <CardDescription>
                  システム全体の動作に関する設定
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="maintenance-mode">メンテナンスモード</Label>
                    <p className="text-sm text-muted-foreground">
                      ユーザーのアクセスを一時的に制限します
                    </p>
                  </div>
                  <Switch
                    id="maintenance-mode"
                    checked={settings.system.maintenance_mode}
                    onCheckedChange={(checked) => 
                      setSettings({ 
                        ...settings, 
                        system: { ...settings.system, maintenance_mode: checked }
                      })
                    }
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="debug-mode">デバッグモード</Label>
                    <p className="text-sm text-muted-foreground">
                      詳細なエラー情報を表示します（開発環境のみ推奨）
                    </p>
                  </div>
                  <Switch
                    id="debug-mode"
                    checked={settings.system.debug_mode}
                    onCheckedChange={(checked) => 
                      setSettings({ 
                        ...settings, 
                        system: { ...settings.system, debug_mode: checked }
                      })
                    }
                  />
                </div>
              </CardContent>
            </Card>

            {/* 情報 */}
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                一部の設定変更はシステムの再起動が必要な場合があります。
                変更を適用する前に、影響を十分に確認してください。
              </AlertDescription>
            </Alert>
          </div>
        </Layout>
      </AdminOnly>
    </PrivateRoute>
  );
}