/**
 * 権限に基づいてコンポーネントの表示を制御するコンポーネント (Phase 0)
 *
 * usePermissions が active_org_id 内のロールを階層判定するため、
 * roles に指定したいずれかのロール以上を満たせば表示される。
 * System Admin は常にバイパスされる。
 */

import { ReactNode } from 'react'

import { usePermissions } from '@/hooks/usePermissions'
import type { OrganizationRole } from '@/types/users'

interface ProtectedComponentProps {
  children: ReactNode
  /** 必要なロール (いずれか 1 つを満たせば表示) */
  roles?: OrganizationRole[]
  /** 評価対象の組織 ID (省略時は active_org_id) */
  organizationId?: number
  /** 権限がない場合に表示する代替コンポーネント */
  fallback?: ReactNode
}

export const ProtectedComponent = ({
  children,
  roles,
  organizationId,
  fallback = null,
}: ProtectedComponentProps) => {
  const permissions = usePermissions()

  if (!roles || roles.length === 0) {
    return <>{children}</>
  }

  const hasAccess = roles.some((role) =>
    permissions.hasRole(role, organizationId)
  )

  return hasAccess ? <>{children}</> : <>{fallback}</>
}

/**
 * System Admin のみ表示するコンポーネント
 */
export const SystemAdminOnly = ({
  children,
  fallback = null,
}: {
  children: ReactNode
  fallback?: ReactNode
}) => {
  const permissions = usePermissions()
  return permissions.isSystemAdmin() ? <>{children}</> : <>{fallback}</>
}

/**
 * 組織内 ADMIN 以上で表示するコンポーネント
 */
export const AdminOnly = ({
  children,
  organizationId,
  fallback = null,
}: {
  children: ReactNode
  organizationId?: number
  fallback?: ReactNode
}) => (
  <ProtectedComponent
    roles={['ADMIN']}
    organizationId={organizationId}
    fallback={fallback}
  >
    {children}
  </ProtectedComponent>
)

/**
 * 組織内 PROJECT_LEADER 以上で表示するコンポーネント
 */
export const ProjectLeaderOnly = ({
  children,
  organizationId,
  fallback = null,
}: {
  children: ReactNode
  organizationId?: number
  fallback?: ReactNode
}) => (
  <ProtectedComponent
    roles={['PROJECT_LEADER']}
    organizationId={organizationId}
    fallback={fallback}
  >
    {children}
  </ProtectedComponent>
)
