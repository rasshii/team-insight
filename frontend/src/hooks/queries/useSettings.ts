/**
 * 設定管理関連のカスタムフック
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsService } from '@/services/settings.service'
import { AllSettings, SettingsUpdateRequest } from '@/types/settings'
import { toast } from '@/components/ui/use-toast'

const QUERY_KEYS = {
  all: ['settings'],
  byGroup: (group: string) => ['settings', group],
}

/**
 * 全設定を取得するフック
 */
export const useSettings = () => {
  return useQuery({
    queryKey: QUERY_KEYS.all,
    queryFn: () => settingsService.getAllSettings(),
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * グループごとの設定を取得するフック
 */
export const useSettingsByGroup = (group: string) => {
  return useQuery({
    queryKey: QUERY_KEYS.byGroup(group),
    queryFn: () => settingsService.getSettingsByGroup(group),
    enabled: !!group,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * 設定を更新するミューテーション
 */
export const useUpdateSettings = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (settings: SettingsUpdateRequest) => 
      settingsService.updateAllSettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(QUERY_KEYS.all, data)
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.all })
      toast({
        title: '設定を更新しました',
        variant: 'default',
      })
    },
    onError: (error: any) => {
      toast({
        title: '設定の更新に失敗しました',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      })
    },
  })
}