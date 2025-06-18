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
import { Activity, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { useEffect, useState } from "react";

interface PersonalDashboardData {
  stats: {
    completedTasks: number;
    inProgressTasks: number;
    pendingReviews: number;
    averageCycleTime: number;
  };
  recentActivity: Array<{
    id: number;
    type: string;
    title: string;
    timestamp: string;
  }>;
}

export default function PersonalDashboardPage() {
  const [data, setData] = useState<PersonalDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPersonalDashboardData = async () => {
      try {
        const response = await fetch("/api/dashboard/personal");
        if (!response.ok) {
          throw new Error("個人ダッシュボードデータの取得に失敗しました");
        }
        const dashboardData = await response.json();
        setData(dashboardData);
      } catch (err) {
        console.error("Error fetching personal dashboard data:", err);
        setError("データの読み込みに失敗しました");
      } finally {
        setLoading(false);
      }
    };
    fetchPersonalDashboardData();
  }, []);

  if (loading) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-8 w-48 bg-gray-200 rounded"></div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-32 bg-gray-200 rounded"></div>
                ))}
              </div>
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
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
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
              個人ダッシュボード
            </h1>
          </div>

          {/* 統計カード */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  完了タスク
                </CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.completedTasks}
                </div>
                <p className="text-xs text-muted-foreground">
                  今月の完了タスク数
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  進行中タスク
                </CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.inProgressTasks}
                </div>
                <p className="text-xs text-muted-foreground">
                  現在の進行中タスク
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  レビュー待ち
                </CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.pendingReviews}
                </div>
                <p className="text-xs text-muted-foreground">
                  レビュー待ちのタスク
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  平均サイクルタイム
                </CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.stats.averageCycleTime}日
                </div>
                <p className="text-xs text-muted-foreground">
                  タスク完了までの平均日数
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 最近のアクティビティ */}
          <Card>
            <CardHeader>
              <CardTitle>最近のアクティビティ</CardTitle>
              <CardDescription>あなたの最近の活動履歴です</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-center justify-between border-b pb-4 last:border-0"
                  >
                    <div>
                      <p className="font-medium">{activity.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {activity.type}
                      </p>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {new Date(activity.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    </PrivateRoute>
  );
}
