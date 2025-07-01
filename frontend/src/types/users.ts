import { Role } from './rbac';

export interface User {
  id: number;
  email: string;
  name: string;
  backlog_user_id: string | null;
  is_active: boolean;
  is_email_verified: boolean;
  email_verified_at: string | null;
  auth_provider: 'email' | 'backlog';
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
  user_roles: UserRole[];
}

export interface UserRole {
  id: number;
  user_id: number;
  role_id: number;
  assigned_at: string;
  assigned_by: number | null;
  role: Role;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UserUpdate {
  name?: string;
  is_active?: boolean;
}

export interface UserRoleAssignmentRequest {
  role_id: number;
}

export interface UserRoleRemovalRequest {
  role_id: number;
}

export interface UserRoleUpdateRequest {
  roles: number[];
}

export interface AvailableRole {
  id: number;
  name: string;
  description: string | null;
}

export interface UserFilters {
  is_active?: boolean;
  is_email_verified?: boolean;
  role_ids?: number[];
  search?: string;
}

export interface UserSortOptions {
  sort_by?: 'name' | 'email' | 'created_at' | 'last_login_at';
  sort_order?: 'asc' | 'desc';
}