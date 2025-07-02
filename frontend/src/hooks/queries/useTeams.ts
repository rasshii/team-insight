/**
 * チーム管理用のReact Queryフック
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { teamsService } from '@/services/teams.service'
import { useToast } from '@/hooks/use-toast'
import {
  TeamCreateInput,
  TeamUpdateInput,
  TeamMemberCreateInput,
  TeamMemberUpdateInput,
} from '@/types/team'

// クエリキー
const QUERY_KEYS = {
  teams: ['teams'] as const,
  team: (id: number) => ['teams', id] as const,
  teamMembers: (id: number) => ['teams', id, 'members'] as const,
}

/**
 * チーム一覧を取得
 */
export function useTeams(params?: {
  page?: number
  page_size?: number
  with_stats?: boolean
}) {
  return useQuery({
    queryKey: [...QUERY_KEYS.teams, params],
    queryFn: () => teamsService.getTeams(params),
  })
}

/**
 * チーム詳細を取得
 */
export function useTeam(teamId: number) {
  return useQuery({
    queryKey: QUERY_KEYS.team(teamId),
    queryFn: () => teamsService.getTeam(teamId),
    enabled: !!teamId,
  })
}

/**
 * チームメンバー一覧を取得
 */
export function useTeamMembers(teamId: number) {
  return useQuery({
    queryKey: QUERY_KEYS.teamMembers(teamId),
    queryFn: () => teamsService.getTeamMembers(teamId),
    enabled: !!teamId,
  })
}

/**
 * チーム作成
 */
export function useCreateTeam() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: TeamCreateInput) => teamsService.createTeam(data),
    onSuccess: (response) => {
      // すべてのteamsクエリを無効化（paramsに関係なく）
      queryClient.invalidateQueries({ 
        predicate: (query) => query.queryKey[0] === 'teams'
      })
      toast({
        title: '成功',
        description: response.message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.message || 'チームの作成に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * チーム更新
 */
export function useUpdateTeam(teamId: number) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: TeamUpdateInput) =>
      teamsService.updateTeam(teamId, data),
    onSuccess: (response) => {
      // すべてのteamsクエリを無効化（paramsに関係なく）
      queryClient.invalidateQueries({ 
        predicate: (query) => query.queryKey[0] === 'teams'
      })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.team(teamId) })
      toast({
        title: '成功',
        description: response.message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.message || 'チームの更新に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * チーム削除
 */
export function useDeleteTeam() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (teamId: number) => teamsService.deleteTeam(teamId),
    onSuccess: (response) => {
      // すべてのteamsクエリを無効化（paramsに関係なく）
      queryClient.invalidateQueries({ 
        predicate: (query) => query.queryKey[0] === 'teams'
      })
      toast({
        title: '成功',
        description: response.message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.message || 'チームの削除に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * チームメンバー追加
 */
export function useAddTeamMember(teamId: number) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: TeamMemberCreateInput) =>
      teamsService.addTeamMember(teamId, data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.team(teamId) })
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.teamMembers(teamId),
      })
      toast({
        title: '成功',
        description: response.message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.message || 'メンバーの追加に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * チームメンバー更新
 */
export function useUpdateTeamMember(teamId: number, userId: number) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: TeamMemberUpdateInput) =>
      teamsService.updateTeamMember(teamId, userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.team(teamId) })
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.teamMembers(teamId),
      })
      toast({
        title: '成功',
        description: 'メンバーの役割を更新しました',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.message || 'メンバーの更新に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * チームメンバー削除
 */
export function useRemoveTeamMember(teamId: number) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (userId: number) =>
      teamsService.removeTeamMember(teamId, userId),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.team(teamId) })
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.teamMembers(teamId),
      })
      toast({
        title: '成功',
        description: response.message,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.message || 'メンバーの削除に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

/**
 * チームメンバーのパフォーマンスデータを取得
 */
export function useTeamMembersPerformance(teamId: number) {
  return useQuery({
    queryKey: ['team-members-performance', teamId],
    queryFn: () => teamsService.getTeamMembersPerformance(teamId),
    enabled: teamId > 0,
  })
}

/**
 * チームのタスク分配データを取得
 */
export function useTeamTaskDistribution(teamId: number) {
  return useQuery({
    queryKey: ['team-task-distribution', teamId],
    queryFn: () => teamsService.getTeamTaskDistribution(teamId),
    enabled: teamId > 0,
  })
}

/**
 * チームの生産性推移データを取得
 */
export function useTeamProductivityTrend(
  teamId: number,
  period: 'daily' | 'weekly' | 'monthly' = 'monthly'
) {
  return useQuery({
    queryKey: ['team-productivity-trend', teamId, period],
    queryFn: () => teamsService.getTeamProductivityTrend(teamId, period),
    enabled: teamId > 0,
  })
}

/**
 * チームの最近のアクティビティを取得
 */
export function useTeamActivities(teamId: number, limit: number = 20) {
  return useQuery({
    queryKey: ['team-activities', teamId, limit],
    queryFn: () => teamsService.getTeamActivities(teamId, limit),
    enabled: teamId > 0,
  })
}