/**
 * ユーザー / 組織所属に関する型定義 (Phase 0)
 */

export type OrganizationRole = 'ADMIN' | 'PROJECT_LEADER' | 'MEMBER'

export interface OrganizationMembership {
  organization_id: number
  organization_name: string | null
  organization_slug: string | null
  role: OrganizationRole
}

export interface User {
  id: number
  email: string | null
  name: string | null
  full_name?: string | null
  is_active: boolean
  is_system_admin: boolean
  organizations: OrganizationMembership[]
  timezone?: string
  locale?: string
  date_format?: string
  created_at: string
  updated_at: string
  last_login_at?: string | null
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  per_page: number
}

export interface UserUpdate {
  name?: string
  email?: string
  is_active?: boolean
}

export interface UserFilters {
  is_active?: boolean
  search?: string
}

export interface UserSortOptions {
  sort_by?: 'name' | 'email' | 'created_at' | 'last_login_at'
  sort_order?: 'asc' | 'desc'
}
