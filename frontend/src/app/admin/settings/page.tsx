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
} from "lucide-react";
import { useState } from 'react';
import { toast } from '@/components/ui/use-toast';

export default function AdminSettingsPage() {
  // 設定の状態管理（実際のAPIは後で実装）
  const [settings, setSettings] = useState({
    // メール設定
    emailEnabled: true,
    emailVerificationRequired: true,
    emailFrom: 'noreply@teaminsight.dev',
    emailFromName: 'Team Insight',
    
    // セキュリティ設定
    sessionTimeout: 60, // 分
    passwordMinLength: 8,
    passwordRequireUppercase: true,
    passwordRequireLowercase: true,
    passwordRequireNumber: true,
    passwordRequireSpecial: true,
    
    // Backlog設定
    backlogSyncInterval: 60, // 分
    backlogCacheTimeout: 300, // 秒
    
    // システム設定
    maintenanceMode: false,
    debugMode: false,
    logLevel: 'info',
  });

  const handleSave = () => {
    // TODO: APIで設定を保存
    toast({
      title: "成功",
      description: "設定を保存しました",
    });
  };

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
              <Button onClick={handleSave}>
                <Save className="mr-2 h-4 w-4" />
                設定を保存
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
                    checked={settings.emailEnabled}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, emailEnabled: checked })
                    }
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
                    checked={settings.emailVerificationRequired}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, emailVerificationRequired: checked })
                    }
                  />
                </div>
                
                <Separator />
                
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="email-from">送信元メールアドレス</Label>
                    <Input
                      id="email-from"
                      type="email"
                      value={settings.emailFrom}
                      onChange={(e) => 
                        setSettings({ ...settings, emailFrom: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email-from-name">送信者名</Label>
                    <Input
                      id="email-from-name"
                      value={settings.emailFromName}
                      onChange={(e) => 
                        setSettings({ ...settings, emailFromName: e.target.value })
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
                    value={settings.sessionTimeout}
                    onChange={(e) => 
                      setSettings({ ...settings, sessionTimeout: parseInt(e.target.value) })
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
                      value={settings.passwordMinLength}
                      onChange={(e) => 
                        setSettings({ ...settings, passwordMinLength: parseInt(e.target.value) })
                      }
                    />
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="password-uppercase"
                        checked={settings.passwordRequireUppercase}
                        onCheckedChange={(checked) => 
                          setSettings({ ...settings, passwordRequireUppercase: checked })
                        }
                      />
                      <Label htmlFor="password-uppercase">大文字を必須にする</Label>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="password-lowercase"
                        checked={settings.passwordRequireLowercase}
                        onCheckedChange={(checked) => 
                          setSettings({ ...settings, passwordRequireLowercase: checked })
                        }
                      />
                      <Label htmlFor="password-lowercase">小文字を必須にする</Label>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="password-number"
                        checked={settings.passwordRequireNumber}
                        onCheckedChange={(checked) => 
                          setSettings({ ...settings, passwordRequireNumber: checked })
                        }
                      />
                      <Label htmlFor="password-number">数字を必須にする</Label>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="password-special"
                        checked={settings.passwordRequireSpecial}
                        onCheckedChange={(checked) => 
                          setSettings({ ...settings, passwordRequireSpecial: checked })
                        }
                      />
                      <Label htmlFor="password-special">特殊文字を必須にする</Label>
                    </div>
                  </div>
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
                    value={settings.backlogSyncInterval}
                    onChange={(e) => 
                      setSettings({ ...settings, backlogSyncInterval: parseInt(e.target.value) })
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
                    value={settings.backlogCacheTimeout}
                    onChange={(e) => 
                      setSettings({ ...settings, backlogCacheTimeout: parseInt(e.target.value) })
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
                    checked={settings.maintenanceMode}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, maintenanceMode: checked })
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
                    checked={settings.debugMode}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, debugMode: checked })
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