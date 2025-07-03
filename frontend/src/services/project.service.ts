import { apiClient } from '@/lib/api-client'

// プロジェクトの型定義
export interface Project {
  id: number
  backlog_id: number
  name: string
  project_key: string
  description?: string
  status: 'active' | 'archived'
  created_at: string
  updated_at: string
}

export interface ProjectMember {
  id: number
  backlog_id: number
  user_id?: string
  name: string
  email?: string
  is_active: boolean
}

export interface ProjectListResponse {
  projects: Project[]
  total: number
  page: number
  per_page: number
}

export interface ProjectCreateRequest {
  name: string
  project_key: string
  description?: string
}

export interface ProjectUpdateRequest {
  name?: string
  description?: string
  status?: 'active' | 'archived'
}

/**
 * プロジェクト関連のAPIサービス
 * 
 * React Queryと組み合わせて使用するためのシンプルな関数群
 */
export const projectService = {
  /**
   * プロジェクト一覧を取得
   */
  async getProjects(params?: {
    page?: number
    per_page?: number
    search?: string
    status?: 'active' | 'archived'
  }): Promise<ProjectListResponse> {
    const response = await apiClient.get('/api/v1/projects/', { params })
    // Handle wrapped response from backend
    return response.data || response
  },

  /**
   * プロジェクト詳細を取得
   */
  async getProject(projectId: string | number): Promise<Project> {
    return await apiClient.get(`/api/v1/projects/${projectId}/`)
  },

  /**
   * プロジェクトを作成
   */
  async createProject(data: ProjectCreateRequest): Promise<Project> {
    return await apiClient.post('/api/v1/projects/', data)
  },

  /**
   * プロジェクトを更新
   */
  async updateProject(projectId: string | number, data: ProjectUpdateRequest): Promise<Project> {
    return await apiClient.put(`/api/v1/projects/${projectId}/`, data)
  },

  /**
   * プロジェクトを削除
   */
  async deleteProject(projectId: string | number): Promise<void> {
    return await apiClient.delete(`/api/v1/projects/${projectId}/`)
  },

  /**
   * プロジェクトメンバー一覧を取得
   */
  async getProjectMembers(projectId: string | number): Promise<ProjectMember[]> {
    return await apiClient.get(`/api/v1/projects/${projectId}/members/`)
  },

  /**
   * プロジェクトからタスクを同期
   */
  async syncProjectTasks(projectId: string | number): Promise<{
    success: boolean
    created: number
    updated: number
    total: number
  }> {
    const response = await apiClient.post(`/api/v1/sync/project/${projectId}/tasks`)
    // Handle wrapped response from backend
    return response.data || response
  },

  /**
   * すべてのプロジェクトを同期
   */
  async syncAllProjects(): Promise<{
    success: boolean
    created: number
    updated: number
    total: number
  }> {
    const response = await apiClient.post('/api/v1/sync/projects/all')
    // Handle wrapped response from backend
    return response.data || response
  },
}