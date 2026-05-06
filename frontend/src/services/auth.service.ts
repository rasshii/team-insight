/**
 * 認証サービス (Phase 0: 組織切替対応)
 *
 * Phase 6 で Backlog OAuth 関連を削除済み。
 * Phase 0 で旧 RBAC を廃止し、organizations 配列をユーザー情報に含めるよう変更。
 * Phase 1 でローカルログイン (login / accept-invitation / forgot-password / reset-password)
 * を追加予定。
 */

import { apiClient } from '@/lib/api-client'
import type { OrganizationRole } from '@/types/users'

export interface OrganizationMembershipResponse {
  organization_id: number
  organization_name: string | null
  organization_slug: string | null
  role: OrganizationRole
}

export interface UserInfoResponse {
  id: number
  email: string | null
  name: string | null
  full_name: string | null
  is_active: boolean
  is_system_admin: boolean
  organizations: OrganizationMembershipResponse[]
}

export interface TokenRefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
  active_org_id: number | null
}

export interface SwitchOrganizationRequest {
  organization_id: number
}

export const authService = {
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout')
  },

  async getCurrentUser(): Promise<UserInfoResponse> {
    return await apiClient.get('/api/v1/auth/me')
  },

  async refreshJwtToken(): Promise<TokenRefreshResponse> {
    return await apiClient.post('/api/v1/auth/refresh')
  },

  async switchOrganization(
    organizationId: number
  ): Promise<TokenRefreshResponse> {
    return await apiClient.post<TokenRefreshResponse>(
      '/api/v1/auth/switch-organization',
      { organization_id: organizationId } satisfies SwitchOrganizationRequest
    )
  },
}
