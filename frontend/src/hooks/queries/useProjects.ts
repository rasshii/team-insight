import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { projectService, type Project, type ProjectCreateRequest, type ProjectUpdateRequest } from '@/services/project.service'
import { useApiMutation, useDeleteMutation } from '@/hooks/useApiMutation'

/**
 * プロジェクト一覧を取得するフック
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
      console.log('Fetching projects with params:', params);
      const result = await projectService.getProjects(params);
      console.log('Projects service returned:', result);
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
        console.log('Sync success callback result:', result);
        // プロジェクト一覧を強制的に再取得
        await queryClient.refetchQueries({ queryKey: queryKeys.projects.all })
        console.log('Projects refetched');
      }
    }
  )
}