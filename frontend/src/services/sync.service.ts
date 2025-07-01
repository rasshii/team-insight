import { apiClient } from '@/lib/api-client'
import { ConnectionStatus, SyncStatus, SyncResult } from '@/types/sync'

/**
 * 同期サービス
 * Backlogとのデータ同期を管理
 */
export const syncService = {
  /**
   * 接続状態を取得
   */
  async getConnectionStatus(): Promise<ConnectionStatus> {
    const response = await apiClient.get('/api/v1/sync/connection/status')
    return response.data
  },

  /**
   * ユーザーのタスクを同期
   */
  async syncUserTasks(): Promise<SyncResult> {
    const response = await apiClient.post('/api/v1/sync/user/tasks')
    return response.data
  },

  /**
   * プロジェクトのタスクを同期
   */
  async syncProjectTasks(projectId: number): Promise<SyncResult> {
    const response = await apiClient.post(`/api/v1/sync/project/${projectId}/tasks`)
    return response.data
  },

  /**
   * 全プロジェクトを同期
   */
  async syncAllProjects(): Promise<SyncResult> {
    const response = await apiClient.post('/api/v1/sync/projects/all')
    return response.data
  },

  /**
   * プロジェクトの同期状態を取得
   */
  async getProjectSyncStatus(projectId: number): Promise<SyncStatus> {
    const response = await apiClient.get(`/api/v1/sync/project/${projectId}/status`)
    return response.data
  },

  /**
   * 単一の課題を同期
   */
  async syncSingleIssue(issueId: number): Promise<SyncResult> {
    const response = await apiClient.post(`/api/v1/sync/issue/${issueId}`)
    return response.data
  },

  /**
   * 同期履歴を取得
   */
  async getSyncHistory(params?: {
    sync_type?: string
    status?: string
    days?: number
    limit?: number
    offset?: number
  }): Promise<{
    total: number
    limit: number
    offset: number
    histories: Array<{
      id: number
      sync_type: string
      status: string
      target_id?: number
      target_name?: string
      items_created?: number
      items_updated?: number
      items_failed?: number
      total_items?: number
      error_message?: string
      started_at?: string
      completed_at?: string
      duration_seconds?: number
    }>
  }> {
    const response = await apiClient.get('/api/v1/sync/history', { params })
    return response.data
  },
}