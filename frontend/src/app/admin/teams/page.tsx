'use client'

import { useState } from 'react'
import { Plus, Users, Activity, CheckCircle2, ArrowLeft, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useTeams } from '@/hooks/queries/useTeams'
import { TeamCreateDialog } from '@/components/admin/TeamCreateDialog'
import { TeamListTable } from '@/components/admin/TeamListTable'
import Link from 'next/link'

export default function TeamsPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 20

  const { data, isLoading, error, refetch, isRefetching } = useTeams({
    page: currentPage,
    page_size: pageSize,
    with_stats: true,
  })

  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              チーム情報の取得に失敗しました
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">チーム管理</h1>
          <p className="text-muted-foreground">
            Team Insight内のチームを管理します
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => refetch()}
            disabled={isLoading || isRefetching}
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
          </Button>
          <Link href="/admin/users">
            <Button variant="outline" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              ユーザー管理へ
            </Button>
          </Link>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新規チーム作成
          </Button>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">総チーム数</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-16" /> : data?.total || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              アクティブタスク総数
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                data?.teams.reduce(
                  (sum, team) => sum + (team as any).active_tasks_count || 0,
                  0
                ) || 0
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              今月の完了タスク
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                data?.teams.reduce(
                  (sum, team) =>
                    sum + (team as any).completed_tasks_this_month || 0,
                  0
                ) || 0
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* チーム一覧テーブル */}
      <Card>
        <CardHeader>
          <CardTitle>チーム一覧</CardTitle>
          <CardDescription>
            登録されているチームとその統計情報を表示します
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : (
            <TeamListTable
              teams={data?.teams || []}
              total={data?.total || 0}
              page={currentPage}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
            />
          )}
        </CardContent>
      </Card>

      {/* チーム作成ダイアログ */}
      <TeamCreateDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />
    </div>
  )
}