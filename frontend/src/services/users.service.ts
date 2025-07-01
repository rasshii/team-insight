import api from '@/services/api';
import {
  User,
  UserListResponse,
  UserUpdate,
  UserRoleAssignmentRequest,
  UserRoleRemovalRequest,
  UserRoleUpdateRequest,
  AvailableRole,
  UserFilters,
  UserSortOptions
} from '@/types/users';

export const usersService = {
  /**
   * ユーザー一覧を取得
   */
  async getUsers(params: {
    page?: number;
    page_size?: number;
    filters?: UserFilters;
    sort?: UserSortOptions;
  }): Promise<UserListResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());
    
    if (params.filters) {
      if (params.filters.is_active !== undefined) {
        queryParams.append('is_active', params.filters.is_active.toString());
      }
      if (params.filters.is_email_verified !== undefined) {
        queryParams.append('is_email_verified', params.filters.is_email_verified.toString());
      }
      if (params.filters.role_ids && params.filters.role_ids.length > 0) {
        params.filters.role_ids.forEach(id => queryParams.append('role_ids', id.toString()));
      }
      if (params.filters.search) {
        queryParams.append('search', params.filters.search);
      }
    }
    
    if (params.sort) {
      if (params.sort.sort_by) queryParams.append('sort_by', params.sort.sort_by);
      if (params.sort.sort_order) queryParams.append('sort_order', params.sort.sort_order);
    }
    
    const response = await api.get<UserListResponse>(`/users/?${queryParams.toString()}`);
    return response.data;
  },

  /**
   * 特定のユーザー詳細を取得
   */
  async getUser(userId: number): Promise<User> {
    const response = await api.get<User>(`/users/${userId}`);
    return response.data;
  },

  /**
   * ユーザー情報を更新
   */
  async updateUser(userId: number, data: UserUpdate): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}`, data);
    return response.data;
  },

  /**
   * ユーザーにロールを割り当て
   */
  async assignRole(userId: number, data: UserRoleAssignmentRequest): Promise<User> {
    const response = await api.post<User>(`/users/${userId}/roles`, data);
    return response.data;
  },

  /**
   * ユーザーからロールを削除
   */
  async removeRole(userId: number, data: UserRoleRemovalRequest): Promise<User> {
    const response = await api.delete<User>(`/users/${userId}/roles`, { data });
    return response.data;
  },

  /**
   * ユーザーのロールを更新（一括設定）
   */
  async updateRoles(userId: number, data: UserRoleUpdateRequest): Promise<User> {
    const response = await api.put<User>(`/users/${userId}/roles`, data);
    return response.data;
  },

  /**
   * 利用可能なロール一覧を取得
   */
  async getAvailableRoles(): Promise<AvailableRole[]> {
    const response = await api.get<AvailableRole[]>('/users/roles/available');
    return response.data;
  }
};