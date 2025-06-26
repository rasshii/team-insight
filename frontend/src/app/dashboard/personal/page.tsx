"use client";

import { Layout } from "@/components/Layout";
import { PrivateRoute } from "@/components/PrivateRoute";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Activity, 
  AlertCircle, 
  CheckCircle2, 
  Clock,
  TrendingUp,
  CalendarDays 
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale/ja";
import { usePersonalDashboard } from "@/hooks/queries/useAnalytics";
import { Skeleton } from "@/components/ui/skeleton";

export default function PersonalDashboardPage() {
  const { data: dashboard, isLoading, error } = usePersonalDashboard();

  if (isLoading) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6 space-y-6">
            <div className="space-y-3">
              <Skeleton className="h-9 w-64" />
              <Skeleton className="h-5 w-48" />
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <Card key={i}>
                  <CardHeader className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-4" />
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Skeleton className="h-8 w-16" />
                    <Skeleton className="h-3 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </Layout>
      </PrivateRoute>
    );
  }

  if (error) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error instanceof Error ? error.message : 'データの読み込みに失敗しました'}
              </AlertDescription>
            </Alert>
          </div>
        </Layout>
      </PrivateRoute>
    );
  }

  if (!dashboard) {
    return null;
  }

  const { statistics } = dashboard;

  return (
    <PrivateRoute>
      <Layout>
        <div className="container mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                個人ダッシュボード
              </h1>
              <p className="text-muted-foreground mt-1">
                {dashboard.user_name}さんの生産性指標
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4" />
              <span>リアルタイム更新</span>
            </div>
          </div>

          {/* KPIカード */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">総タスク数</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.total_tasks}</div>
                <p className="text-xs text-muted-foreground">
                  アサインされた全タスク
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">完了タスク</CardTitle>
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.completed_tasks}</div>
                <Progress 
                  value={statistics.completion_rate} 
                  className="mt-2 h-2" 
                />
                <p className="text-xs text-muted-foreground mt-1">
                  完了率: {statistics.completion_rate.toFixed(1)}%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">進行中</CardTitle>
                <Clock className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.in_progress_tasks}</div>
                <p className="text-xs text-muted-foreground">
                  現在作業中のタスク
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">期限切れ</CardTitle>
                <AlertCircle className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {statistics.overdue_tasks}
                </div>
                <p className="text-xs text-muted-foreground">
                  期限を過ぎたタスク
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 生産性トレンドと最近完了したタスク */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  生産性サマリー
                </CardTitle>
                <CardDescription>
                  あなたの現在のパフォーマンス状況
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">完了率</span>
                    <span className="text-sm font-bold">
                      {statistics.completion_rate.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={statistics.completion_rate} className="h-2" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">進行中タスク割合</span>
                    <span className="text-sm font-bold">
                      {statistics.total_tasks > 0 
                        ? ((statistics.in_progress_tasks / statistics.total_tasks) * 100).toFixed(1) 
                        : 0}%
                    </span>
                  </div>
                  <Progress 
                    value={statistics.total_tasks > 0 
                      ? (statistics.in_progress_tasks / statistics.total_tasks) * 100 
                      : 0} 
                    className="h-2" 
                  />
                </div>

                {statistics.overdue_tasks > 0 && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {statistics.overdue_tasks}件のタスクが期限切れです。
                      早急な対応が必要です。
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* 最近完了したタスク */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarDays className="h-5 w-5" />
                  最近完了したタスク
                </CardTitle>
                <CardDescription>
                  直近で完了したタスクの一覧
                </CardDescription>
              </CardHeader>
              <CardContent>
                {dashboard.recent_completed_tasks.length > 0 ? (
                  <div className="space-y-3">
                    {dashboard.recent_completed_tasks.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-center justify-between border-b pb-2 last:border-0"
                      >
                        <div className="flex-1 space-y-1">
                          <p className="text-sm font-medium leading-none">
                            {task.title}
                          </p>
                          {task.completed_date && (
                            <p className="text-xs text-muted-foreground">
                              {formatDistanceToNow(new Date(task.completed_date), {
                                addSuffix: true,
                                locale: ja,
                              })}
                            </p>
                          )}
                        </div>
                        <Badge variant="secondary" className="ml-2">
                          完了
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    最近完了したタスクはありません
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* アクションプロンプト */}
          {statistics.overdue_tasks === 0 && statistics.completion_rate > 80 && (
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertDescription>
                素晴らしいパフォーマンスです！この調子で作業を続けましょう。
              </AlertDescription>
            </Alert>
          )}
        </div>
      </Layout>
    </PrivateRoute>
  );
}
