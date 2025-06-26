/**
 * 権限に基づいて表示を制御するコンポーネント
 */

import React from 'react';
import { usePermissions, checkPermission } from '@/hooks/usePermissions';
import { RoleType } from '@/types/rbac';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Shield } from 'lucide-react';

interface ProtectedComponentProps {
  children: React.ReactNode;
  roles?: RoleType[];
  permissions?: string[];
  projectId?: number;
  requireAll?: boolean;
  fallback?: React.ReactNode;
  showError?: boolean;
}

/**
 * 権限に基づいてコンポーネントの表示を制御
 * 
 * @example
 * ```tsx
 * // 管理者のみ表示
 * <ProtectedComponent roles={[RoleType.ADMIN]}>
 *   <AdminPanel />
 * </ProtectedComponent>
 * 
 * // プロジェクトリーダー以上の権限で表示
 * <ProtectedComponent 
 *   roles={[RoleType.PROJECT_LEADER]} 
 *   projectId={projectId}
 * >
 *   <ProjectSettings />
 * </ProtectedComponent>
 * 
 * // 特定のパーミッションを持つユーザーのみ表示
 * <ProtectedComponent permissions={[PERMISSIONS.METRICS_EXPORT]}>
 *   <ExportButton />
 * </ProtectedComponent>
 * ```
 */
export const ProtectedComponent: React.FC<ProtectedComponentProps> = ({
  children,
  roles = [],
  permissions = [],
  projectId,
  requireAll = false,
  fallback = null,
  showError = false
}) => {
  const userPermissions = usePermissions();

  const hasAccess = checkPermission(userPermissions, {
    roles,
    permissions,
    projectId,
    requireAll
  });

  if (!hasAccess) {
    if (showError) {
      return (
        <Alert variant="destructive">
          <Shield className="h-4 w-4" />
          <AlertDescription>
            このコンテンツを表示する権限がありません。
            {projectId && 'プロジェクトメンバーである必要があります。'}
          </AlertDescription>
        </Alert>
      );
    }
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

/**
 * 権限チェック用のHOC（Higher Order Component）
 */
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  requirement: {
    roles?: RoleType[];
    permissions?: string[];
    requireAll?: boolean;
  }
) {
  return (props: P & { projectId?: number }) => {
    const { projectId, ...restProps } = props;

    return (
      <ProtectedComponent
        roles={requirement.roles}
        permissions={requirement.permissions}
        projectId={projectId}
        requireAll={requirement.requireAll}
        showError
      >
        <Component {...(restProps as P)} projectId={projectId} />
      </ProtectedComponent>
    );
  };
}