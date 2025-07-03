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
import { Activity, FolderOpen, TrendingUp, Users } from "lucide-react";
import Link from "next/link";
import { useProjects } from "@/hooks/queries/useProjects";
import { useTasks } from "@/hooks/queries/useTasks";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

export default function DashboardPage() {
  // React Queryフックを使用してデータを取得
  const { data: projectsData, isLoading: projectsLoading, error: projectsError } = useProjects();
  const { data: tasksData, isLoading: tasksLoading, error: tasksError } = useTasks();
  
  const loading = projectsLoading || tasksLoading;
  const error = projectsError || tasksError;
  
  // ダッシュボードデータを計算
  const data = projectsData && tasksData ? {
    stats: {
      totalProjects: projectsData.total || 0,
      totalTeams: 0, // チーム機能は未実装
      totalIssues: tasksData.total || 0,
      activeIssues: tasksData.tasks?.filter(task => task.status !== 'closed').length || 0,
    }
  } : null;

  if (loading) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6 space-y-6">
            <Skeleton className="h-9 w-48" />
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(3)].map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-4 w-48 mt-2" />
                  </CardHeader>
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

  if (!data) {
    return null;
  }

  return (
    <PrivateRoute>
      <Layout>
        <div className="container mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold tracking-tight">
              ダッシュボード
            </h1>
          </div>

          {/* クイックアクセス */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Link href="/dashboard/personal">
              <Card className="hover:bg-gray-50 transition-colors cursor-pointer">
                <CardHeader>
                  <CardTitle>個人ダッシュボード</CardTitle>
                  <CardDescription>
                    あなたの活動状況とパフォーマンスを確認
                  </CardDescription>
                </CardHeader>
              </Card>
            </Link>
            <Link href="/projects">
              <Card className="hover:bg-gray-50 transition-colors cursor-pointer">
                <CardHeader>
                  <CardTitle>プロジェクト一覧</CardTitle>
                  <CardDescription>
                    参加しているプロジェクトの一覧を表示
                  </CardDescription>
                </CardHeader>
              </Card>
            </Link>
            <Link href="/dashboard/organization">
              <Card className="hover:bg-gray-50 transition-colors cursor-pointer">
                <CardHeader>
                  <CardTitle>組織ダッシュボード</CardTitle>
                  <CardDescription>組織全体の状況と分析を確認</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          </div>

          {/* 統計カード */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  プロジェクト数
                </CardTitle>
                <FolderOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.totalProjects}
                </div>
                <p className="text-xs text-muted-foreground">
                  アクティブなプロジェクト
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">チーム数</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.totalTeams}
                </div>
                <p className="text-xs text-muted-foreground">
                  登録されているチーム
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">総課題数</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.totalIssues}
                </div>
                <p className="text-xs text-muted-foreground">すべての課題</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  アクティブな課題
                </CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.activeIssues}
                </div>
                <p className="text-xs text-muted-foreground">対応中の課題</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </Layout>
    </PrivateRoute>
  );
}
