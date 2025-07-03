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
import { Button } from "@/components/ui/button";
import { 
  Activity, 
  AlertCircle, 
  CheckCircle2, 
  Clock,
  TrendingUp,
  CalendarDays,
  RefreshCw,
  BarChart3,
  Workflow 
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale/ja";
import { usePersonalDashboard } from "@/hooks/queries/useAnalytics";
import { Skeleton } from "@/components/ui/skeleton";
import { ThroughputChart } from "@/components/charts/ThroughputChart";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { syncService } from "@/services/sync.service";
import { toast } from "@/components/ui/use-toast";
import { queryKeys } from "@/lib/react-query";
import { getTaskStatusLabel } from "@/lib/task-utils";
import { MetricTooltip, MetricLabel } from "@/components/ui/metric-tooltip";

export default function PersonalDashboardPage() {
  const { data: dashboard, isLoading, error } = usePersonalDashboard();
  const queryClient = useQueryClient();
  
  // タスク同期ミューテーション
  const syncTasksMutation = useMutation({
    mutationFn: () => syncService.syncUserTasks(),
    onSuccess: () => {
      // 関連するクエリを無効化して再取得
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.personalDashboard });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast({
        title: "同期完了",
        description: "タスクデータを最新の状態に更新しました。",
      });
    },
    onError: (error) => {
      toast({
        title: "同期エラー",
        description: "タスクの同期に失敗しました。",
        variant: "destructive",
      });
      console.error('Sync error:', error);
    }
  });
  
  console.log('Dashboard data:', dashboard);
  console.log('Loading state:', isLoading);
  console.log('Error state:', error);

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
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                ダッシュボードデータの読み込みに失敗しました。
              </AlertDescription>
            </Alert>
          </div>
        </Layout>
      </PrivateRoute>
    );
  }

  const statistics = dashboard?.kpi_summary || {
    total_tasks: 0,
    completed_tasks: 0,
    in_progress_tasks: 0,
    overdue_tasks: 0,
    completion_rate: 0,
    average_completion_days: 0
  };

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
                {dashboard?.user_name || 'ユーザー'}さんの生産性指標
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                syncTasksMutation.mutate(undefined, {
                  onSuccess: (data) => {
                    toast({
                      title: "同期完了",
                      description: `タスクを同期しました。新規: ${data.created || 0}件、更新: ${data.updated || 0}件`,
                    });
                  },
                  onError: (error) => {
                    toast({
                      title: "同期エラー",
                      description: error instanceof Error ? error.message : "タスクの同期に失敗しました。",
                      variant: "destructive",
                    });
                  }
                });
              }}
              disabled={syncTasksMutation.isPending}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${syncTasksMutation.isPending ? 'animate-spin' : ''}`} />
              {syncTasksMutation.isPending ? '同期中...' : 'タスクを同期'}
            </Button>
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
                    <MetricLabel metric="completionRate" className="text-sm font-medium">
                      完了率
                    </MetricLabel>
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
                {(dashboard.recent_completed_tasks || []).length > 0 ? (
                  <div className="space-y-3">
                    {(dashboard.recent_completed_tasks || []).map((task) => (
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
                  <div className="text-center py-8">
                    <p className="text-sm text-muted-foreground mb-4">
                      最近完了したタスクはありません
                    </p>
                    {statistics.total_tasks === 0 && (
                      <p className="text-xs text-muted-foreground">
                        「タスクを同期」ボタンをクリックして、Backlogから最新のタスクデータを取得してください
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 詳細分析セクション */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* ワークフロー分析 */}
            {dashboard.workflow_analysis && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Workflow className="h-5 w-5" />
                    <MetricLabel metric="workflowAnalysis">
                      ワークフロー分析
                    </MetricLabel>
                  </CardTitle>
                  <CardDescription>
                    各ステータスでの平均滞留時間（日数）
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(dashboard.workflow_analysis || []).map((item) => (
                      <div key={item.status} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium">
                            {item.status_name || getTaskStatusLabel(item.status)}
                          </span>
                          <span className="text-muted-foreground">
                            平均 {item.average_days} 日
                          </span>
                        </div>
                        <Progress 
                          value={Math.min((item.average_days / 10) * 100, 100)} 
                          className="h-2"
                        />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 平均処理時間とスキルマトリックス */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  パフォーマンス詳細
                </CardTitle>
                <CardDescription>
                  あなたの効率性指標
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 平均処理時間 */}
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <MetricLabel metric="averageCompletionTime" className="text-sm font-medium">
                      平均処理時間
                    </MetricLabel>
                    <span className="text-2xl font-bold">
                      {statistics.average_completion_days} 日
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    タスク完了までの平均日数
                  </p>
                </div>

                {/* スキルマトリックス */}
                {dashboard.skill_matrix && dashboard.skill_matrix.length > 0 && (
                  <div className="space-y-2">
                    <MetricLabel metric="taskTypeEfficiency" className="text-sm font-medium">
                      タスクタイプ別効率
                    </MetricLabel>
                    {dashboard.skill_matrix.map((skill) => (
                      <div key={skill.task_type} className="flex items-center justify-between text-sm">
                        <span>
                          {skill.task_type === 'FEATURE' ? '機能開発' :
                           skill.task_type === 'BUG' ? 'バグ修正' :
                           skill.task_type === 'IMPROVEMENT' ? '改善' :
                           skill.task_type === 'REFACTORING' ? 'リファクタリング' :
                           skill.task_type}
                        </span>
                        <span className="text-muted-foreground">
                          平均 {skill.average_completion_days || 0} 日 ({skill.total_count}件)
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 生産性トレンドチャート */}
          {dashboard.productivity_trend && dashboard.productivity_trend.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  <MetricLabel metric="productivityTrend">
                    生産性トレンド
                  </MetricLabel>
                </CardTitle>
                <CardDescription>
                  過去30日間の完了タスク数推移
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ThroughputChart
                  data={dashboard.productivity_trend.map(item => ({
                    date: item.date,
                    completed_tasks: item.completed_count,
                    story_points: 0 // 個人ダッシュボードではストーリーポイントは表示しない
                  }))}
                />
              </CardContent>
            </Card>
          )}

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
