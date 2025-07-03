/**
 * Backlog連携サービス
 */

import { apiClient } from '@/lib/api-client'

// Backlog連携関連の型定義
export interface BacklogConnectionStatus {
  is_connected: boolean
  space_key: string | null
  connection_type: 'oauth' | null
  connected_at: string | null
  last_sync_at: string | null
  expires_at: string | null
  user_email: string | null
}

export interface ConnectOAuthParams {
  space_key: string
}

export interface BacklogConnectionResponse {
  is_connected: boolean
  space_key: string
  connection_type: 'oauth'
  user_email: string
}

export interface BacklogTestResponse {
  success: boolean
  message: string
  user_info?: {
    id: number
    name: string
    email: string
  }
}

export interface BacklogDisconnectResponse {
  success: boolean
  message: string
}

export interface BacklogSyncResponse {
  synced: number
  message: string
}

export interface BacklogSpaceKeyUpdateParams {
  space_key: string
}

export interface BacklogSpaceKeyUpdateResponse {
  success: boolean
  message: string
  space_key: string
}

export interface BacklogStatus {
  id: number
  projectId: number
  name: string
  color: string
  displayOrder: number
}

export interface BacklogStatusesResponse {
  statuses: BacklogStatus[]
  cached: boolean
}

/**
 * Backlog連携関連のAPIサービス
 */
export const backlogService = {
  /**
   * Backlog接続状態を取得
   */
  async getConnection(): Promise<BacklogConnectionStatus> {
    const response = await apiClient.get('/api/v1/backlog/connection')
    return response
  },

  /**
   * OAuthでBacklogと連携
   */
  async connectWithOAuth(params?: ConnectOAuthParams): Promise<{ authorization_url: string; state: string }> {
    // バックエンドはGETエンドポイントを使用するため、クエリパラメータとして送信
    const queryParams = params?.space_key ? `?space_key=${encodeURIComponent(params.space_key)}` : ''
    const response = await apiClient.get(`/api/v1/auth/backlog/authorize${queryParams}`)
    return response.data
  },

  /**
   * Backlog連携をテスト
   */
  async testConnection(): Promise<BacklogTestResponse> {
    const response = await apiClient.post('/api/v1/backlog/test')
    return response.data
  },

  /**
   * Backlog連携を解除
   */
  async disconnect(): Promise<BacklogDisconnectResponse> {
    const response = await apiClient.post('/api/v1/backlog/disconnect')
    return response.data
  },

  /**
   * プロジェクトを同期
   */
  async syncProjects(): Promise<BacklogSyncResponse> {
    const response = await apiClient.post('/api/v1/sync/projects/all')
    return response.data
  },

  /**
   * タスクを同期
   */
  async syncTasks(projectId: string | number): Promise<BacklogSyncResponse> {
    const response = await apiClient.post(`/api/v1/sync/tasks/${projectId}`)
    return response.data
  },

  /**
   * スペースキーを更新
   */
  async updateSpaceKey(params: BacklogSpaceKeyUpdateParams): Promise<BacklogSpaceKeyUpdateResponse> {
    const response = await apiClient.put('/api/v1/backlog/connection/space-key', params)
    return response.data
  },

  /**
   * プロジェクトのステータス一覧を取得
   */
  async getProjectStatuses(projectId: string | number): Promise<BacklogStatusesResponse> {
    const response = await apiClient.get(`/api/v1/backlog/projects/${projectId}/statuses`)
    return response.data
  },

  /**
   * ユーザーのプロジェクトのステータス情報を取得
   */
  async getUserProjectStatuses(): Promise<{
    projects: Array<{
      project_id: number
      project_name: string
      backlog_project_id: number
      statuses: BacklogStatus[]
    }>
    all_statuses: BacklogStatus[]
  }> {
    const response = await apiClient.get('/api/v1/backlog/user/project-statuses')
    return response.data
  },
}