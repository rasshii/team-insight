/**
 * 設定管理APIサービス
 */

import { apiClient } from '@/lib/api-client'
import { AllSettings, SettingsUpdateRequest } from '@/types/settings'

export class SettingsService {
  private baseUrl = '/settings'

  /**
   * 全設定を取得
   */
  async getAllSettings(): Promise<AllSettings> {
    const response = await apiClient.get<AllSettings>(this.baseUrl)
    return response
  }

  /**
   * グループごとの設定を取得
   */
  async getSettingsByGroup(group: string): Promise<Record<string, any>> {
    const response = await apiClient.get<Record<string, any>>(`${this.baseUrl}/${group}`)
    return response
  }

  /**
   * 全設定を更新
   */
  async updateAllSettings(settings: SettingsUpdateRequest): Promise<AllSettings> {
    const response = await apiClient.put<AllSettings>(this.baseUrl, settings)
    return response
  }
}

export const settingsService = new SettingsService()