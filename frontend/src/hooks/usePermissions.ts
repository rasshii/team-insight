/**
 * @fileoverview 権限チェック用のカスタムフック
 *
 * ユーザーのロールと権限を検証し、機能へのアクセス制御を行うカスタムフックです。
 * RBAC（ロールベースアクセス制御）システムを実装しています。
 *
 * @module usePermissions
 */

import { useMemo } from 'react';
import { useAppSelector } from '@/store/hooks';
import { selectCurrentUser } from '@/store/slices/authSlice';
import { RoleType, PermissionCheck, ROLE_HIERARCHY, ROLE_PERMISSIONS } from '@/types/rbac';

/**
 * 現在のユーザーの権限をチェックするカスタムフック
 *
 * ログイン中のユーザーのロールと権限を検証し、
 * 各種機能へのアクセス制御を行うためのユーティリティ関数群を提供します。
 *
 * ## ロール階層
 * - ADMIN: 全機能へのアクセス権限を持つ最上位ロール
 * - PROJECT_LEADER: プロジェクト管理権限を持つロール
 * - MEMBER: 基本的なメンバー権限
 *
 * ## 権限スコープ
 * - グローバルロール: システム全体に適用される権限（project_id = null）
 * - プロジェクトロール: 特定プロジェクトにのみ適用される権限（project_id指定）
 *
 * @returns {PermissionCheck} 権限チェック関数群を含むオブジェクト
 *
 * @example
 * ```tsx
 * function AdminPanel() {
 *   const permissions = usePermissions();
 *
 *   if (!permissions.isAdmin()) {
 *     return <AccessDenied />;
 *   }
 *
 *   return <AdminDashboard />;
 * }
 * ```
 *
 * @example
 * ```tsx
 * function ProjectSettings({ projectId }) {
 *   const permissions = usePermissions();
 *
 *   // プロジェクト管理権限のチェック
 *   const canManage = permissions.canManageProject(projectId);
 *
 *   return (
 *     <div>
 *       {canManage && <EditButton />}
 *     </div>
 *   );
 * }
 * ```
 *
 * @remarks
 * - 管理者（ADMIN）ロールは全ての権限チェックでtrueを返します
 * - ユーザーが未認証の場合、全ての権限チェックでfalseを返します
 * - パフォーマンス最適化のため、useMemoで結果をメモ化しています
 *
 * @see {@link PermissionCheck} - 権限チェック関数の型定義
 * @see {@link RoleType} - ロールの型定義
 * @see {@link ROLE_PERMISSIONS} - ロールごとの権限マッピング
 */
export const usePermissions = (): PermissionCheck => {
  const currentUser = useAppSelector(selectCurrentUser);

  return useMemo(() => {
    // デバッグ用ログ（本番環境では削除してください）
    if (process.env.NODE_ENV === 'development') {
      console.log('usePermissions - currentUser:', currentUser);
    }
    
    // ユーザーが存在しない場合のデフォルト権限オブジェクト
    if (!currentUser) {
      return {
        hasRole: () => false,
        hasPermission: () => false,
        canAccessProject: () => false,
        canManageProject: () => false,
        isAdmin: () => false,
        isProjectLeader: () => false,
      };
    }
    
    const permissions: PermissionCheck = {
      /**
       * 指定されたロールを持っているかチェック
       */
      hasRole: (role: RoleType, projectId?: number) => {
        if (!currentUser || !currentUser.user_roles) return false;

        // 管理者ロールを持っているかチェック
        const hasAdminRole = currentUser.user_roles.some(
          userRole => userRole.role.name === RoleType.ADMIN && userRole.project_id === null
        );
        
        // 管理者は全ての権限を持つ
        if (hasAdminRole) {
          return true;
        }

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
        if (!currentUser || !currentUser.user_roles) return false;

        // 管理者ロールを持っているかチェック
        const hasAdminRole = currentUser.user_roles.some(
          userRole => userRole.role.name === RoleType.ADMIN && userRole.project_id === null
        );
        
        // 管理者は全ての権限を持つ
        if (hasAdminRole) {
          return true;
        }

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
        if (!currentUser || !currentUser.user_roles) return false;

        // 管理者ロールを持っているかチェック
        const hasAdminRole = currentUser.user_roles.some(
          userRole => userRole.role.name === RoleType.ADMIN && userRole.project_id === null
        );
        
        // 管理者は全プロジェクトにアクセス可能
        if (hasAdminRole) {
          return true;
        }

        // プロジェクトメンバーかチェック（プロジェクトに関連するロールを持っているか）
        return currentUser.user_roles.some(
          userRole => userRole.project_id === projectId
        );
      },

      /**
       * プロジェクトの管理権限があるかチェック
       */
      canManageProject: (projectId: number) => {
        if (!currentUser || !currentUser.user_roles) return false;

        // 管理者ロールを持っているかチェック
        const hasAdminRole = currentUser.user_roles.some(
          userRole => userRole.role.name === RoleType.ADMIN && userRole.project_id === null
        );
        
        // 管理者は全プロジェクトを管理可能
        if (hasAdminRole) {
          return true;
        }

        // プロジェクトリーダー権限をチェック
        return permissions.hasRole(RoleType.PROJECT_LEADER, projectId);
      },

      /**
       * 管理者かどうかチェック
       */
      isAdmin: () => {
        if (!currentUser || !currentUser.user_roles) return false;
        return currentUser.user_roles.some(
          userRole => userRole.role.name === RoleType.ADMIN && userRole.project_id === null
        );
      },

      /**
       * プロジェクトリーダーかどうかチェック（グローバルロール）
       */
      isProjectLeader: () => {
        if (!currentUser || !currentUser.user_roles) return false;
        return currentUser.user_roles.some(
          userRole => userRole.role.name === RoleType.PROJECT_LEADER && userRole.project_id === null
        );
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