/**
 * @fileoverview プロジェクト一覧ページ
 *
 * Backlogプロジェクトの一覧表示と同期機能を提供するページコンポーネント。
 * プロジェクトの基本情報（名前、キー、ステータス、説明）を表形式で表示します。
 *
 * @module ProjectsPage
 */

"use client";

import { Layout } from "@/components/Layout";
import { PrivateRoute } from "@/components/PrivateRoute";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects, useSyncAllProjects } from "@/hooks/queries/useProjects";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/react-query";
import { syncService } from "@/services/sync.service";
import { useAuth } from "@/hooks/useAuth";
import { RefreshCw, AlertCircle, CheckCircle2, Database } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale/ja";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * プロジェクト一覧ページ
 *
 * ユーザーがアクセス可能なBacklogプロジェクトの一覧を表示します。
 *
 * ## 主要機能
 * - プロジェクト一覧の表形式表示
 *   - プロジェクト名
 *   - プロジェクトキー
 *   - ステータス（アクティブ/アーカイブ）
 *   - 説明
 * - Backlogプロジェクト同期機能（管理者/プロジェクトリーダーのみ）
 * - Backlog接続状態の表示
 * - プロジェクト詳細ページへの遷移
 *
 * ## データフェッチ戦略
 * - React Queryでプロジェクトデータを取得
 * - 同期状態は1分ごとに更新（staleTime: 60秒）
 * - プロジェクト同期後は強制的にページをリロード
 *
 * ## 権限
 * - 認証必須（PrivateRouteでラップ）
 * - 全ユーザーが自身がアクセス可能なプロジェクトを閲覧可能
 * - プロジェクト同期は管理者またはプロジェクトリーダーのみ実行可能
 *
 * @example
 * ```tsx
 * // App Routerでの使用
 * // app/projects/page.tsx
 * export default ProjectsPage
 * ```
 *
 * @returns {JSX.Element} プロジェクト一覧ページのUIコンポーネント
 *
 * @remarks
 * - プロジェクトが存在しない場合、Backlog同期を促すメッセージを表示します
 * - Backlog接続がない場合、連携設定ページへのリンクを表示します
 * - 同期完了後、1秒後に自動的にページがリロードされます
 *
 * @see {@link useProjects} - プロジェクト一覧取得フック
 * @see {@link useSyncAllProjects} - プロジェクト同期フック
 * @see {@link syncService.getConnectionStatus} - Backlog接続状態取得サービス
 */
export default function ProjectsPage() {
  const router = useRouter();
  const { user } = useAuth();

  // React Queryフックでプロジェクトデータを取得
  const { data: projectsData, isLoading, error } = useProjects();
  
  // 同期状態を取得
  const { data: connectionStatus } = useQuery({
    queryKey: queryKeys.sync.status,
    queryFn: () => syncService.getConnectionStatus(),
    staleTime: 60 * 1000, // 1分
  });
  
  // プロジェクト同期のミューテーション
  const syncProjectsMutation = useSyncAllProjects();

  /**
   * 管理者またはプロジェクトリーダー判定
   *
   * ユーザーのロール情報から、プロジェクト同期権限を持つかどうかを判定します。
   */
  const isAdminOrLeader = user?.user_roles?.some(
    (role) => role.role.name === "ADMIN" || role.role.name === "PROJECT_LEADER"
  );

  /**
   * プロジェクト同期ハンドラー
   *
   * Backlogから全プロジェクトを同期し、
   * 完了後にページを強制リロードします。
   */
  const handleSyncProjects = () => {
    syncProjectsMutation.mutate(undefined, {
      onSuccess: (data) => {
        // Force a hard refresh of the page after a short delay to bypass any caching
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      },
    });
  };

  /**
   * プロジェクト詳細ページへの遷移
   *
   * @param {number} projectId - 遷移先のプロジェクトID
   */
  const navigateToProject = (projectId: number) => {
    router.push(`/dashboard/project/${projectId}`);
  };

  // ローディング状態
  if (isLoading) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6">
            <div className="space-y-4">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-64 w-full" />
            </div>
          </div>
        </Layout>
      </PrivateRoute>
    );
  }

  // エラー状態
  if (error) {
    return (
      <PrivateRoute>
        <Layout>
          <div className="container mx-auto p-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error instanceof Error ? error.message : "データの読み込みに失敗しました"}
              </AlertDescription>
            </Alert>
          </div>
        </Layout>
      </PrivateRoute>
    );
  }

  const projects = projectsData?.projects || [];

  return (
    <PrivateRoute>
      <Layout>
        <div className="container mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold tracking-tight">
              プロジェクト一覧
            </h1>
            {isAdminOrLeader && (
              <Button
                onClick={handleSyncProjects}
                disabled={syncProjectsMutation.isPending || !connectionStatus?.connected}
                size="sm"
                variant="outline"
              >
                {syncProjectsMutation.isPending ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    同期中...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Backlogと同期
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Backlog接続状態 */}
          {connectionStatus && (
            <Alert variant={connectionStatus.connected ? "default" : "destructive"}>
              {connectionStatus.connected ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <span>{connectionStatus.message}</span>
                  {connectionStatus.last_project_sync && (
                    <span className="text-sm text-muted-foreground">
                      最終同期: {formatDistanceToNow(
                        new Date(connectionStatus.last_project_sync),
                        { addSuffix: true, locale: ja }
                      )}
                    </span>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>プロジェクト一覧</CardTitle>
                  <CardDescription>
                    あなたが参加しているプロジェクトの一覧です
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Database className="h-4 w-4" />
                  <span>{projects.length} プロジェクト</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {projects.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>プロジェクト名</TableHead>
                      <TableHead>キー</TableHead>
                      <TableHead>ステータス</TableHead>
                      <TableHead>説明</TableHead>
                      <TableHead className="text-right">アクション</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {projects.map((project) => (
                      <TableRow key={project.id}>
                        <TableCell className="font-medium">
                          {project.name}
                        </TableCell>
                        <TableCell>
                          <code className="px-2 py-1 bg-muted rounded text-sm">
                            {project.project_key}
                          </code>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              project.status === "active"
                                ? "default"
                                : "secondary"
                            }
                          >
                            {project.status === "active"
                              ? "アクティブ"
                              : "アーカイブ"}
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {project.description || "-"}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigateToProject(project.id)}
                          >
                            詳細
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12">
                  <Database className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-4 text-lg font-medium">
                    プロジェクトがありません
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {connectionStatus?.connected
                      ? "Backlogからプロジェクトを同期してください"
                      : "Backlog連携を設定してください"}
                  </p>
                  {connectionStatus?.connected ? (
                    isAdminOrLeader && (
                      <Button
                        onClick={handleSyncProjects}
                        disabled={syncProjectsMutation.isPending}
                        className="mt-4"
                      >
                        プロジェクトを同期
                      </Button>
                    )
                  ) : (
                    <Button
                      onClick={() => router.push('/settings/backlog')}
                      className="mt-4"
                    >
                      Backlog連携を設定
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </Layout>
    </PrivateRoute>
  );
}