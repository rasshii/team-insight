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

  const isAdminOrLeader = user?.user_roles?.some(
    (role) => role.role.name === "ADMIN" || role.role.name === "PROJECT_LEADER"
  );

  // Monitor projects data changes
  useEffect(() => {
    console.log('Projects data updated:', {
      fullData: projectsData,
      projectsArray: projectsData?.projects,
      projectCount: projectsData?.projects?.length || 0,
      projectKeys: projectsData?.projects?.map((p: any) => p.project_key) || [],
      sampleProject: projectsData?.projects?.[0] || null
    });
  }, [projectsData]);

  const handleSyncProjects = () => {
    console.log('Sync button clicked');
    console.log('Connection status:', connectionStatus);
    console.log('Is admin or leader:', isAdminOrLeader);
    console.log('Mutation is pending:', syncProjectsMutation.isPending);
    
    syncProjectsMutation.mutate(undefined, {
      onSuccess: (data) => {
        console.log('Sync successful:', data);
        console.log('Projects after sync:', projectsData);
        // Force a hard refresh of the page after a short delay to bypass any caching
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      },
      onError: (error) => {
        console.error('Sync failed:', error);
      }
    });
  };

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
  
  // Debug logging
  console.log('Projects data:', projectsData);
  console.log('Projects array:', projects);
  console.log('User roles:', user?.user_roles);

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