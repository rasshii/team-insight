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
    return await apiClient.get('/api/v1/sync/connection/status')
  },

  /**
   * ユーザーのタスクを同期
   */
  async syncUserTasks(): Promise<SyncResult> {
    return await apiClient.post('/api/v1/sync/user/tasks')
  },

  /**
   * プロジェクトのタスクを同期
   */
  async syncProjectTasks(projectId: number): Promise<SyncResult> {
    return await apiClient.post(`/api/v1/sync/project/${projectId}/tasks`)
  },

  /**
   * 全プロジェクトを同期
   */
  async syncAllProjects(): Promise<SyncResult> {
    return await apiClient.post('/api/v1/sync/projects/all')
  },

  /**
   * プロジェクトの同期状態を取得
   */
  async getProjectSyncStatus(projectId: number): Promise<SyncStatus> {
    return await apiClient.get(`/api/v1/sync/project/${projectId}/status`)
  },

  /**
   * 単一の課題を同期
   */
  async syncSingleIssue(issueId: number): Promise<SyncResult> {
    return await apiClient.post(`/api/v1/sync/issue/${issueId}`)
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
    return await apiClient.get('/api/v1/sync/history', { params })
  },
}