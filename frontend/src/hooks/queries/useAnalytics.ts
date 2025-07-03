import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { analyticsService } from '@/services/analytics.service'

/**
 * プロジェクトの健全性情報を取得するフック
 */
export const useProjectHealth = (projectId: number, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'health', projectId],
    queryFn: () => analyticsService.getProjectHealth(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * プロジェクトのボトルネックを取得するフック
 */
export const useProjectBottlenecks = (projectId: number, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'bottlenecks', projectId],
    queryFn: () => analyticsService.getProjectBottlenecks(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * プロジェクトのベロシティを取得するフック
 */
export const useProjectVelocity = (projectId: number, periodDays = 30, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'velocity', projectId, periodDays],
    queryFn: () => analyticsService.getProjectVelocity(projectId, periodDays),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * プロジェクトのサイクルタイムを取得するフック
 */
export const useProjectCycleTime = (projectId: number, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'cycle-time', projectId],
    queryFn: () => analyticsService.getProjectCycleTime(projectId),
    enabled: enabled && !!projectId,
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * 個人ダッシュボード情報を取得するフック
 */
export const usePersonalDashboard = () => {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, 'personal-dashboard'],
    queryFn: () => analyticsService.getPersonalDashboard(),
    staleTime: 5 * 60 * 1000, // 5分
  })
}