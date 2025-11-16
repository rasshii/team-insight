/**
 * @fileoverview チーム生産性ダッシュボードページ
 *
 * チームごとの生産性指標、メンバーパフォーマンス、タスク分配状況を可視化するページコンポーネント。
 * 複数チームの比較分析や、チーム内メンバーの詳細分析を提供します。
 *
 * @module TeamsProductivityPage
 */

'use client'

import { useState, useEffect, useMemo } from 'react'
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
import { MetricTooltip, MetricLabel } from '@/components/ui/metric-tooltip'

/**
 * チーム生産性ダッシュボードページ
 *
 * 全チームの生産性指標を一覧表示し、選択したチームの詳細分析を提供します。
 *
 * ## 主要機能
 * - 全チーム統計サマリー（総チーム数、総メンバー数、アクティブタスク数、今月の完了タスク数）
 * - チーム選択ドロップダウン
 * - 選択チームの詳細情報表示
 *   - チーム概要（メンバー数、アクティブタスク数、完了タスク数、効率性スコア）
 *   - メンバー別パフォーマンス分析
 *   - タスク分配チャート
 *   - 生産性推移グラフ
 *   - アクティビティタイムライン
 * - 管理者向けチーム管理ページへのリンク
 *
 * ## データフェッチ戦略
 * - チーム一覧: `with_stats=true`で統計情報を含めて取得
 * - チーム詳細: 選択時に個別に取得
 * - staleTime: デフォルト設定（React Query）
 *
 * ## 権限
 * - 認証必須
 * - 全ユーザーが閲覧可能
 * - チーム管理機能は管理者またはプロジェクトリーダーのみアクセス可能
 *
 * @example
 * ```tsx
 * // App Routerでの使用
 * // app/teams/page.tsx
 * export default TeamsProductivityPage
 * ```
 *
 * @returns {JSX.Element} チーム生産性ダッシュボードページのUIコンポーネント
 *
 * @remarks
 * - チームが存在しない場合、チーム作成を促すメッセージを表示します
 * - チームを選択するまでは全体統計のみ表示されます
 * - 選択したチームの詳細は、タブで切り替えて表示します
 *
 * @see {@link useTeams} - チーム一覧取得フック
 * @see {@link useTeam} - チーム詳細取得フック
 * @see {@link usePermissions} - 権限チェックフック
 * @see {@link TeamMemberPerformance} - メンバーパフォーマンスコンポーネント
 * @see {@link TeamProductivityChart} - 生産性推移チャートコンポーネント
 */
