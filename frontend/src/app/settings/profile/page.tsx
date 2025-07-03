"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { CheckCircle, Mail, User, Hash, Users, Folder } from "lucide-react";
import { useAppSelector } from "@/store/hooks";
import { Layout } from "@/components/Layout";
import { PrivateRoute } from "@/components/PrivateRoute";
import { useProjects } from "@/hooks/queries/useProjects";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricLabel } from "@/components/ui/metric-tooltip";

export default function ProfileSettingsPage() {
  const user = useAppSelector((state) => state.auth.user);
  const { data: projectsData, isLoading: projectsLoading } = useProjects();

  if (!user) {
    return null;
  }

  // プロジェクトIDから名前を取得するヘルパー関数
  const getProjectName = (projectId: number) => {
    if (!projectsData) return `プロジェクトID: ${projectId}`;
    const project = projectsData.projects.find(p => p.id === projectId);
    return project ? project.name : `プロジェクトID: ${projectId}`;
  };

  return (
    <PrivateRoute>
      <Layout>
        <div className="container mx-auto py-8 max-w-4xl">
          <h1 className="text-3xl font-bold mb-8">プロフィール設定</h1>

          <div className="space-y-6">
            {/* ユーザー基本情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  基本情報
                </CardTitle>
                <CardDescription>Backlogアカウントから取得した情報</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>名前</Label>
                  <p className="text-lg font-medium mt-1">{user.name}</p>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label>ユーザーID</Label>
                    <p className="text-sm text-muted-foreground mt-1">{user.user_id}</p>
                  </div>
                  <div>
                    <Label>BacklogID</Label>
                    <p className="text-sm text-muted-foreground mt-1">{user.backlog_id}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* メールアドレス情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  メールアドレス
                </CardTitle>
                <CardDescription>
                  Backlogアカウントに登録されているメールアドレス
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-lg font-medium">{user.email || "未設定"}</p>
                    {user.email && (
                      <p className="text-sm text-muted-foreground">
                        レポート配信やシステム通知はこのアドレスに送信されます
                      </p>
                    )}
                  </div>
                  {user.email && (
                    <Badge variant="default" className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Backlog連携
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* ロール情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  ロールと権限
                </CardTitle>
                <CardDescription>
                  Team Insightでのアクセス権限
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {user.user_roles && user.user_roles.length > 0 ? (
                    <>
                      <div className="space-y-2">
                        <MetricLabel metric="globalRole">
                          グローバルロール
                        </MetricLabel>
                        {user.user_roles
                          .filter(userRole => !userRole.project_id)
                          .map((userRole) => (
                            <div key={userRole.id} className="p-3 bg-muted/50 rounded-lg space-y-1">
                              <div className="flex items-center gap-2">
                                <Badge 
                                  variant={userRole.role.name === 'ADMIN' ? 'destructive' : 
                                          userRole.role.name === 'PROJECT_LEADER' ? 'default' : 'secondary'}
                                >
                                  {userRole.role.name === 'ADMIN' ? '管理者' :
                                   userRole.role.name === 'PROJECT_LEADER' ? 'プロジェクトリーダー' :
                                   userRole.role.name === 'MEMBER' ? 'メンバー' :
                                   userRole.role.name}
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  全プロジェクト共通
                                </span>
                              </div>
                              {userRole.role.description && (
                                <p className="text-sm text-muted-foreground">
                                  {userRole.role.description}
                                </p>
                              )}
                            </div>
                          ))}
                        {user.user_roles.filter(ur => !ur.project_id).length === 0 && (
                          <p className="text-sm text-muted-foreground">なし</p>
                        )}
                      </div>
                      
                      <div className="space-y-2">
                        <MetricLabel metric="projectRole">
                          プロジェクトロール
                        </MetricLabel>
                        {projectsLoading ? (
                          <div className="space-y-2">
                            <Skeleton className="h-6 w-48" />
                            <Skeleton className="h-6 w-48" />
                          </div>
                        ) : (
                          <>
                            {user.user_roles
                              .filter(userRole => userRole.project_id)
                              .map((userRole) => (
                                <div key={userRole.id} className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <Folder className="h-4 w-4 text-muted-foreground" />
                                    <span className="font-medium">
                                      {getProjectName(userRole.project_id!)}
                                    </span>
                                  </div>
                                  <div className="ml-6 flex items-center gap-2">
                                    <Badge variant="secondary">
                                      {userRole.role.name}
                                    </Badge>
                                    {userRole.role.description && (
                                      <span className="text-sm text-muted-foreground">
                                        {userRole.role.description}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              ))}
                            {user.user_roles.filter(ur => ur.project_id).length === 0 && (
                              <p className="text-sm text-muted-foreground">なし</p>
                            )}
                          </>
                        )}
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      ロールが割り当てられていません
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* アカウント状態 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Hash className="h-5 w-5" />
                  アカウント状態
                </CardTitle>
                <CardDescription>
                  アカウントのステータス情報
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>ログイン状態</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      システムへのアクセス可否
                    </p>
                  </div>
                  <Badge variant={user.is_active ? "default" : "destructive"}>
                    {user.is_active ? "有効" : "無効"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>連携状態</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Backlog APIとの接続状態
                    </p>
                  </div>
                  <Badge variant="default">
                    接続済み
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </Layout>
    </PrivateRoute>
  );
}