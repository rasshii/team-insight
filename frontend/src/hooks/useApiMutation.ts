import { useMutation, useQueryClient, type UseMutationOptions, type QueryKey } from '@tanstack/react-query'
import { useToast } from '@/hooks/use-toast'
import { isApiError } from '@/lib/error-handler'

export interface UseApiMutationOptions<TData = unknown, TError = unknown, TVariables = void> 
  extends Omit<UseMutationOptions<TData, TError, TVariables>, 'mutationFn'> {
  // 成功時のメッセージ設定
  successMessage?: string | ((data: TData) => string)
  // エラー時のメッセージ設定
  errorMessage?: string
  // 成功時の詳細メッセージ
  successDescription?: string | ((data: TData) => string)
  // 無効化するキャッシュキー
  invalidateQueries?: QueryKey[]
  // 更新するキャッシュキー
  setQueryData?: {
    queryKey: QueryKey
    updater: (data: TData) => any
  }[]
  // キャッシュから削除するキー
  removeQueries?: QueryKey[]
  // トースト通知を無効化
  disableToast?: boolean
  // 成功時の追加処理
  onSuccessCallback?: (data: TData) => void
  // エラー時の追加処理
  onErrorCallback?: (error: TError) => void
}

/**
 * API呼び出し用の共通ミューテーションフック
 * 
 * エラーハンドリング、トースト通知、キャッシュ管理を統一的に処理します
 * 
 * @example
 * ```tsx
 * const createProject = useApiMutation(
 *   (data: ProjectCreateRequest) => projectService.createProject(data),
 *   {
 *     successMessage: (project) => `${project.name}を作成しました`,
 *     invalidateQueries: [queryKeys.projects.all]
 *   }
 * )
 * ```
 */
export function useApiMutation<TData = unknown, TError = unknown, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: UseApiMutationOptions<TData, TError, TVariables>
) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const {
    successMessage,
    errorMessage = 'エラーが発生しました',
    successDescription,
    invalidateQueries = [],
    setQueryData = [],
    removeQueries = [],
    disableToast = false,
    onSuccessCallback,
    onErrorCallback,
    ...restOptions
  } = options || {}

  return useMutation<TData, TError, TVariables>({
    mutationFn,
    onSuccess: async (data, variables, context) => {
      // キャッシュの無効化
      for (const queryKey of invalidateQueries) {
        await queryClient.invalidateQueries({ queryKey })
      }

      // キャッシュの更新
      for (const { queryKey, updater } of setQueryData) {
        queryClient.setQueryData(queryKey, updater(data))
      }

      // キャッシュの削除
      for (const queryKey of removeQueries) {
        queryClient.removeQueries({ queryKey })
      }

      // 成功トースト
      if (!disableToast && successMessage) {
        const message = typeof successMessage === 'function' 
          ? successMessage(data) 
          : successMessage
        
        const description = successDescription 
          ? (typeof successDescription === 'function' 
              ? successDescription(data) 
              : successDescription)
          : undefined

        toast({
          title: message,
          description,
        })
      }

      // カスタムコールバック
      onSuccessCallback?.(data)

      // 元のonSuccessを呼び出し
      restOptions.onSuccess?.(data, variables, context)
    },
    onError: (error, variables, context) => {
      // エラートースト
      if (!disableToast) {
        let errorDetail = errorMessage
        
        // APIエラーの場合、詳細メッセージを取得
        if (isApiError(error)) {
          const apiError = error as any
          errorDetail = apiError.response?.data?.detail || errorMessage
        }

        toast({
          title: 'エラー',
          description: errorDetail,
          variant: 'destructive',
        })
      }

      // カスタムコールバック
      onErrorCallback?.(error)

      // 元のonErrorを呼び出し
      restOptions.onError?.(error, variables, context)
    },
    ...restOptions,
  })
}

/**
 * ページネーション付きミューテーションフック
 * 
 * ページネーションされたリストの更新に最適化されています
 */
export function usePaginatedMutation<TData = unknown, TError = unknown, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: UseApiMutationOptions<TData, TError, TVariables> & {
    // ページネーションキーのプレフィックス
    paginationKeyPrefix: QueryKey
  }
) {
  const queryClient = useQueryClient()
  
  return useApiMutation(mutationFn, {
    ...options,
    onSuccess: async (data, variables, context) => {
      // ページネーションされたすべてのキャッシュを無効化
      if (options?.paginationKeyPrefix) {
        await queryClient.invalidateQueries({ 
          queryKey: options.paginationKeyPrefix,
          exact: false,
        })
      }
      
      // 元のonSuccessを呼び出し
      options?.onSuccess?.(data, variables, context)
    },
  })
}

/**
 * 削除操作用のミューテーションフック
 * 
 * 削除確認ダイアログと組み合わせて使用することを想定
 */
export function useDeleteMutation<TData = unknown, TError = unknown, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: UseApiMutationOptions<TData, TError, TVariables> & {
    // 削除対象の名前（トーストメッセージ用）
    resourceName?: string
  }
) {
  const { resourceName = 'リソース' } = options || {}
  
  return useApiMutation(mutationFn, {
    successMessage: `${resourceName}を削除しました`,
    errorMessage: `${resourceName}の削除に失敗しました`,
    ...options,
  })
}