"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Link2,
  Unlink,
  Clock,
  Database,
  Activity,
  Loader2
} from "lucide-react";
import { useConnectionStatus, useSyncHistory, useSyncAllProjects, useSyncUserTasks } from "@/hooks/queries/useSync";
import { useGetAuthorizationUrl, useLogout } from "@/hooks/queries/useAuth";
import { cn } from "@/lib/utils";


export default function BacklogSettingsPage() {
  const router = useRouter();
  const [syncProgress, setSyncProgress] = useState(0);
  
  // React Queryフックを使用
  const { data: connectionStatus, isLoading: connectionLoading, error: connectionError } = useConnectionStatus();
  const { data: syncHistoryData, isLoading: historyLoading } = useSyncHistory({ days: 7, limit: 20 });
  const syncAllProjectsMutation = useSyncAllProjects();
  const syncUserTasksMutation = useSyncUserTasks();
  const getAuthorizationUrlMutation = useGetAuthorizationUrl();
  const logoutMutation = useLogout();

  // Backlogに接続
  const handleConnect = () => {
    // Backlog OAuth認証フローを開始
    getAuthorizationUrlMutation.mutate();
  };

  // 接続を解除
  const handleDisconnect = () => {
    if (!confirm("Backlogとの連携を解除しますか？")) {
      return;
    }

    // ログアウト処理
    logoutMutation.mutate();
  };

  // 全プロジェクトを同期
  const handleSyncAllProjects = () => {
    setSyncProgress(10);
    syncAllProjectsMutation.mutate(undefined, {
      onSuccess: () => {
        setSyncProgress(100);
        setTimeout(() => setSyncProgress(0), 1000);
      },
      onError: () => {
        setSyncProgress(0);
      },
    });
  };

  // ユーザータスクを同期
  const handleSyncUserTasks = () => {
    setSyncProgress(10);
    syncUserTasksMutation.mutate(undefined, {
      onSuccess: () => {
        setSyncProgress(100);
        setTimeout(() => setSyncProgress(0), 1000);
      },
      onError: () => {
        setSyncProgress(0);
      },
    });
  };

  // 接続状態のアイコンとスタイル
  const getConnectionStatusIcon = () => {
    if (connectionLoading) return <Loader2 className="h-5 w-5 animate-spin" />;
    if (!connectionStatus) return <XCircle className="h-5 w-5" />;
    
    switch (connectionStatus.status) {
      case 'active':
        return <CheckCircle2 className="h-5 w-5" />;
      case 'expired':
        return <AlertCircle className="h-5 w-5" />;
      case 'no_token':
        return <XCircle className="h-5 w-5" />;
      default:
        return <AlertCircle className="h-5 w-5" />;
    }
  };

  const getConnectionStatusColor = () => {
    if (!connectionStatus) return "text-destructive";
    
    switch (connectionStatus.status) {
      case 'active':
        return "text-green-600";
      case 'expired':
        return "text-yellow-600";
      case 'no_token':
        return "text-destructive";
      default:
        return "text-muted-foreground";
    }
  };

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "なし";
    return format(new Date(dateString), "yyyy年MM月dd日 HH:mm", { locale: ja });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Backlog連携設定</h2>
        <p className="text-muted-foreground">
          BacklogアカウントとTeam Insightを連携して、プロジェクトやタスクのデータを同期します。
        </p>
      </div>

      {(connectionError || syncAllProjectsMutation.error || syncUserTasksMutation.error) && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>エラー</AlertTitle>
          <AlertDescription>
            {connectionError instanceof Error ? connectionError.message : 
             syncAllProjectsMutation.error instanceof Error ? syncAllProjectsMutation.error.message :
             syncUserTasksMutation.error instanceof Error ? syncUserTasksMutation.error.message :
             'エラーが発生しました'}
          </AlertDescription>
        </Alert>
      )}

      {/* 接続状態カード */}
      <Card>
        <CardHeader>
          <CardTitle>接続状態</CardTitle>
          <CardDescription>
            Backlogアカウントとの連携状態を確認・管理します
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn("p-2 rounded-full bg-muted", getConnectionStatusColor())}>
                  {getConnectionStatusIcon()}
                </div>
                <div>
                  <p className="font-medium">
                    {connectionLoading ? "読み込み中..." : connectionStatus?.message || "接続されていません"}
                  </p>
                  {connectionStatus?.expires_at && (
                    <p className="text-sm text-muted-foreground">
                      有効期限: {formatDate(connectionStatus.expires_at)}
                    </p>
                  )}
                </div>
              </div>
              <div>
                {connectionStatus?.connected ? (
                  <Button
                    variant="outline"
                    onClick={handleDisconnect}
                    disabled={loading}
                  >
                    <Unlink className="mr-2 h-4 w-4" />
                    連携を解除
                  </Button>
                ) : (
                  <Button
                    onClick={handleConnect}
                    disabled={loading}
                  >
                    <Link2 className="mr-2 h-4 w-4" />
                    Backlogに接続
                  </Button>
                )}
              </div>
            </div>

            {connectionStatus?.connected && (
              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm text-muted-foreground">最終プロジェクト同期</p>
                  <p className="font-medium">
                    {formatDate(connectionStatus.last_project_sync)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">最終タスク同期</p>
                  <p className="font-medium">
                    {formatDate(connectionStatus.last_task_sync)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 同期操作 */}
      {connectionStatus?.connected && (
        <Card>
          <CardHeader>
            <CardTitle>データ同期</CardTitle>
            <CardDescription>
              Backlogからプロジェクトやタスクのデータを同期します
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="projects" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="projects">プロジェクト</TabsTrigger>
                <TabsTrigger value="tasks">タスク</TabsTrigger>
              </TabsList>
              
              <TabsContent value="projects" className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Backlogから全てのプロジェクトとメンバー情報を同期します。
                  </p>
                  <Button
                    onClick={handleSyncAllProjects}
                    disabled={syncAllProjectsMutation.isPending || !connectionStatus?.connected}
                    className="w-full"
                  >
                    {syncAllProjectsMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        同期中...
                      </>
                    ) : (
                      <>
                        <Database className="mr-2 h-4 w-4" />
                        全プロジェクトを同期
                      </>
                    )}
                  </Button>
                </div>
              </TabsContent>
              
              <TabsContent value="tasks" className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    あなたに割り当てられているタスクを同期します。
                  </p>
                  <Button
                    onClick={handleSyncUserTasks}
                    disabled={syncUserTasksMutation.isPending || !connectionStatus?.connected}
                    className="w-full"
                  >
                    {syncUserTasksMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        同期中...
                      </>
                    ) : (
                      <>
                        <Activity className="mr-2 h-4 w-4" />
                        自分のタスクを同期
                      </>
                    )}
                  </Button>
                </div>
              </TabsContent>
            </Tabs>

            {/* 同期進捗 */}
            {syncProgress > 0 && (
              <div className="mt-4 space-y-2">
                <Progress value={syncProgress} className="w-full" />
                <p className="text-sm text-center text-muted-foreground">
                  同期中... {syncProgress}%
                </p>
              </div>
            )}

            {/* 最終同期結果 */}
            {(syncAllProjectsMutation.isSuccess || syncUserTasksMutation.isSuccess) && syncProgress === 0 && (
              <Alert className="mt-4">
                <CheckCircle2 className="h-4 w-4" />
                <AlertTitle>同期完了</AlertTitle>
                <AlertDescription>
                  {syncAllProjectsMutation.data?.message || syncUserTasksMutation.data?.message}
                  {(syncAllProjectsMutation.data || syncUserTasksMutation.data) && (
                    <span className="block mt-1">
                      作成: {syncAllProjectsMutation.data?.items_created || syncUserTasksMutation.data?.items_created || 0}件、
                      更新: {syncAllProjectsMutation.data?.items_updated || syncUserTasksMutation.data?.items_updated || 0}件、
                      合計: {syncAllProjectsMutation.data?.total_items || syncUserTasksMutation.data?.total_items || 0}件
                    </span>
                  )}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* 同期設定 */}
      {connectionStatus?.connected && (
        <Card>
          <CardHeader>
            <CardTitle>同期設定</CardTitle>
            <CardDescription>
              自動同期やその他の設定を管理します
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">自動同期</p>
                  <p className="text-sm text-muted-foreground">
                    定期的にデータを自動で同期します
                  </p>
                </div>
                <Badge variant="outline">
                  <Clock className="mr-1 h-3 w-3" />
                  準備中
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">同期間隔</p>
                  <p className="text-sm text-muted-foreground">
                    自動同期の実行間隔
                  </p>
                </div>
                <Badge variant="outline">15分</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 同期履歴 */}
      {connectionStatus?.connected && (
        <Card>
          <CardHeader>
            <CardTitle>同期履歴</CardTitle>
            <CardDescription>
              過去7日間の同期履歴を表示します
            </CardDescription>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-5 w-16" />
                    </div>
                    <Skeleton className="h-3 w-48" />
                  </div>
                ))}
              </div>
            ) : !syncHistoryData?.histories || syncHistoryData.histories.length === 0 ? (
              <p className="text-center py-8 text-muted-foreground">
                同期履歴がありません
              </p>
            ) : (
              <div className="space-y-2">
                {syncHistoryData.histories.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "p-1.5 rounded-full",
                        item.status === 'COMPLETED' ? "bg-green-100 text-green-600" :
                        item.status === 'FAILED' ? "bg-red-100 text-red-600" :
                        "bg-yellow-100 text-yellow-600"
                      )}>
                        {item.status === 'COMPLETED' ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : item.status === 'FAILED' ? (
                          <XCircle className="h-4 w-4" />
                        ) : (
                          <RefreshCw className="h-4 w-4" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-sm">
                          {item.sync_type === 'USER_TASKS' ? 'ユーザータスク' :
                           item.sync_type === 'PROJECT_TASKS' ? 'プロジェクトタスク' :
                           item.sync_type === 'ALL_PROJECTS' ? '全プロジェクト' :
                           item.sync_type}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {item.target_name || 'ー'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm">
                        {item.started_at && formatDate(item.started_at)}
                      </p>
                      {item.status === 'COMPLETED' && item.total_items !== undefined && (
                        <p className="text-xs text-muted-foreground">
                          作成: {item.items_created || 0}件、
                          更新: {item.items_updated || 0}件
                        </p>
                      )}
                      {item.status === 'FAILED' && item.error_message && (
                        <p className="text-xs text-red-600">
                          {item.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}