import { apiClient } from '@/lib/api-client'

// タスクの型定義
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED'

export interface Task {
  id: number
  backlog_id: number
  backlog_key: string
  title: string
  description?: string
  status: TaskStatus
  priority?: number
  issue_type_id?: number
  issue_type_name?: string
  project_id?: number
  assignee_id?: number
  reporter_id?: number
  estimated_hours?: number
  actual_hours?: number
  start_date?: string
  due_date?: string
  completed_date?: string
  milestone_id?: number
  milestone_name?: string
  category_names?: string
  version_names?: string
  created_at: string
  updated_at: string
}

export interface TaskListResponse {
  tasks: Task[]
  total: number
  page: number
  per_page: number
}

export interface TaskCreateRequest {
  title: string
  description?: string
  status?: TaskStatus
  priority?: number
  project_id?: number
  assignee_id?: number
  estimated_hours?: number
  start_date?: string
  due_date?: string
}

export interface TaskUpdateRequest {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: number
  assignee_id?: number
  estimated_hours?: number
  actual_hours?: number
  start_date?: string
  due_date?: string
  completed_date?: string
}

export interface TaskFilterParams {
  page?: number
  per_page?: number
  project_id?: number
  assignee_id?: number
  status?: TaskStatus
  search?: string
  start_date_from?: string
  start_date_to?: string
  due_date_from?: string
  due_date_to?: string
  sort_by?: 'created_at' | 'updated_at' | 'due_date' | 'priority'
  order?: 'asc' | 'desc'
}

/**
 * タスク関連のAPIサービス
 */
export const taskService = {
  /**
   * タスク一覧を取得
   */
  async getTasks(params?: TaskFilterParams): Promise<TaskListResponse> {
    return await apiClient.get('/api/v1/tasks/', { params })
  },

  /**
   * タスク詳細を取得
   */
  async getTask(taskId: string | number): Promise<Task> {
    return await apiClient.get(`/api/v1/tasks/${taskId}/`)
  },

  /**
   * タスクを作成
   */
  async createTask(data: TaskCreateRequest): Promise<Task> {
    return await apiClient.post('/api/v1/tasks/', data)
  },

  /**
   * タスクを更新
   */
  async updateTask(taskId: string | number, data: TaskUpdateRequest): Promise<Task> {
    return await apiClient.put(`/api/v1/tasks/${taskId}/`, data)
  },

  /**
   * タスクを削除
   */
  async deleteTask(taskId: string | number): Promise<void> {
    return await apiClient.delete(`/api/v1/tasks/${taskId}/`)
  },

  /**
   * プロジェクトのタスクを取得
   */
  async getTasksByProject(projectId: string | number, params?: Omit<TaskFilterParams, 'project_id'>): Promise<TaskListResponse> {
    return await apiClient.get('/api/v1/tasks/', { 
      params: { ...params, project_id: projectId } 
    })
  },

  /**
   * ユーザーのタスクを取得
   */
  async getTasksByUser(userId: string | number, params?: Omit<TaskFilterParams, 'assignee_id'>): Promise<TaskListResponse> {
    return await apiClient.get('/api/v1/tasks/', { 
      params: { ...params, assignee_id: userId } 
    })
  },

  /**
   * ユーザーのタスクを同期
   */
  async syncUserTasks(projectId?: string | number): Promise<{
    success: boolean
    created: number
    updated: number
    total: number
  }> {
    const endpoint = projectId 
      ? `/api/v1/sync/tasks/user/?project_id=${projectId}`
      : '/api/v1/sync/tasks/user/'
    return await apiClient.post(endpoint)
  },

  /**
   * プロジェクトのタスクを同期
   */
  async syncProjectTasks(projectId: string | number): Promise<{
    success: boolean
    created: number
    updated: number
    total: number
  }> {
    return await apiClient.post(`/api/v1/sync/tasks/${projectId}/`)
  },
}