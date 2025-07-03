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
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { 
  Activity, 
  AlertCircle, 
  CheckCircle2, 
  Clock,
  TrendingUp,
  Users,
  BarChart3,
  Zap,
  AlertTriangle,
  RefreshCw
} from "lucide-react";
import { 
  useProjectHealth,
  useProjectBottlenecks,
  useProjectVelocity,
  useProjectCycleTime
} from "@/hooks/queries/useAnalytics";
import { BottleneckChart } from "@/components/charts/BottleneckChart";
import { ThroughputChart } from "@/components/charts/ThroughputChart";
import { useRouter } from "next/navigation";
import { useProject, useSyncProjectTasks } from "@/hooks/queries/useProjects";
import { toast } from "@/components/ui/use-toast";
import { getTaskStatusLabel } from "@/lib/task-utils";
import { useProjectStatuses } from "@/hooks/queries/useBacklog";
import { MetricTooltip, MetricLabel } from "@/components/ui/metric-tooltip";

interface ProjectDashboardPageProps {
  params: {
    id: string
  }
}

export default function ProjectDashboardPage({ params }: ProjectDashboardPageProps) {
  const router = useRouter();
  const projectId = Number(params.id);
  
  // データフェッチ
  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const { data: health, isLoading: healthLoading } = useProjectHealth(projectId);
  const { data: bottlenecks, isLoading: bottlenecksLoading } = useProjectBottlenecks(projectId);
  const { data: velocity, isLoading: velocityLoading } = useProjectVelocity(projectId);
  const { data: cycleTime, isLoading: cycleTimeLoading } = useProjectCycleTime(projectId);
  const { data: statusesData, isLoading: statusesLoading } = useProjectStatuses(projectId, !!project);
  
  // タスク同期ミューテーション
  const syncTasksMutation = useSyncProjectTasks();

  const isLoading = projectLoading || healthLoading || bottlenecksLoading || velocityLoading || cycleTimeLoading || statusesLoading;

  // ステータス名のマッピングを作成
  const getStatusLabel = (statusKey: string) => {
    if (statusesData?.statuses) {
      // ステータスIDで検索
      const statusById = statusesData.statuses.find(s => s.id.toString() === statusKey);
      if (statusById) return statusById.name;
      
      // ステータス名で検索（互換性のため）
      const statusByName = statusesData.statuses.find(s => 
        s.name.toLowerCase() === statusKey.toLowerCase() ||
        s.name === statusKey
      );
      if (statusByName) return statusByName.name;
    }
    
    // フォールバックとして固定マッピングを使用
    return getTaskStatusLabel(statusKey);
  };

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

  if (!project && !projectLoading) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>エラー</AlertTitle>
              <AlertDescription>
                プロジェクトID: {projectId} が見つかりません。
                プロジェクトが存在しないか、アクセス権限がありません。
              </AlertDescription>
            </Alert>
            <div className="mt-4 space-x-2">
              <Button
                variant="outline"
                onClick={() => router.push('/projects')}
              >
                プロジェクト一覧に戻る
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
              >
                再読み込み
              </Button>
            </div>
          </div>
        </Layout>
      </PrivateRoute>
    );
  }

  // 健康度スコアに基づく色とアイコンを決定
  const getHealthScoreVariant = (score: number) => {
    if (score >= 80) return { color: "text-green-600", icon: CheckCircle2, label: "健全" };
    if (score >= 60) return { color: "text-yellow-600", icon: AlertTriangle, label: "注意" };
    return { color: "text-red-600", icon: AlertCircle, label: "要改善" };
  };

  const healthScore = health?.health_score || 0;
  const healthVariant = getHealthScoreVariant(healthScore);

  return (
    <PrivateRoute>
      <Layout>
        <div className="container mx-auto p-6 space-y-6">
          {/* ヘッダー */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {project.name}
              </h1>
              <p className="text-muted-foreground mt-1">
                プロジェクトダッシュボード
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                if (!project) {
                  toast({
                    title: "エラー",
                    description: "プロジェクトが見つかりません",
                    variant: "destructive",
                  });
                  return;
                }
                syncTasksMutation.mutate(projectId);
              }}
              disabled={syncTasksMutation.isPending || !project}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${syncTasksMutation.isPending ? 'animate-spin' : ''}`} />
              {syncTasksMutation.isPending ? '同期中...' : 'タスクを同期'}
            </Button>
          </div>

          {/* 健康度とKPIカード */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* 健康度スコア */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <MetricLabel metric="healthScore" className="text-sm font-medium">
                  健康度スコア
                </MetricLabel>
                <healthVariant.icon className={`h-5 w-5 ${healthVariant.color}`} />
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <div className={`text-3xl font-bold ${healthVariant.color}`}>
                    {healthScore}
                  </div>
                  <span className="text-sm text-muted-foreground">/ 100</span>
                </div>
                <Badge variant="secondary" className="mt-2">
                  {healthVariant.label}
                </Badge>
                <Progress value={healthScore} className="mt-3 h-2" />
              </CardContent>
            </Card>

            {/* 総タスク数 */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">総タスク数</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{health?.total_tasks || 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  完了率: {health?.completion_rate?.toFixed(1) || 0}%
                </p>
                <Progress value={health?.completion_rate || 0} className="mt-2 h-2" />
              </CardContent>
            </Card>

            {/* 期限切れタスク */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">期限切れ</CardTitle>
                <AlertCircle className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {health?.overdue_tasks || 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  期限遵守率: {100 - (health?.overdue_rate || 0)}%
                </p>
              </CardContent>
            </Card>

            {/* ステータス分布 */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <MetricLabel metric="statusDistribution" className="text-sm font-medium">
                  ステータス分布
                </MetricLabel>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm">
                  {statusesData?.statuses ? (
                    // Backlog APIから取得したステータスを表示
                    statusesData.statuses
                      .sort((a, b) => a.displayOrder - b.displayOrder)
                      .map(status => {
                        const count = health?.status_distribution?.[status.id] || 
                                     health?.status_distribution?.[status.name] || 
                                     0;
                        return (
                          <div key={status.id} className="flex justify-between">
                            <span style={{ color: status.color }}>{status.name}</span>
                            <span className="font-medium">{count}</span>
                          </div>
                        );
                      })
                  ) : (
                    // フォールバック: 固定のステータスを表示
                    <>
                      <div className="flex justify-between">
                        <span>未着手</span>
                        <span className="font-medium">{health?.status_distribution?.TODO || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>進行中</span>
                        <span className="font-medium">{health?.status_distribution?.IN_PROGRESS || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>処理済み</span>
                        <span className="font-medium">{health?.status_distribution?.RESOLVED || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>完了</span>
                        <span className="font-medium">{health?.status_distribution?.CLOSED || 0}</span>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ボトルネック分析 */}
          {bottlenecks && bottlenecks.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  <MetricLabel 
                    metric="bottleneck"
                  >
                    ボトルネック分析
                  </MetricLabel>
                </CardTitle>
                <CardDescription>
                  プロジェクトの進行を妨げている要因
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[400px] overflow-y-auto">
                <BottleneckChart data={bottlenecks} />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  <MetricLabel 
                    metric="bottleneck"
                  >
                    ボトルネック分析
                  </MetricLabel>
                </CardTitle>
                <CardDescription>
                  プロジェクトの進行を妨げている要因
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[400px] flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-2" />
                  <p>ボトルネックデータがありません</p>
                  <p className="text-sm mt-1">タスクを同期してください</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ベロシティとサイクルタイム */}
          <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
            {/* ベロシティトレンド */}
            {velocity && velocity.length > 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    <MetricLabel metric="velocity">
                      ベロシティトレンド
                    </MetricLabel>
                  </CardTitle>
                  <CardDescription>
                    日別完了タスク数の推移
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  <ThroughputChart
                    data={velocity.map(item => ({
                      date: item.date,
                      completed_tasks: item.completed_count,
                      story_points: item.story_points || 0
                    }))}
                  />
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    <MetricLabel metric="velocity">
                      ベロシティトレンド
                    </MetricLabel>
                  </CardTitle>
                  <CardDescription>
                    日別完了タスク数の推移
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[300px] flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                    <p>ベロシティデータがありません</p>
                    <p className="text-sm mt-1">タスクを同期してください</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* サイクルタイム分析 */}
            {cycleTime && Object.keys(cycleTime.cycle_times || {}).length > 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    <MetricLabel metric="cycleTime">
                      サイクルタイム分析
                    </MetricLabel>
                  </CardTitle>
                  <CardDescription>
                    各ステータスでの平均滞留時間
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(cycleTime.cycle_times || {}).map(([status, days]) => (
                      <div key={status} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium">
                            {getStatusLabel(status)}
                          </span>
                          <span className="text-muted-foreground">
                            平均 {typeof days === 'number' ? days.toFixed(1) : days} 日
                          </span>
                        </div>
                        <Progress 
                          value={Math.min((Number(days) / 10) * 100, 100)} 
                          className="h-2"
                        />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    <MetricLabel metric="cycleTime">
                      サイクルタイム分析
                    </MetricLabel>
                  </CardTitle>
                  <CardDescription>
                    各ステータスでの平均滞留時間
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[300px] flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <Clock className="h-12 w-12 mx-auto mb-2" />
                    <p>サイクルタイムデータがありません</p>
                    <p className="text-sm mt-1">タスクを同期してください</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* アクションアイテム */}
          {bottlenecks && bottlenecks.some(b => b.severity === 'high') && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>緊急の対応が必要です</AlertTitle>
              <AlertDescription>
                複数の深刻なボトルネックが検出されました。早急な対応を推奨します。
              </AlertDescription>
            </Alert>
          )}

          {/* プロジェクト一覧へ戻る */}
          <div className="flex justify-start">
            <Button
              variant="ghost"
              onClick={() => router.push('/projects')}
            >
              プロジェクト一覧に戻る
            </Button>
          </div>
        </div>
      </Layout>
    </PrivateRoute>
  );
}