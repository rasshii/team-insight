/**
 * @fileoverview 分析・アナリティクスサービス
 *
 * プロジェクトの健全性、ボトルネック、ベロシティ、サイクルタイム、個人ダッシュボードなど、
 * データ分析に関連するAPIエンドポイントへのアクセスを提供します。
 *
 * @module analyticsService
 */

import { apiClient } from '@/lib/api-client'

/**
 * プロジェクト健全性の型定義
 *
 * プロジェクトの全体的な健全性スコアと関連メトリクスを表します。
 */
export interface ProjectHealth {
  project_id: number;
  project_name: string;
  health_score: number;
  total_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  overdue_tasks: number;
  overdue_rate: number;
  status_distribution: {
    [key: string]: number;
  };
}

export interface Bottleneck {
  type: "stalled_tasks" | "task_concentration" | "overdue_tasks";
  severity: "high" | "medium" | "low";
  status?: string;
  assignee?: string;
  count?: number;
  task_count?: number;
  overdue_count?: number;
  avg_days_stalled?: number;
  avg_task_count?: number;
}

export interface VelocityData {
  date: string;
  completed_count: number;
}

export interface CycleTimeData {
  project_id: number;
  project_name: string;
  cycle_times: {
    [status: string]: number;
  };
  unit: string;
}

export interface PersonalDashboard {
  user_id: number;
  user_name: string;
  kpi_summary: {
    total_tasks: number;
    completed_tasks: number;
    in_progress_tasks: number;
    overdue_tasks: number;
    completion_rate: number;
    average_completion_days: number;
  };
  workflow_analysis: Array<{
    status: string;
    average_days: number;
  }>;
  productivity_trend: Array<{
    date: string;
    completed_count: number;
  }>;
  skill_matrix: Array<{
    task_type: string;
    total_count: number;
    average_completion_days: number | null;
  }>;
  recent_completed_tasks: Array<{
    id: number;
    title: string;
    project_name: string | null;
    completed_date: string | null;
  }>;
}

/**
 * 分析関連のAPIサービス
 *
 * プロジェクトと個人の生産性メトリクス、ボトルネック分析、トレンドデータを提供します。
 * React Queryと組み合わせて使用することで、効率的なデータフェッチとキャッシング戦略を実現します。
 *
 * ## 提供する分析機能
 * - プロジェクト健全性スコア
 * - ワークフローボトルネック検出
 * - チームベロシティ測定
 * - サイクルタイム分析
 * - 個人ダッシュボード指標
 *
 * @see {@link apiClient} - 全APIリクエストで使用する共通クライアント
 */
