'use client'

import { useState } from 'react'
import { BarChart3, Users, TrendingUp, Activity, CheckCircle2, Clock, AlertCircle, Settings } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useTeams, useTeam } from '@/hooks/queries/useTeams'
import { TeamProductivityChart } from '@/components/teams/TeamProductivityChart'
import { TeamMemberPerformance } from '@/components/teams/TeamMemberPerformance'
import { TaskDistributionChart } from '@/components/teams/TaskDistributionChart'
import { TeamActivityTimeline } from '@/components/teams/TeamActivityTimeline'
import { Layout } from '@/components/Layout'
import { usePermissions } from '@/hooks/usePermissions'
import Link from 'next/link'

export default function TeamsProductivityPage() {
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const permissions = usePermissions()
  
  const { data: teamsData, isLoading: teamsLoading } = useTeams({ with_stats: true })
  const { data: teamDetail, isLoading: teamLoading } = useTeam(selectedTeamId || 0)

  const handleTeamChange = (value: string) => {
    setSelectedTeamId(parseInt(value))
  }

  // 全体統計の計算
  const totalStats = teamsData ? {
    totalTeams: teamsData.total,
    totalMembers: teamsData.teams.reduce((sum, team: any) => sum + (team.member_count || 0), 0),
    totalActiveTasks: teamsData.teams.reduce((sum, team: any) => sum + (team.active_tasks_count || 0), 0),
    totalCompletedThisMonth: teamsData.teams.reduce((sum, team: any) => sum + (team.completed_tasks_this_month || 0), 0),
  } : null

  if (teamsLoading) {
    return (
      <Layout>
        <div className="container mx-auto py-6 space-y-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid gap-4 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <BarChart3 className="h-8 w-8" />
              チーム生産性ダッシュボード
            </h1>
            <p className="text-muted-foreground mt-1">
              チームごとの生産性とパフォーマンスを分析します
            </p>
          </div>
        
          <div className="flex items-center gap-4">
            {/* チーム選択 */}
            <Select value={selectedTeamId?.toString() || ''} onValueChange={handleTeamChange}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="チームを選択してください" />
              </SelectTrigger>
              <SelectContent>
                {teamsData?.teams.map((team) => (
                  <SelectItem key={team.id} value={team.id.toString()}>
                    {team.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {/* 管理者向けボタン */}
            {(permissions.isAdmin() || permissions.isProjectLeader()) && (
              <Link href="/admin/teams">
                <Badge variant="outline" className="cursor-pointer hover:bg-accent">
                  <Settings className="mr-1 h-3 w-3" />
                  チーム管理
                </Badge>
              </Link>
            )}
          </div>
        </div>

      {/* 全体統計 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">総チーム数</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStats?.totalTeams || 0}</div>
            <p className="text-xs text-muted-foreground">
              {totalStats?.totalMembers || 0} 名のメンバー
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">アクティブタスク</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStats?.totalActiveTasks || 0}</div>
            <p className="text-xs text-muted-foreground">
              全チーム合計
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今月の完了タスク</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStats?.totalCompletedThisMonth || 0}</div>
            <p className="text-xs text-muted-foreground">
              全チーム合計
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均生産性</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalStats && totalStats.totalTeams > 0
                ? Math.round(totalStats.totalCompletedThisMonth / totalStats.totalTeams)
                : 0}
            </div>
            <p className="text-xs text-muted-foreground">
              タスク/チーム/月
            </p>
          </CardContent>
        </Card>
      </div>

      {/* チーム詳細 */}
      {selectedTeamId && teamDetail ? (
        <div className="space-y-6">
          {/* チーム概要 */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>{teamDetail.name}</CardTitle>
                  <CardDescription>{teamDetail.description || 'チームの説明なし'}</CardDescription>
                </div>
                <Badge variant="outline" className="gap-1">
                  <Users className="h-3 w-3" />
                  {teamDetail.member_count} メンバー
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <p className="text-sm font-medium">アクティブタスク</p>
                  <div className="flex items-center gap-2">
                    <Progress value={30} className="flex-1" />
                    <span className="text-sm font-bold">{teamDetail.active_tasks_count}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">今月の完了タスク</p>
                  <div className="flex items-center gap-2">
                    <Progress value={70} className="flex-1" />
                    <span className="text-sm font-bold">{teamDetail.completed_tasks_this_month}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">効率性スコア</p>
                  <div className="flex items-center gap-2">
                    <Progress value={85} className="flex-1" />
                    <span className="text-sm font-bold">85%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 詳細分析タブ */}
          <Tabs defaultValue="members" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="members">メンバー別パフォーマンス</TabsTrigger>
              <TabsTrigger value="distribution">タスク分配</TabsTrigger>
              <TabsTrigger value="productivity">生産性推移</TabsTrigger>
              <TabsTrigger value="timeline">アクティビティ</TabsTrigger>
            </TabsList>

            <TabsContent value="members" className="space-y-4">
              <TeamMemberPerformance teamId={selectedTeamId} members={teamDetail.members} />
            </TabsContent>

            <TabsContent value="distribution" className="space-y-4">
              <TaskDistributionChart teamId={selectedTeamId} />
            </TabsContent>

            <TabsContent value="productivity" className="space-y-4">
              <TeamProductivityChart teamId={selectedTeamId} />
            </TabsContent>

            <TabsContent value="timeline" className="space-y-4">
              <TeamActivityTimeline teamId={selectedTeamId} />
            </TabsContent>
          </Tabs>
        </div>
      ) : (
        <Card className="p-12">
          <div className="text-center space-y-4">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <h3 className="text-lg font-semibold">チームを選択してください</h3>
              <p className="text-muted-foreground">
                上のドロップダウンからチームを選択すると、詳細な分析が表示されます
              </p>
            </div>
          </div>
        </Card>
      )}
      </div>
    </Layout>
  )
}