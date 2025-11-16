/**
 * 設定管理APIサービス
 */

import { apiClient } from '@/lib/api-client'
import { AllSettings, SettingsUpdateRequest } from '@/types/settings'

const BASE_URL = '/settings'

export const settingsService = {
  /**
   * 全設定を取得
   */
  async getAllSettings(): Promise<AllSettings> {
    const response = await apiClient.get<AllSettings>(BASE_URL)
    return response
  },

  /**
   * グループごとの設定を取得
   */
  async getSettingsByGroup(group: string): Promise<Record<string, any>> {
    const response = await apiClient.get<Record<string, any>>(`${BASE_URL}/${group}`)
    return response
  },

  /**
   * 全設定を更新
   */
  async updateAllSettings(settings: SettingsUpdateRequest): Promise<AllSettings> {
    const response = await apiClient.put<AllSettings>(BASE_URL, settings)
    return response
  },
}