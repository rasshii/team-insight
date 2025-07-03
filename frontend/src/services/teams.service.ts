/**
 * チーム管理APIサービス
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
} from '@/types/team'

export const teamsService = {
  /**
   * チーム一覧を取得
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
   */
  async getTeamMembersPerformance(teamId: number): Promise<any[]> {
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
   */
  async getTeamProductivityTrend(
    teamId: number,
    period: 'daily' | 'weekly' | 'monthly' = 'monthly'
  ): Promise<any[]> {
    return await apiClient.get(`/api/v1/teams/${teamId}/productivity-trend`, {
      params: { period }
    })
  },

  /**
   * チームの最近のアクティビティを取得
   */
  async getTeamActivities(teamId: number, limit: number = 20): Promise<any[]> {
    return await apiClient.get(`/api/v1/teams/${teamId}/activities`, {
      params: { limit }
    })
  },
}