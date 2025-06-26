/**
 * 権限チェック用のカスタムフック
 */

import { useMemo } from 'react';
import { useAppSelector } from '@/store/hooks';
import { selectCurrentUser } from '@/store/slices/authSlice';
import { RoleType, PermissionCheck, ROLE_HIERARCHY, ROLE_PERMISSIONS } from '@/types/rbac';

/**
 * 現在のユーザーの権限をチェックするフック
 */
export const usePermissions = (): PermissionCheck => {
  const currentUser = useAppSelector(selectCurrentUser);

  return useMemo(() => {
    const permissions: PermissionCheck = {
      /**
       * 指定されたロールを持っているかチェック
       */
      hasRole: (role: RoleType, projectId?: number) => {
        if (!currentUser) return false;

        // 管理者は全ての権限を持つ
        if (currentUser.is_superuser || currentUser.is_admin) {
          return true;
        }

        if (!currentUser.user_roles) return false;

        // プロジェクト指定がある場合
        if (projectId !== undefined) {
          return currentUser.user_roles.some(
            userRole => 
              userRole.project_id === projectId &&
              userRole.role.name === role
          );
        }

        // グローバルロールのチェック
        return currentUser.user_roles.some(
          userRole => 
            userRole.project_id === null &&
            userRole.role.name === role
        );
      },

      /**
       * 指定されたパーミッションを持っているかチェック
       */
      hasPermission: (permission: string, projectId?: number) => {
        if (!currentUser) return false;

        // 管理者は全ての権限を持つ
        if (currentUser.is_superuser || currentUser.is_admin) {
          return true;
        }

        if (!currentUser.user_roles) return false;

        // ユーザーのロールを取得
        const userRoles = projectId !== undefined
          ? currentUser.user_roles.filter(ur => ur.project_id === projectId)
          : currentUser.user_roles.filter(ur => ur.project_id === null);

        // 各ロールのパーミッションをチェック
        return userRoles.some(userRole => {
          const rolePermissions = ROLE_PERMISSIONS[userRole.role.name as RoleType] || [];
          return rolePermissions.includes(permission);
        });
      },

      /**
       * プロジェクトへのアクセス権限があるかチェック
       */
      canAccessProject: (projectId: number) => {
        if (!currentUser) return false;

        // 管理者は全プロジェクトにアクセス可能
        if (currentUser.is_superuser || currentUser.is_admin) {
          return true;
        }

        // プロジェクトメンバーかチェック
        if (currentUser.projects) {
          return currentUser.projects.some(project => project.id === projectId);
        }

        return false;
      },

      /**
       * プロジェクトの管理権限があるかチェック
       */
      canManageProject: (projectId: number) => {
        if (!currentUser) return false;

        // 管理者は全プロジェクトを管理可能
        if (currentUser.is_superuser || currentUser.is_admin) {
          return true;
        }

        // プロジェクトリーダー権限をチェック
        return permissions.hasRole(RoleType.PROJECT_LEADER, projectId);
      },

      /**
       * 管理者かどうかチェック
       */
      isAdmin: () => {
        if (!currentUser) return false;
        return currentUser.is_superuser || currentUser.is_admin || false;
      }
    };

    return permissions;
  }, [currentUser]);
};

/**
 * 権限に基づいて表示を制御するユーティリティ関数
 */
export const checkPermission = (
  permissions: PermissionCheck,
  requirement: {
    roles?: RoleType[];
    permissions?: string[];
    projectId?: number;
    requireAll?: boolean;
  }
): boolean => {
  const { roles = [], permissions: perms = [], projectId, requireAll = false } = requirement;

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

  // 全ての条件をチェック
  return checks.length === 0 || (requireAll ? checks.every(Boolean) : checks.some(Boolean));
};