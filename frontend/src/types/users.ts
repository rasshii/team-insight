import { Role } from './rbac';

export interface User {
  id: number;
  email: string | null;
  name: string;
  backlog_id: number | null;
  user_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
  user_roles: UserRole[];
}

export interface UserRole {
  id: number;
  user_id: number;
  role_id: number;
  project_id: number | null;
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

export interface UserRoleAssignment {
  role_id: number;
  project_id: number | null;
}

export interface UserRoleAssignmentRequest {
  assignments: UserRoleAssignment[];
}

export interface UserRoleRemovalRequest {
  user_role_ids: number[];
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
  role_ids?: number[];
  search?: string;
  project_id?: number;
  team_id?: number;
}

export interface UserSortOptions {
  sort_by?: 'name' | 'email' | 'created_at' | 'last_login_at';
  sort_order?: 'asc' | 'desc';
}