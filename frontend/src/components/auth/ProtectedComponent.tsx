/**
 * 権限に基づいてコンポーネントの表示を制御するコンポーネント
 */

import { ReactNode } from 'react';
import { usePermissions } from '@/hooks/usePermissions';
import { RoleType } from '@/types/rbac';

interface ProtectedComponentProps {
  children: ReactNode;
  /** 必要なロール（いずれか1つでも持っていれば表示） */
  roles?: RoleType[];
  /** 必要な権限（いずれか1つでも持っていれば表示） */
  permissions?: string[];
  /** プロジェクトID（プロジェクト単位の権限チェック用） */
  projectId?: number;
  /** 全ての条件を満たす必要があるか（デフォルト: false） */
  requireAll?: boolean;
  /** 権限がない場合に表示する代替コンポーネント */
  fallback?: ReactNode;
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
 * // プロジェクトリーダーまたは管理者のみ表示
 * <ProtectedComponent 
 *   roles={[RoleType.PROJECT_LEADER, RoleType.ADMIN]} 
 *   projectId={projectId}
 * >
 *   <ProjectSettings />
 * </ProtectedComponent>
 * 
 * // 特定の権限を持つユーザーのみ表示
 * <ProtectedComponent permissions={['projects.manage']}>
 *   <ManageProjectButton />
 * </ProtectedComponent>
 * ```
 */
export const ProtectedComponent = ({
  children,
  roles = [],
  permissions: perms = [],
  projectId,
  requireAll = false,
  fallback = null,
}: ProtectedComponentProps) => {
  const permissions = usePermissions();

  // 権限チェック
  const hasAccess = (() => {
    const checks: boolean[] = [];

    // ロールチェック
    if (roles.length > 0) {
      const roleCheck = requireAll
        ? roles.every(role => permissions.hasRole(role, projectId))
        : roles.some(role => permissions.hasRole(role, projectId));
      checks.push(roleCheck);
    }

    // パーミッションチェック
    if (perms.length > 0) {
      const permCheck = requireAll
        ? perms.every(perm => permissions.hasPermission(perm, projectId))
        : perms.some(perm => permissions.hasPermission(perm, projectId));
      checks.push(permCheck);
    }

    // チェック項目がない場合は表示
    if (checks.length === 0) return true;

    // 全ての条件をチェック
    return requireAll ? checks.every(Boolean) : checks.some(Boolean);
  })();

  return hasAccess ? <>{children}</> : <>{fallback}</>;
};

/**
 * 管理者のみ表示するコンポーネント
 */
export const AdminOnly = ({ 
  children, 
  fallback = null 
}: { 
  children: ReactNode; 
  fallback?: ReactNode;
}) => (
  <ProtectedComponent roles={[RoleType.ADMIN]} fallback={fallback}>
    {children}
  </ProtectedComponent>
);

/**
 * プロジェクトリーダー以上の権限で表示するコンポーネント
 */
export const ProjectLeaderOnly = ({ 
  children, 
  projectId,
  fallback = null 
}: { 
  children: ReactNode;
  projectId?: number;
  fallback?: ReactNode;
}) => (
  <ProtectedComponent 
    roles={[RoleType.PROJECT_LEADER, RoleType.ADMIN]} 
    projectId={projectId}
    fallback={fallback}
  >
    {children}
  </ProtectedComponent>
);