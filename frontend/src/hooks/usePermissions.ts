/**
 * 権限チェック用のカスタムフック (Phase 0: organization_members ベース)
 *
 * Phase 0 で旧 RBAC を廃止し、users.is_system_admin と organization_members.role に
 * 一本化した。アクセス判定は active_org_id 内のロールを基準に階層的に行う。
 */

import { useMemo } from 'react'

import { useAppSelector } from '@/store/hooks'
import {
  selectActiveOrganizationId,
  selectCurrentUser,
} from '@/store/slices/authSlice'
import type { OrganizationRole } from '@/types/users'

export type RoleType = OrganizationRole

const ROLE_HIERARCHY: Record<OrganizationRole, number> = {
  ADMIN: 3,
  PROJECT_LEADER: 2,
  MEMBER: 1,
}

export interface PermissionCheck {
  /** 指定組織 (省略時は active_org_id) で role 以上の権限を持つか */
  hasRole: (role: OrganizationRole, organizationId?: number) => boolean
  /** 組織内 ADMIN か (System Admin もバイパスで true) */
  isAdmin: () => boolean
  /** 組織内 PROJECT_LEADER 以上か */
  isProjectLeader: () => boolean
  /** System Admin (テナントバイパス権限) か */
  isSystemAdmin: () => boolean
}

export const usePermissions = (): PermissionCheck => {
  const currentUser = useAppSelector(selectCurrentUser)
  const activeOrganizationId = useAppSelector(selectActiveOrganizationId)

  return useMemo(() => {
    if (!currentUser) {
      return {
        hasRole: () => false,
        isAdmin: () => false,
        isProjectLeader: () => false,
        isSystemAdmin: () => false,
      }
    }

    const isSystemAdmin = () => Boolean(currentUser.is_system_admin)

    const findRole = (orgId: number): OrganizationRole | null => {
      const membership = currentUser.organizations.find(
        (m) => m.organization_id === orgId
      )
      return membership?.role ?? null
    }

    const hasRole: PermissionCheck['hasRole'] = (role, organizationId) => {
      if (isSystemAdmin()) return true
      const targetOrgId = organizationId ?? activeOrganizationId
      if (targetOrgId == null) return false
      const actual = findRole(targetOrgId)
      if (!actual) return false
      return ROLE_HIERARCHY[actual] >= ROLE_HIERARCHY[role]
    }

    return {
      hasRole,
      isAdmin: () => hasRole('ADMIN'),
      isProjectLeader: () => hasRole('PROJECT_LEADER'),
      isSystemAdmin,
    }
  }, [currentUser, activeOrganizationId])
}
