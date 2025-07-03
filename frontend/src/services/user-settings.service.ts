/**
 * ユーザー設定APIサービス
 */

import { apiClient } from '@/lib/api-client'
import { 
  UserSettings, 
  UserSettingsUpdate,
  LoginHistory,
  ActivityLog,
  SessionInfo 
} from '@/types/user-settings'

export class UserSettingsService {
  private baseUrl = '/api/v1/users'

  /**
   * 現在のユーザーの設定を取得
   */
  async getMySettings(): Promise<UserSettings> {
    const response = await apiClient.get<UserSettings>(`${this.baseUrl}/me`)
    return response
  }

  /**
   * 現在のユーザーの設定を更新
   */
  async updateMySettings(settings: UserSettingsUpdate): Promise<UserSettings> {
    const response = await apiClient.put<UserSettings>(`${this.baseUrl}/me`, settings)
    return response
  }

  /**
   * ログイン履歴を取得
   */
  async getLoginHistory(page: number = 1, pageSize: number = 20): Promise<{
    items: LoginHistory[]
    total: number
    page: number
    page_size: number
  }> {
    const response = await apiClient.get(`${this.baseUrl}/me/login-history`, {
      params: { page, page_size: pageSize }
    })
    return response
  }

  /**
   * アクティビティログを取得
   */
  async getActivityLogs(page: number = 1, pageSize: number = 50, action?: string): Promise<{
    items: ActivityLog[]
    total: number
    page: number
    page_size: number
  }> {
    const params: any = { page, page_size: pageSize }
    if (action) {
      params.action = action
    }
    const response = await apiClient.get(`${this.baseUrl}/me/activity-logs`, { params })
    return response
  }

  /**
   * アクティブセッション一覧を取得
   */
  async getSessions(): Promise<{ sessions: SessionInfo[] }> {
    const response = await apiClient.get(`${this.baseUrl}/me/sessions`)
    return response
  }

  /**
   * セッションを終了
   */
  async terminateSession(sessionId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/me/sessions/${sessionId}`)
  }
}

export const userSettingsService = new UserSettingsService()