export default function TeamsProductivityPage() {
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)
  const permissions = usePermissions()
  
  const { data: teamsData, isLoading: teamsLoading } = useTeams({ with_stats: true })
  const { data: teamDetail, isLoading: teamLoading } = useTeam(selectedTeamId || 0)

  /**
   * チーム選択変更ハンドラー
   *
   * ドロップダウンで選択したチームIDを状態に保存します。
   *
   * @param {string} value - 選択されたチームのID（文字列）
   */
  const handleTeamChange = (value: string) => {
    setSelectedTeamId(parseInt(value))
  }

  /**
   * 全体統計の計算
   *
   * 全チームのデータから、総チーム数、総メンバー数、
   * アクティブタスク数、完了タスク数を集計します。
   *
   * @returns {Object} 全体統計オブジェクト
   */
  const totalStats = useMemo(() => {
    if (!teamsData || !teamsData.teams || teamsData.teams.length === 0) {
      return {
        totalTeams: 0,
        totalMembers: 0,
        totalActiveTasks: 0,
        totalCompletedThisMonth: 0,
      }
    }
    
    return {
      totalTeams: teamsData.total || 0,
      totalMembers: teamsData.teams.reduce((sum, team: any) => sum + (team.member_count || 0), 0),
      totalActiveTasks: teamsData.teams.reduce((sum, team: any) => sum + (team.active_tasks_count || 0), 0),
      totalCompletedThisMonth: teamsData.teams.reduce((sum, team: any) => sum + (team.completed_tasks_this_month || 0), 0),
    }
  }, [teamsData])

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
                {teamsData?.teams && teamsData.teams.length > 0 ? (
                  teamsData.teams.map((team) => (
                    <SelectItem key={team.id} value={team.id.toString()}>
                      {team.name}
                    </SelectItem>
                  ))
                ) : (
                  <div className="p-2 text-sm text-muted-foreground">
                    チームがありません
                  </div>
                )}
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
            <MetricLabel metric="activeTasks" className="text-sm font-medium">
              アクティブタスク
            </MetricLabel>
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
            <MetricLabel metric="teamProductivity" className="text-sm font-medium">
              平均生産性
            </MetricLabel>
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

      {/* チームがない場合のメッセージ */}
      {teamsData && teamsData.teams.length === 0 && (
        <Card className="p-12">
          <div className="text-center space-y-4">
            <Users className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <h3 className="text-lg font-semibold">チームがまだ作成されていません</h3>
              <p className="text-muted-foreground">
                {permissions.isAdmin() || permissions.isProjectLeader() ? (
                  <>チーム管理画面から新しいチームを作成してください</>
                ) : (
                  <>管理者にチームの作成を依頼してください</>
                )}
              </p>
            </div>
            {(permissions.isAdmin() || permissions.isProjectLeader()) && (
              <Link href="/admin/teams">
                <Badge variant="default" className="cursor-pointer">
                  <Settings className="mr-1 h-3 w-3" />
                  チームを作成
                </Badge>
              </Link>
            )}
          </div>
        </Card>
      )}

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
                  <MetricLabel metric="activeTasks" className="text-sm font-medium">
                    アクティブタスク
                  </MetricLabel>
                  <div className="flex items-center gap-2">
                    <Progress value={teamDetail.active_tasks_count ? (teamDetail.active_tasks_count / (teamDetail.active_tasks_count + teamDetail.completed_tasks_this_month) * 100) : 0} className="flex-1" />
                    <span className="text-sm font-bold">{teamDetail.active_tasks_count}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">今月の完了タスク</p>
                  <div className="flex items-center gap-2">
                    <Progress value={teamDetail.completed_tasks_this_month ? (teamDetail.completed_tasks_this_month / (teamDetail.active_tasks_count + teamDetail.completed_tasks_this_month) * 100) : 0} className="flex-1" />
                    <span className="text-sm font-bold">{teamDetail.completed_tasks_this_month}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <MetricLabel 
                    metric="efficiencyScore" 
                    className="text-sm font-medium"
                  >
                    効率性スコア
                  </MetricLabel>
                  <div className="flex items-center gap-2">
                    <Progress value={teamDetail.efficiency_score || 0} className="flex-1" />
                    <span className="text-sm font-bold">{teamDetail.efficiency_score || 0}%</span>
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
              <div className="flex items-center justify-between mb-4">
                <MetricLabel 
                  metric="memberPerformance"
                  className="text-lg font-medium"
                >
                  メンバー別パフォーマンス分析
                </MetricLabel>
              </div>
              <TeamMemberPerformance teamId={selectedTeamId} members={teamDetail.members} />
            </TabsContent>

            <TabsContent value="distribution" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <MetricLabel 
                  metric="taskDistribution"
                  className="text-lg font-medium"
                >
                  タスク分配分析
                </MetricLabel>
              </div>
              <TaskDistributionChart teamId={selectedTeamId} />
            </TabsContent>

            <TabsContent value="productivity" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <MetricLabel 
                  metric="productivityTrend"
                  className="text-lg font-medium"
                >
                  生産性推移分析
                </MetricLabel>
              </div>
              <TeamProductivityChart teamId={selectedTeamId} />
            </TabsContent>

            <TabsContent value="timeline" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <MetricLabel 
                  metric="activityTimeline"
                  className="text-lg font-medium"
                >
                  アクティビティタイムライン
                </MetricLabel>
              </div>
              <TeamActivityTimeline teamId={selectedTeamId} />
            </TabsContent>
          </Tabs>
        </div>
      ) : teamsData && teamsData.teams.length > 0 ? (
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
      ) : null}
      </div>
    </Layout>
  )
}