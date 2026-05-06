/**
 * 権限に基づいてコンポーネントをラップする HOC (Phase 0: organization_members ベース)
 */

import { ComponentType, ReactNode } from 'react'

import { ProtectedComponent } from './ProtectedComponent'
import type { OrganizationRole } from '@/types/users'

interface WithPermissionOptions {
  roles?: OrganizationRole[]
  organizationId?: number
  fallback?: ReactNode
}

export function withPermission<P extends object>(
  Component: ComponentType<P>,
  options: WithPermissionOptions
): ComponentType<P & { organizationId?: number }> {
  const Wrapped = (props: P & { organizationId?: number }) => {
    const organizationId = props.organizationId ?? options.organizationId
    return (
      <ProtectedComponent
        roles={options.roles}
        organizationId={organizationId}
        fallback={options.fallback}
      >
        <Component {...props} />
      </ProtectedComponent>
    )
  }
  Wrapped.displayName = `withPermission(${Component.displayName ?? Component.name ?? 'Component'})`
  return Wrapped
}

export const withAdminOnly = <P extends object>(
  Component: ComponentType<P>,
  fallback?: ReactNode
) => withPermission(Component, { roles: ['ADMIN'], fallback })

export const withProjectLeaderAccess = <P extends object>(
  Component: ComponentType<P>,
  fallback?: ReactNode
) => withPermission(Component, { roles: ['PROJECT_LEADER'], fallback })

export const withProjectMemberAccess = <P extends object>(
  Component: ComponentType<P>,
  fallback?: ReactNode
) => withPermission(Component, { roles: ['MEMBER'], fallback })
