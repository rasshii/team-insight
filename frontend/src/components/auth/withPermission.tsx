/**
 * 権限に基づいてコンポーネントをラップする高階コンポーネント（HOC）
 */

import { ComponentType } from 'react';
import { ProtectedComponent } from './ProtectedComponent';
import { RoleType } from '@/types/rbac';

interface WithPermissionOptions {
  /** 必要なロール（いずれか1つでも持っていれば表示） */
  roles?: RoleType[];
  /** 必要な権限（いずれか1つでも持っていれば表示） */
  permissions?: string[];
  /** プロジェクトID（プロジェクト単位の権限チェック用） */
  projectId?: number;
  /** 全ての条件を満たす必要があるか（デフォルト: false） */
  requireAll?: boolean;
  /** 権限がない場合に表示する代替コンポーネント */
  fallback?: React.ReactNode;
}

/**
 * 権限に基づいてコンポーネントの表示を制御する高階コンポーネント
 * 
 * @example
 * ```tsx
 * // 管理者のみアクセス可能なコンポーネントを作成
 * const AdminDashboard = withPermission(Dashboard, {
 *   roles: [RoleType.ADMIN]
 * });
 * 
 * // プロジェクトリーダー以上の権限が必要なコンポーネント
 * const ProjectSettings = withPermission(Settings, {
 *   roles: [RoleType.PROJECT_LEADER, RoleType.ADMIN],
 *   fallback: <div>権限がありません</div>
 * });
 * 
 * // 使用時にプロジェクトIDを渡す
 * <ProjectSettings projectId={projectId} />
 * ```
 */
export function withPermission<P extends object>(
  Component: ComponentType<P>,
  options: WithPermissionOptions
): ComponentType<P & { projectId?: number }> {
  const WrappedComponent = (props: P & { projectId?: number }) => {
    // propsからprojectIdを取得（optionsのprojectIdより優先）
    const projectId = props.projectId ?? options.projectId;

    return (
      <ProtectedComponent
        roles={options.roles}
        permissions={options.permissions}
        projectId={projectId}
        requireAll={options.requireAll}
        fallback={options.fallback}
      >
        <Component {...props} />
      </ProtectedComponent>
    );
  };

  // デバッグ用にコンポーネント名を設定
  WrappedComponent.displayName = `withPermission(${Component.displayName || Component.name || 'Component'})`;

  return WrappedComponent;
}

/**
 * プリセットされた権限HOC
 */

/**
 * 管理者のみアクセス可能なコンポーネントを作成
 */
export const withAdminOnly = <P extends object>(
  Component: ComponentType<P>,
  fallback?: React.ReactNode
) => withPermission(Component, { 
  roles: [RoleType.ADMIN], 
  fallback 
});

/**
 * プロジェクトリーダー以上の権限でアクセス可能なコンポーネントを作成
 */
export const withProjectLeaderAccess = <P extends object>(
  Component: ComponentType<P>,
  fallback?: React.ReactNode
) => withPermission(Component, { 
  roles: [RoleType.PROJECT_LEADER, RoleType.ADMIN], 
  fallback 
});

/**
 * プロジェクトメンバー以上の権限でアクセス可能なコンポーネントを作成
 */
export const withProjectMemberAccess = <P extends object>(
  Component: ComponentType<P>,
  fallback?: React.ReactNode
) => withPermission(Component, { 
  roles: [RoleType.MEMBER, RoleType.PROJECT_LEADER, RoleType.ADMIN], 
  fallback 
});