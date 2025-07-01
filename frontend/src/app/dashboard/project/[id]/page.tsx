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
import { useProject } from "@/hooks/queries/useProjects";

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

  const isLoading = projectLoading || healthLoading || bottlenecksLoading || velocityLoading || cycleTimeLoading;

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

  if (!project) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>エラー</AlertTitle>
              <AlertDescription>
                プロジェクトが見つかりません
              </AlertDescription>
            </Alert>
            <Button
              variant="ghost"
              onClick={() => router.push('/projects')}
              className="mt-4"
            >
              プロジェクト一覧に戻る
            </Button>
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
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              データを更新
            </Button>
          </div>

          {/* 健康度とKPIカード */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* 健康度スコア */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">健康度スコア</CardTitle>
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
                <CardTitle className="text-sm font-medium">ステータス分布</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>未着手</span>
                    <span className="font-medium">{health?.status_distribution?.TODO || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>進行中</span>
                    <span className="font-medium">{health?.status_distribution?.IN_PROGRESS || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>完了</span>
                    <span className="font-medium">{health?.status_distribution?.CLOSED || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ボトルネック分析 */}
          {bottlenecks && bottlenecks.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  ボトルネック分析
                </CardTitle>
                <CardDescription>
                  プロジェクトの進行を妨げている要因
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[400px]">
                <BottleneckChart data={bottlenecks} />
              </CardContent>
            </Card>
          )}

          {/* ベロシティとサイクルタイム */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* ベロシティトレンド */}
            {velocity && velocity.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    ベロシティトレンド
                  </CardTitle>
                  <CardDescription>
                    日別完了タスク数の推移
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  <ThroughputChart
                    data={velocity.map(item => ({
                      date: item.date,
                      value: item.completed_count
                    }))}
                  />
                </CardContent>
              </Card>
            )}

            {/* サイクルタイム分析 */}
            {cycleTime && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    サイクルタイム分析
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
                            {status === 'TODO' ? '未着手' :
                             status === 'IN_PROGRESS' ? '進行中' :
                             status === 'DONE' ? '完了待ち' :
                             status === 'CLOSED' ? '完了' : status}
                          </span>
                          <span className="text-muted-foreground">
                            平均 {days} 日
                          </span>
                        </div>
                        <Progress 
                          value={Math.min((days / 10) * 100, 100)} 
                          className="h-2"
                        />
                      </div>
                    ))}
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