export const analyticsService = {
  /**
   * プロジェクトの健全性情報を取得
   *
   * プロジェクトの全体的な健全性スコアと関連メトリクスを取得します。
   * 健全性スコアは、完了率、期限切れ率、タスク分布などから算出されます。
   *
   * @param {number} projectId - 取得対象のプロジェクトID
   * @returns {Promise<ProjectHealth>} プロジェクト健全性情報
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * const health = await analyticsService.getProjectHealth(123);
   * console.log(`健全性スコア: ${health.health_score}%`);
   * console.log(`完了率: ${health.completion_rate}%`);
   * console.log(`期限切れタスク: ${health.overdue_tasks}件`);
   * ```
   *
   * @remarks
   * 健全性スコアは0-100の範囲で表され、高いほど健全な状態を示します。
   * React QueryでstaleTime: 5分を推奨します。
   */
  async getProjectHealth(projectId: number): Promise<ProjectHealth> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/health/`)
  },

  /**
   * プロジェクトのボトルネックを取得
   *
   * プロジェクト内のワークフローボトルネックを自動検出します。
   * 停滞しているタスク、タスクが集中しているメンバー、期限切れタスクなどを識別します。
   *
   * @param {number} projectId - 分析対象のプロジェクトID
   * @returns {Promise<Bottleneck[]>} ボトルネック情報の配列（重要度順）
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * const bottlenecks = await analyticsService.getProjectBottlenecks(123);
   * bottlenecks.forEach(bn => {
   *   console.log(`[${bn.severity}] ${bn.type}: ${bn.count}件`);
   * });
   * ```
   *
   * @remarks
   * - ボトルネックの種類: stalled_tasks（停滞タスク）、task_concentration（タスク集中）、overdue_tasks（期限切れ）
   * - 重要度: high（高）、medium（中）、low（低）
   * - React QueryでstaleTime: 5分を推奨します
   */
  async getProjectBottlenecks(projectId: number): Promise<Bottleneck[]> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/bottlenecks/`)
  },

  /**
   * プロジェクトのベロシティを取得
   *
   * 指定期間内のタスク完了数の推移を日ごとに取得します。
   * チームの生産性トレンドや作業ペースの変化を把握するために使用します。
   *
   * @param {number} projectId - 分析対象のプロジェクトID
   * @param {number} [periodDays=30] - 取得期間（日数）。デフォルトは30日
   * @returns {Promise<VelocityData[]>} 日ごとの完了タスク数データ
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * // 過去30日間のベロシティを取得
   * const velocity = await analyticsService.getProjectVelocity(123);
   *
   * // 過去7日間のベロシティを取得
   * const weeklyVelocity = await analyticsService.getProjectVelocity(123, 7);
   *
   * // チャート表示
   * <VelocityChart data={velocity} />
   * ```
   *
   * @remarks
   * ベロシティデータは日付昇順でソートされています。
   * React QueryでstaleTime: 5分を推奨します。
   */
  async getProjectVelocity(projectId: number, periodDays: number = 30): Promise<VelocityData[]> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/velocity/`, {
      params: { period_days: periodDays }
    })
  },

  /**
   * プロジェクトのサイクルタイムを取得
   *
   * 各ワークフローステータスでのタスクの平均滞留時間を取得します。
   * どのステータスでタスクが滞留しやすいかを把握し、プロセス改善に役立てます。
   *
   * @param {number} projectId - 分析対象のプロジェクトID
   * @returns {Promise<CycleTimeData>} ステータスごとのサイクルタイム情報
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * const cycleTime = await analyticsService.getProjectCycleTime(123);
   * console.log(`プロジェクト: ${cycleTime.project_name}`);
   * Object.entries(cycleTime.cycle_times).forEach(([status, days]) => {
   *   console.log(`${status}: 平均${days}日`);
   * });
   * ```
   *
   * @remarks
   * - サイクルタイムの単位はプロジェクト設定により異なります（通常は日数）
   * - React QueryでstaleTime: 5分を推奨します
   */
  async getProjectCycleTime(projectId: number): Promise<CycleTimeData> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/cycle-time/`)
  },

  /**
   * 個人ダッシュボード情報を取得
   *
   * ログイン中のユーザーの包括的な生産性メトリクスを取得します。
   * KPIサマリー、ワークフロー分析、生産性トレンド、スキルマトリックス、
   * 最近完了したタスクなど、個人パフォーマンスの全体像を提供します。
   *
   * @returns {Promise<PersonalDashboard>} 個人ダッシュボードデータ
   * @throws {AxiosError} APIリクエストが失敗した場合、または未認証の場合
   *
   * @example
   * ```typescript
   * const dashboard = await analyticsService.getPersonalDashboard();
   * console.log(`完了率: ${dashboard.kpi_summary.completion_rate}%`);
   * console.log(`平均処理時間: ${dashboard.kpi_summary.average_completion_days}日`);
   *
   * // 生産性トレンドをグラフ表示
   * <ProductivityChart data={dashboard.productivity_trend} />
   * ```
   *
   * @remarks
   * - 認証必須のエンドポイントです（ログイン中のユーザーのデータのみ取得可能）
   * - React QueryでstaleTime: 5分を推奨します
   * - ワークフロー分析は最近のタスクデータに基づいて計算されます
   *
   * @see {@link PersonalDashboard} - レスポンスの詳細な型定義
   */
  async getPersonalDashboard(): Promise<PersonalDashboard> {
    return await apiClient.get('/api/v1/analytics/personal/dashboard/')
  },
}