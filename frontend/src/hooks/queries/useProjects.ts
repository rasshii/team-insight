/**
 * @fileoverview プロジェクト関連のReact Queryフック
 *
 * プロジェクトのCRUD操作とタスク同期をReact Queryで管理するカスタムフック集です。
 * プロジェクト一覧・詳細取得、作成・更新・削除、メンバー管理、Backlog同期などの機能を提供します。
 *
 * @module useProjectsQueries
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { projectService, type Project, type ProjectCreateRequest, type ProjectUpdateRequest } from '@/services/project.service'
import { useApiMutation, useDeleteMutation } from '@/hooks/useApiMutation'

/**
 * プロジェクト一覧を取得するフック
 *
 * ユーザーがアクセス可能な全プロジェクトの一覧をReact Queryで取得します。
 * 検索、ステータスフィルター、ページネーションをサポートします。
 *
 * @param {Object} [params] - クエリパラメータ
 * @param {number} [params.page] - ページ番号（1から開始）
 * @param {number} [params.per_page] - 1ページあたりの件数
 * @param {string} [params.search] - 検索キーワード（プロジェクト名で検索）
 * @param {'active' | 'archived'} [params.status] - ステータスフィルター
 * @returns {UseQueryResult<ProjectListResponse>} React Queryの結果オブジェクト
 *
 * @example
 * ```tsx
 * function ProjectList() {
 *   const { data, isLoading } = useProjects({ status: 'active' });
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <ul>
 *       {data.projects.map(project => (
 *         <li key={project.id}>{project.name}</li>
 *       ))}
 *     </ul>
 *   );
 * }
 * ```
 *
 * @remarks
 * - staleTime: 5分（データの鮮度保証期間）
 * - パラメータが変更されると自動的に再取得されます
 *
 * @see {@link projectService.getProjects} - プロジェクト一覧取得API
 * @see {@link queryKeys.projects.list} - React Queryのクエリキー
 */
export const useProjects = (params?: {
  page?: number
  per_page?: number
  search?: string
  status?: 'active' | 'archived'
}) => {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: async () => {
      const result = await projectService.getProjects(params);
      return result;
    },
    staleTime: 5 * 60 * 1000, // 5分
  })
}

/**
 * プロジェクト詳細を取得するフック
 */
export const useProject = (projectId: string | number | null) => {
  return useQuery({
    queryKey: queryKeys.projects.detail(projectId!),
    queryFn: () => projectService.getProject(projectId!),
    enabled: !!projectId,
  })
}

/**
 * プロジェクトメンバーを取得するフック
 */
export const useProjectMembers = (projectId: string | number | null) => {
  return useQuery({
    queryKey: queryKeys.projects.members(projectId!),
    queryFn: () => projectService.getProjectMembers(projectId!),
    enabled: !!projectId,
  })
}

/**
 * プロジェクトを作成するミューテーションフック
 */
export const useCreateProject = () => {
  return useApiMutation(
    (data: ProjectCreateRequest) => projectService.createProject(data),
    {
      successMessage: (project) => 'プロジェクトを作成しました',
      successDescription: (project) => `${project.name}が正常に作成されました。`,
      errorMessage: 'プロジェクトの作成に失敗しました。',
      invalidateQueries: [queryKeys.projects.all],
    }
  )
}

/**
 * プロジェクトを更新するミューテーションフック
 */
export const useUpdateProject = () => {
  return useApiMutation(
    ({ projectId, data }: { projectId: string | number; data: ProjectUpdateRequest }) => 
      projectService.updateProject(projectId, data),
    {
      successMessage: (project) => 'プロジェクトを更新しました',
      successDescription: (project) => `${project.name}が正常に更新されました。`,
      errorMessage: 'プロジェクトの更新に失敗しました。',
      invalidateQueries: [queryKeys.projects.all],
      setQueryData: [
        {
          queryKey: (project: Project) => queryKeys.projects.detail(project.id),
          updater: (project) => project,
        },
      ],
    }
  )
}

/**
 * プロジェクトを削除するミューテーションフック
 */
export const useDeleteProject = () => {
  const queryClient = useQueryClient()
  
  return useDeleteMutation(
    (projectId: string | number) => projectService.deleteProject(projectId),
    {
      resourceName: 'プロジェクト',
      invalidateQueries: [queryKeys.projects.all],
      onSuccessCallback: (_, projectId) => {
        // キャッシュから削除
        queryClient.removeQueries({ queryKey: queryKeys.projects.detail(projectId) })
      },
    }
  )
}

/**
 * プロジェクトのタスクを同期するミューテーションフック
 */
export const useSyncProjectTasks = () => {
  const queryClient = useQueryClient()
  
  return useApiMutation(
    (projectId: string | number) => projectService.syncProjectTasks(projectId),
    {
      successMessage: '同期が完了しました',
      successDescription: (result) => `新規: ${result.created}件、更新: ${result.updated}件、合計: ${result.total}件`,
      errorMessage: 'タスクの同期に失敗しました。',
      onSuccessCallback: (_, projectId) => {
        // タスク関連のキャッシュを無効化
        queryClient.invalidateQueries({ queryKey: queryKeys.tasks.byProject(projectId) })
      },
    }
  )
}

/**
 * すべてのプロジェクトを同期するミューテーションフック
 *
 * Backlogから全プロジェクトを同期し、データベースに保存します。
 * 同期完了後、プロジェクト一覧を自動的に再取得します。
 *
 * @returns {UseMutationResult} React Queryのミューテーション結果オブジェクト
 *
 * @example
 * ```tsx
 * function SyncProjectsButton() {
 *   const syncMutation = useSyncAllProjects();
 *
 *   return (
 *     <button
 *       onClick={() => syncMutation.mutate()}
 *       disabled={syncMutation.isPending}
 *     >
 *       {syncMutation.isPending ? '同期中...' : 'プロジェクトを同期'}
 *     </button>
 *   );
 * }
 * ```
 *
 * @remarks
 * - 成功時の処理:
 *   1. 成功メッセージをトースト表示（新規/更新/合計件数）
 *   2. プロジェクト一覧とBacklog同期状態のキャッシュを無効化
 *   3. プロジェクト一覧を強制的に再取得
 * - 管理者またはプロジェクトリーダーのみ実行可能
 *
 * @see {@link projectService.syncAllProjects} - プロジェクト同期API
 * @see {@link useApiMutation} - ミューテーション共通処理ラッパー
 */
export const useSyncAllProjects = () => {
  const queryClient = useQueryClient()
  
  return useApiMutation(
    () => projectService.syncAllProjects(),
    {
      successMessage: '同期が完了しました',
      successDescription: (result) => {
        // レスポンスがラップされている場合とそうでない場合を処理
        const data = result.data || result
        return `新規: ${data.created}件、更新: ${data.updated}件、合計: ${data.total}件`
      },
      errorMessage: 'プロジェクトの同期に失敗しました。',
      invalidateQueries: [queryKeys.projects.all, queryKeys.sync.status],
      onSuccessCallback: async (result) => {
        // プロジェクト一覧を強制的に再取得
        await queryClient.refetchQueries({ queryKey: queryKeys.projects.all })
      }
    }
  )
}