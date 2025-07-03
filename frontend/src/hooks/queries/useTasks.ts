import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { taskService, type Task, type TaskCreateRequest, type TaskUpdateRequest, type TaskFilterParams } from '@/services/task.service'
import { useToast } from '@/hooks/use-toast'

/**
 * タスク一覧を取得するフック
 */
export const useTasks = (params?: TaskFilterParams) => {
  return useQuery({
    queryKey: queryKeys.tasks.list(params),
    queryFn: () => taskService.getTasks(params),
    staleTime: 3 * 60 * 1000, // 3分
  })
}

/**
 * タスク詳細を取得するフック
 */
export const useTask = (taskId: string | number | null) => {
  return useQuery({
    queryKey: queryKeys.tasks.detail(taskId!),
    queryFn: () => taskService.getTask(taskId!),
    enabled: !!taskId,
  })
}

/**
 * プロジェクトのタスクを取得するフック
 */
export const useProjectTasks = (projectId: string | number | null, params?: Omit<TaskFilterParams, 'project_id'>) => {
  return useQuery({
    queryKey: queryKeys.tasks.byProject(projectId!),
    queryFn: () => taskService.getTasksByProject(projectId!, params),
    enabled: !!projectId,
    staleTime: 3 * 60 * 1000, // 3分
  })
}

/**
 * ユーザーのタスクを取得するフック
 */
export const useUserTasks = (userId: string | number | null, params?: Omit<TaskFilterParams, 'assignee_id'>) => {
  return useQuery({
    queryKey: queryKeys.tasks.byUser(userId!),
    queryFn: () => taskService.getTasksByUser(userId!, params),
    enabled: !!userId,
    staleTime: 3 * 60 * 1000, // 3分
  })
}

/**
 * タスクを作成するミューテーションフック
 */
export const useCreateTask = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: TaskCreateRequest) => taskService.createTask(data),
    onSuccess: (newTask) => {
      // タスクリストのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      
      // プロジェクトのタスクリストも無効化
      if (newTask.project_id) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.tasks.byProject(newTask.project_id) 
        })
      }
      
      toast({
        title: 'タスクを作成しました',
        description: `${newTask.title}が正常に作成されました。`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'タスクの作成に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * タスクを更新するミューテーションフック
 */
export const useUpdateTask = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string | number; data: TaskUpdateRequest }) => 
      taskService.updateTask(taskId, data),
    onSuccess: (updatedTask) => {
      // 特定のタスクのキャッシュを更新
      queryClient.setQueryData(
        queryKeys.tasks.detail(updatedTask.id),
        updatedTask
      )
      
      // タスクリストのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      
      // プロジェクトのタスクリストも無効化
      if (updatedTask.project_id) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.tasks.byProject(updatedTask.project_id) 
        })
      }
      
      toast({
        title: 'タスクを更新しました',
        description: `${updatedTask.title}が正常に更新されました。`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'タスクの更新に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * タスクを削除するミューテーションフック
 */
export const useDeleteTask = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (taskId: string | number) => taskService.deleteTask(taskId),
    onSuccess: (_, deletedTaskId) => {
      // タスクのキャッシュを削除
      queryClient.removeQueries({ queryKey: queryKeys.tasks.detail(deletedTaskId) })
      
      // タスクリストのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      
      toast({
        title: 'タスクを削除しました',
        description: 'タスクが正常に削除されました。',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'エラー',
        description: error.response?.data?.detail || 'タスクの削除に失敗しました。',
        variant: 'destructive',
      })
    },
  })
}

/**
 * ユーザーのタスクを同期するミューテーションフック
 */
export const useSyncUserTasks = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (projectId?: string | number) => taskService.syncUserTasks(projectId),
    onSuccess: (result) => {
      // タスク関連のすべてのキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      
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
 * プロジェクトのタスクを同期するミューテーションフック
 */
export const useSyncProjectTasks = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (projectId: string | number) => taskService.syncProjectTasks(projectId),
    onSuccess: (result, projectId) => {
      // プロジェクトのタスクキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.byProject(projectId) })
      
      // 全体のタスクリストも無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      
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