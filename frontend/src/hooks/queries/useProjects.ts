import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { projectService, type Project, type ProjectCreateRequest, type ProjectUpdateRequest } from '@/services/project.service'
import { useToast } from '@/hooks/use-toast'

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
    queryFn: () => projectService.getProjects(params),
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
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: ProjectCreateRequest) => projectService.createProject(data),
    onSuccess: (newProject) => {
      // プロジェクトリストのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      
      toast({
        title: 'プロジェクトを作成しました',
        description: `${newProject.name}が正常に作成されました。`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'プロジェクトの作成に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * プロジェクトを更新するミューテーションフック
 */
export const useUpdateProject = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string | number; data: ProjectUpdateRequest }) => 
      projectService.updateProject(projectId, data),
    onSuccess: (updatedProject) => {
      // 特定のプロジェクトのキャッシュを更新
      queryClient.setQueryData(
        queryKeys.projects.detail(updatedProject.id),
        updatedProject
      )
      
      // プロジェクトリストのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      
      toast({
        title: 'プロジェクトを更新しました',
        description: `${updatedProject.name}が正常に更新されました。`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'プロジェクトの更新に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * プロジェクトを削除するミューテーションフック
 */
export const useDeleteProject = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (projectId: string | number) => projectService.deleteProject(projectId),
    onSuccess: (_, deletedProjectId) => {
      // プロジェクトのキャッシュを削除
      queryClient.removeQueries({ queryKey: queryKeys.projects.detail(deletedProjectId) })
      
      // プロジェクトリストのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      
      toast({
        title: 'プロジェクトを削除しました',
        description: 'プロジェクトが正常に削除されました。',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'プロジェクトの削除に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * プロジェクトのタスクを同期するミューテーションフック
 */
export const useSyncProjectTasks = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (projectId: string | number) => projectService.syncProjectTasks(projectId),
    onSuccess: (result, projectId) => {
      // タスク関連のキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.byProject(projectId) })
      
      toast({
        title: '同期が完了しました',
        description: `新規: ${result.created}件、更新: ${result.updated}件、合計: ${result.total}件`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'タスクの同期に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * すべてのプロジェクトを同期するミューテーションフック
 */
export const useSyncAllProjects = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => projectService.syncAllProjects(),
    onSuccess: (result) => {
      // プロジェクト関連のすべてのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      
      toast({
        title: '同期が完了しました',
        description: `新規: ${result.created}件、更新: ${result.updated}件、合計: ${result.total}件`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'プロジェクトの同期に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}