/**
 * 組織サービス (Phase 0)
 */

import { apiClient } from '@/lib/api-client'
import type { OrganizationRole } from '@/types/users'

export interface OrganizationResponse {
  id: number
  name: string
  slug: string
  fiscal_year_start_month: number
  timezone: string
  settings: Record<string, unknown>
  is_active: boolean
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface OrganizationCreateRequest {
  name: string
  slug: string
  fiscal_year_start_month?: number
  timezone?: string
  settings?: Record<string, unknown>
}

export interface OrganizationUpdateRequest {
  name?: string
  fiscal_year_start_month?: number
  timezone?: string
  settings?: Record<string, unknown>
  is_active?: boolean
}

export interface OrganizationMemberResponse {
  id: number
  organization_id: number
  user_id: number
  user_email: string | null
  user_name: string | null
  role: OrganizationRole
  joined_at: string
}

export interface OrganizationMemberCreateRequest {
  user_id: number
  role?: OrganizationRole
}

export interface OrganizationMemberUpdateRequest {
  role: OrganizationRole
}

export const organizationService = {
  async listMine(): Promise<OrganizationResponse[]> {
    return await apiClient.get('/api/v1/organizations/me')
  },

  async get(organizationId: number): Promise<OrganizationResponse> {
    return await apiClient.get(`/api/v1/organizations/${organizationId}`)
  },

  async update(
    organizationId: number,
    payload: OrganizationUpdateRequest
  ): Promise<OrganizationResponse> {
    return await apiClient.patch(
      `/api/v1/organizations/${organizationId}`,
      payload
    )
  },

  async listMembers(
    organizationId: number,
    params?: { skip?: number; limit?: number }
  ): Promise<OrganizationMemberResponse[]> {
    return await apiClient.get(
      `/api/v1/organizations/${organizationId}/members`,
      { params }
    )
  },

  async addMember(
    organizationId: number,
    payload: OrganizationMemberCreateRequest
  ): Promise<OrganizationMemberResponse> {
    return await apiClient.post(
      `/api/v1/organizations/${organizationId}/members`,
      payload
    )
  },

  async updateMemberRole(
    organizationId: number,
    userId: number,
    payload: OrganizationMemberUpdateRequest
  ): Promise<OrganizationMemberResponse> {
    return await apiClient.patch(
      `/api/v1/organizations/${organizationId}/members/${userId}`,
      payload
    )
  },

  async removeMember(organizationId: number, userId: number): Promise<void> {
    await apiClient.delete(
      `/api/v1/organizations/${organizationId}/members/${userId}`
    )
  },

  // System Admin
  async listAll(): Promise<OrganizationResponse[]> {
    return await apiClient.get('/api/v1/system/organizations')
  },

  async create(
    payload: OrganizationCreateRequest
  ): Promise<OrganizationResponse> {
    return await apiClient.post('/api/v1/system/organizations', payload)
  },

  async deleteOrganization(organizationId: number): Promise<void> {
    await apiClient.delete(`/api/v1/system/organizations/${organizationId}`)
  },
}
