/**
 * @fileoverview チーム管理APIサービス
 *
 * チームの作成、更新、削除、メンバー管理、パフォーマンスデータ取得など、
 * チーム関連の全機能へのAPIアクセスを提供します。
 *
 * @module teamsService
 */

import { apiClient } from '@/lib/api-client'
import {
  Team,
  TeamWithStats,
  TeamListResponse,
  TeamCreateResponse,
  TeamUpdateResponse,
  TeamDeleteResponse,
  TeamMemberAddResponse,
  TeamMemberRemoveResponse,
  TeamCreateInput,
  TeamUpdateInput,
  TeamMemberCreateInput,
  TeamMemberUpdateInput,
  TeamMember,
  TeamMemberPerformance,
  TeamProductivityDataPoint,
  TeamActivity,
} from '@/types/team'

/**
 * チーム管理APIサービス
 *
 * チームのCRUD操作、メンバー管理、パフォーマンス分析データの取得を提供します。
 *
 * ## 主要機能
 * - チーム一覧・詳細取得
 * - チーム作成・更新・削除
 * - メンバー追加・削除・役割更新
 * - チームパフォーマンスデータ取得
 * - タスク分配データ取得
 * - 生産性推移データ取得
 * - アクティビティタイムライン取得
 *
 * @see {@link apiClient} - 全APIリクエストで使用する共通クライアント
 */
export const teamsService = {
  /**
   * チーム一覧を取得
   *
   * ユーザーがアクセス可能な全チームの一覧を取得します。
   * オプションで統計情報を含めることができます。
   *
   * @param {Object} [params] - クエリパラメータ
   * @param {number} [params.page] - ページ番号（1から開始）
   * @param {number} [params.page_size] - 1ページあたりの件数
   * @param {boolean} [params.with_stats] - 統計情報（メンバー数、アクティブタスク数など）を含めるか
   * @returns {Promise<TeamListResponse>} チーム一覧と総数
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * // 統計情報付きで全チームを取得
   * const { teams, total } = await teamsService.getTeams({ with_stats: true });
   * teams.forEach(team => {
   *   console.log(`${team.name}: ${team.member_count}名`);
   * });
   * ```
   */
  async getTeams(params?: {
    page?: number
    page_size?: number
    with_stats?: boolean
  }): Promise<TeamListResponse> {
    return await apiClient.get('/api/v1/teams/', { params })
  },

  /**
   * チーム詳細を取得
   */
  async getTeam(teamId: number): Promise<TeamWithStats> {
    return await apiClient.get(`/api/v1/teams/${teamId}`)
  },

  /**
   * チームを作成
   */
  async createTeam(data: TeamCreateInput): Promise<TeamCreateResponse> {
    return await apiClient.post('/api/v1/teams/', data)
  },

  /**
   * チームを更新
   */
  async updateTeam(
    teamId: number,
    data: TeamUpdateInput
  ): Promise<TeamUpdateResponse> {
    return await apiClient.put(`/api/v1/teams/${teamId}`, data)
  },

  /**
   * チームを削除
   */
  async deleteTeam(teamId: number): Promise<TeamDeleteResponse> {
    return await apiClient.delete(`/api/v1/teams/${teamId}`)
  },

  /**
   * チームメンバー一覧を取得
   */
  async getTeamMembers(teamId: number): Promise<TeamMember[]> {
    return await apiClient.get(`/api/v1/teams/${teamId}/members`)
  },

  /**
   * チームにメンバーを追加
   */
  async addTeamMember(
    teamId: number,
    data: TeamMemberCreateInput
  ): Promise<TeamMemberAddResponse> {
    return await apiClient.post(`/api/v1/teams/${teamId}/members`, data)
  },

  /**
   * チームメンバーの役割を更新
   */
  async updateTeamMember(
    teamId: number,
    userId: number,
    data: TeamMemberUpdateInput
  ): Promise<TeamMember> {
    return await apiClient.put(
      `/api/v1/teams/${teamId}/members/${userId}`,
      data
    )
  },

  /**
   * チームからメンバーを削除
   */
  async removeTeamMember(
    teamId: number,
    userId: number
  ): Promise<TeamMemberRemoveResponse> {
    return await apiClient.delete(`/api/v1/teams/${teamId}/members/${userId}`)
  },

  /**
   * チームメンバーのパフォーマンスデータを取得
   *
   * 各メンバーの完了タスク数、平均完了時間、効率スコアなどを取得します。
   *
   * @param {number} teamId - チームID
   * @returns {Promise<TeamMemberPerformance[]>} メンバーごとのパフォーマンスデータ配列
   * @throws {AxiosError} APIリクエストが失敗した場合
   */
  async getTeamMembersPerformance(teamId: number): Promise<TeamMemberPerformance[]> {
    return await apiClient.get(`/api/v1/teams/${teamId}/members/performance`)
  },

  /**
   * チームのタスク分配データを取得
   */
  async getTeamTaskDistribution(teamId: number): Promise<{
    labels: string[]
    data: number[]
    backgroundColor: string[]
  }> {
    return await apiClient.get(`/api/v1/teams/${teamId}/task-distribution`)
  },

  /**
   * チームの生産性推移データを取得
   *
   * 指定期間での完了タスク数、総タスク数、効率性の推移を取得します。
   *
   * @param {number} teamId - チームID
   * @param {'daily' | 'weekly' | 'monthly'} [period='monthly'] - 集計期間
   * @returns {Promise<TeamProductivityDataPoint[]>} 生産性推移データポイント配列
   * @throws {AxiosError} APIリクエストが失敗した場合
   */
  async getTeamProductivityTrend(
    teamId: number,
    period: 'daily' | 'weekly' | 'monthly' = 'monthly'
  ): Promise<TeamProductivityDataPoint[]> {
    return await apiClient.get(`/api/v1/teams/${teamId}/productivity-trend`, {
      params: { period }
    })
  },

  /**
   * チームの最近のアクティビティを取得
   *
   * タスク完了、メンバー追加などのチームのアクティビティログを取得します。
   *
   * @param {number} teamId - チームID
   * @param {number} [limit=20] - 取得件数の上限
   * @returns {Promise<TeamActivity[]>} アクティビティログ配列
   * @throws {AxiosError} APIリクエストが失敗した場合
   */
  async getTeamActivities(teamId: number, limit: number = 20): Promise<TeamActivity[]> {
    return await apiClient.get(`/api/v1/teams/${teamId}/activities`, {
      params: { limit }
    })
  },
}