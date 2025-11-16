/**
 * @fileoverview プロジェクト管理APIサービス
 *
 * Backlogプロジェクトの一覧取得、詳細取得、CRUD操作、メンバー管理、
 * タスク同期などのプロジェクト関連機能を提供します。
 *
 * @module projectService
 */

import { apiClient } from '@/lib/api-client'

/**
 * プロジェクトの型定義
 *
 * Backlogプロジェクトの基本情報を表します。
 */
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
 * Backlogプロジェクトの管理とタスク同期機能を提供します。
 * React Queryと組み合わせて使用することで、効率的なデータフェッチを実現します。
 *
 * ## 主要機能
 * - プロジェクト一覧・詳細取得
 * - プロジェクト作成・更新・削除
 * - プロジェクトメンバー一覧取得
 * - Backlogとのタスク同期
 *
 * @see {@link apiClient} - 全APIリクエストで使用する共通クライアント
 */
export const projectService = {
  /**
   * プロジェクト一覧を取得
   *
   * ユーザーがアクセス可能な全プロジェクトの一覧を取得します。
   * 検索、ステータスフィルター、ページネーションをサポートします。
   *
   * @param {Object} [params] - クエリパラメータ
   * @param {number} [params.page] - ページ番号（1から開始）
   * @param {number} [params.per_page] - 1ページあたりの件数
   * @param {string} [params.search] - 検索キーワード（プロジェクト名で検索）
   * @param {'active' | 'archived'} [params.status] - ステータスフィルター
   * @returns {Promise<ProjectListResponse>} プロジェクト一覧と総数
   * @throws {AxiosError} APIリクエストが失敗した場合
   *
   * @example
   * ```typescript
   * // アクティブなプロジェクトのみ取得
   * const { projects } = await projectService.getProjects({ status: 'active' });
   *
   * // 名前で検索
   * const result = await projectService.getProjects({ search: 'Team' });
   * ```
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