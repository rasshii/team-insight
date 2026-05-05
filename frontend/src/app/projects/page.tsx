/**
 * @fileoverview プロジェクト一覧ページ
 *
 * プロジェクトの基本情報（名前、キー、ステータス、説明）を表形式で表示します。
 * Phase 6 で Backlog 同期機能を削除済み。Phase 3 でローカル CRUD を実装予定。
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
import { useProjects } from "@/hooks/queries/useProjects";
import { AlertCircle, Database } from "lucide-react";
import { useRouter } from "next/navigation";

export default function ProjectsPage() {
  const router = useRouter();
  const { data: projectsData, isLoading, error } = useProjects();

  const navigateToProject = (projectId: number) => {
    router.push(`/dashboard/project/${projectId}`);
  };

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
          <h1 className="text-3xl font-bold tracking-tight">プロジェクト一覧</h1>

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
                        <TableCell className="font-medium">{project.name}</TableCell>
                        <TableCell>
                          <code className="px-2 py-1 bg-muted rounded text-sm">
                            {project.project_key}
                          </code>
                        </TableCell>
                        <TableCell>
                          <Badge variant={project.status === "active" ? "default" : "secondary"}>
                            {project.status === "active" ? "アクティブ" : "アーカイブ"}
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
                  <h3 className="mt-4 text-lg font-medium">プロジェクトがありません</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    プロジェクト作成機能は Phase 3 で実装予定です。
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </Layout>
    </PrivateRoute>
  );
}
