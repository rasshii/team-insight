/**
 * チーム管理関連の型定義
 */

import { User } from './users'

export enum TeamRole {
  TEAM_LEADER = 'team_leader',
  MEMBER = 'member',
}

export interface TeamMember {
  id: number
  user_id: number
  team_id: number
  role: string
  joined_at: string
  user: {
    id: number
    backlog_id?: number
    name: string
    email?: string
  }
}

export interface Team {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
  members: TeamMember[]
}

export interface TeamWithStats extends Team {
  member_count: number
  active_tasks_count: number
  completed_tasks_this_month: number
  efficiency_score: number
}

export interface TeamCreateInput {
  name: string
  description?: string
}

export interface TeamUpdateInput {
  name?: string
  description?: string
}

export interface TeamMemberCreateInput {
  user_id: number
  role: TeamRole
}

export interface TeamMemberUpdateInput {
  role: TeamRole
}

// API レスポンス型
export interface TeamListResponse {
  teams: Team[]
  total: number
  page: number
  page_size: number
}

export interface TeamCreateResponse {
  success: boolean
  data: Team
  message: string
}

export interface TeamUpdateResponse {
  success: boolean
  data: Team
  message: string
}

export interface TeamDeleteResponse {
  success: boolean
  message: string
}

export interface TeamMemberAddResponse {
  success: boolean
  data: TeamMember
  message: string
}

export interface TeamMemberRemoveResponse {
  success: boolean
  message: string
}

/**
 * チームメンバーのパフォーマンスデータ
 */
export interface TeamMemberPerformance {
  user_id: number
  user_name: string
  completed_tasks: number
  average_completion_time: number
  efficiency_score: number
}

/**
 * チームの生産性推移データポイント
 */
export interface TeamProductivityDataPoint {
  date: string
  completed_tasks: number
  total_tasks: number
  efficiency: number
}

/**
 * チームのアクティビティログ
 */
export interface TeamActivity {
  id: number
  type: 'task_completed' | 'task_created' | 'member_added' | 'member_removed' | 'team_updated'
  user_id: number
  user_name: string
  description: string
  timestamp: string
  metadata?: Record<string, any>
}