/**
 * @fileoverview 分析データ取得のReact Queryフック
 *
 * プロジェクトと個人の分析データをReact Queryで管理するカスタムフック集です。
 * 健全性スコア、ボトルネック、ベロシティ、サイクルタイム、個人ダッシュボードデータの取得を提供します。
 *
 * @module useAnalyticsQueries
 */

import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { analyticsService } from '@/services/analytics.service'

/**
 * プロジェクトの健全性情報を取得するフック
 *
 * プロジェクトの全体的な健全性スコアと関連メトリクスをReact Queryで取得します。
 *
 * @param {number} projectId - 取得対象のプロジェクトID
 * @param {boolean} [enabled=true] - クエリを有効にするかどうか
 * @returns {UseQueryResult<ProjectHealth>} React Queryの結果オブジェクト
 *
 * @example
 * ```tsx
 * function ProjectHealthCard({ projectId }) {
 *   const { data, isLoading } = useProjectHealth(projectId);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <Card>
 *       <h3>健全性スコア: {data.health_score}%</h3>
 *       <p>完了率: {data.completion_rate}%</p>
 *       <p>期限切れ: {data.overdue_tasks}件</p>
 *     </Card>
 *   );
 * }
 * ```
 *
 * @remarks
 * - staleTime: 5分（データの鮮度保証期間）
 * - projectIdが未指定（falsy）の場合はクエリが無効化されます
 *
 * @see {@link analyticsService.getProjectHealth} - 健全性情報取得API
 */
export const useProjectHealth = (projectId: number, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'health', projectId],
    queryFn: () => analyticsService.getProjectHealth(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * プロジェクトのボトルネックを取得するフック
 */
export const useProjectBottlenecks = (projectId: number, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'bottlenecks', projectId],
    queryFn: () => analyticsService.getProjectBottlenecks(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * プロジェクトのベロシティを取得するフック
 */
export const useProjectVelocity = (projectId: number, periodDays = 30, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'velocity', projectId, periodDays],
    queryFn: () => analyticsService.getProjectVelocity(projectId, periodDays),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * プロジェクトのサイクルタイムを取得するフック
 */
export const useProjectCycleTime = (projectId: number, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'cycle-time', projectId],
    queryFn: () => analyticsService.getProjectCycleTime(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * 個人ダッシュボード情報を取得するフック
 *
 * ログイン中のユーザーの包括的な生産性メトリクスをReact Queryで取得します。
 * KPIサマリー、ワークフロー分析、生産性トレンド、スキルマトリックスなどを含みます。
 *
 * @returns {UseQueryResult<PersonalDashboard>} React Queryの結果オブジェクト
 *
 * @example
 * ```tsx
 * function PersonalDashboard() {
 *   const { data: dashboard, isLoading, error } = usePersonalDashboard();
 *
 *   if (isLoading) return <LoadingSpinner />;
 *   if (error) return <ErrorAlert error={error} />;
 *
 *   return (
 *     <div>
 *       <KPISummary data={dashboard.kpi_summary} />
 *       <ProductivityChart data={dashboard.productivity_trend} />
 *       <WorkflowAnalysis data={dashboard.workflow_analysis} />
 *     </div>
 *   );
 * }
 * ```
 *
 * @remarks
 * - staleTime: 5分（データの鮮度保証期間）
 * - 認証必須（未認証の場合は401エラー）
 * - ログイン中のユーザー自身のデータのみ取得可能
 *
 * @see {@link analyticsService.getPersonalDashboard} - 個人ダッシュボードデータ取得API
 * @see {@link PersonalDashboard} - レスポンスの型定義
 */
export const usePersonalDashboard = () => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'personal-dashboard'],
    queryFn: () => analyticsService.getPersonalDashboard(),
    staleTime: 5 * 60 * 1000, // 5分
  })
}