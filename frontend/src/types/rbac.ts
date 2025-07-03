/**
 * RBAC（Role-Based Access Control）関連の型定義
 */

/**
 * ロールの種類
 */
export enum RoleType {
  ADMIN = 'ADMIN',
  PROJECT_LEADER = 'PROJECT_LEADER',
  MEMBER = 'MEMBER'
}

/**
 * ロール
 */
export interface Role {
  id: number;
  name: RoleType;
  description: string;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * パーミッション
 */
export interface Permission {
  id: number;
  name: string;
  resource: string;
  action: string;
  description: string;
  created_at: string;
  updated_at: string;
}

/**
 * ユーザーロール
 */
export interface UserRole {
  id: number;
  user_id: number;
  role_id: number;
  project_id: number | null;
  role: Role;
  created_at: string;
  updated_at: string;
}

/**
 * 権限チェック用のユーティリティ型
 */
export interface PermissionCheck {
  hasRole: (role: RoleType, projectId?: number) => boolean;
  hasPermission: (permission: string, projectId?: number) => boolean;
  canAccessProject: (projectId: number) => boolean;
  canManageProject: (projectId: number) => boolean;
  isAdmin: () => boolean;
  isProjectLeader: () => boolean;
}

/**
 * ロール階層の定義
 */
export const ROLE_HIERARCHY = {
  [RoleType.ADMIN]: [RoleType.ADMIN, RoleType.PROJECT_LEADER, RoleType.MEMBER],
  [RoleType.PROJECT_LEADER]: [RoleType.PROJECT_LEADER, RoleType.MEMBER],
  [RoleType.MEMBER]: [RoleType.MEMBER]
};

/**
 * パーミッション定数
 */
export const PERMISSIONS = {
  // ユーザー管理
  USERS_READ: 'users.read',
  USERS_WRITE: 'users.write',
  USERS_DELETE: 'users.delete',
  
  // プロジェクト管理
  PROJECTS_READ: 'projects.read',
  PROJECTS_WRITE: 'projects.write',
  PROJECTS_DELETE: 'projects.delete',
  PROJECTS_MANAGE: 'projects.manage',
  
  // メトリクス
  METRICS_READ: 'metrics.read',
  METRICS_EXPORT: 'metrics.export',
  
  // システム管理
  SYSTEM_ADMIN: 'system.admin'
} as const;

/**
 * ロールごとのデフォルトパーミッション
 */
export const ROLE_PERMISSIONS = {
  [RoleType.ADMIN]: Object.values(PERMISSIONS),
  [RoleType.PROJECT_LEADER]: [
    PERMISSIONS.PROJECTS_READ,
    PERMISSIONS.PROJECTS_WRITE,
    PERMISSIONS.PROJECTS_MANAGE,
    PERMISSIONS.METRICS_READ,
    PERMISSIONS.METRICS_EXPORT
  ],
  [RoleType.MEMBER]: [
    PERMISSIONS.PROJECTS_READ,
    PERMISSIONS.METRICS_READ
  ]
};