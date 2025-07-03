import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { healthService } from '@/services/health.service'

/**
 * ヘルスチェックを実行するフック
 * 
 * @param refetchInterval - 自動更新の間隔（ミリ秒）。0の場合は自動更新しない
 */
export const useHealthCheck = (refetchInterval = 30000) => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => healthService.checkHealth(),
    refetchInterval, // デフォルトは30秒ごとに自動更新
    retry: 1, // ヘルスチェックは1回だけリトライ
    staleTime: 10 * 1000, // 10秒
  })
}