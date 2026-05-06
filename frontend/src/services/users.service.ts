import { apiClient as api } from '@/lib/api-client'
import type {
  User,
  UserListResponse,
  UserUpdate,
  UserFilters,
  UserSortOptions,
} from '@/types/users'

export const usersService = {
  /**
   * ユーザー一覧を取得 (Phase 0: 組織コンテキスト)
   */
  async getUsers(params: {
    page?: number
    per_page?: number
    filters?: UserFilters
    sort?: UserSortOptions
  }): Promise<UserListResponse> {
    const queryParams = new URLSearchParams()

    if (params.page) queryParams.append('page', params.page.toString())
    if (params.per_page)
      queryParams.append('per_page', params.per_page.toString())

    if (params.filters?.is_active !== undefined) {
      queryParams.append('is_active', params.filters.is_active.toString())
    }
    if (params.filters?.search) {
      queryParams.append('search', params.filters.search)
    }

    if (params.sort?.sort_by)
      queryParams.append('sort_by', params.sort.sort_by)
    if (params.sort?.sort_order)
      queryParams.append('sort_order', params.sort.sort_order)

    return await api.get<UserListResponse>(
      `/api/v1/users/?${queryParams.toString()}`
    )
  },

  async getUser(userId: number): Promise<User> {
    return await api.get<User>(`/api/v1/users/${userId}`)
  },

  async updateUser(userId: number, data: UserUpdate): Promise<User> {
    return await api.patch<User>(`/api/v1/users/${userId}`, data)
  },
}
