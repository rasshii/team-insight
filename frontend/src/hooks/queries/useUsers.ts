import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useToast } from '@/components/ui/use-toast'
import { usersService } from '@/services/users.service'
import type { UserFilters, UserSortOptions, UserUpdate } from '@/types/users'

const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters?: UserFilters, sort?: UserSortOptions, page?: number) =>
    [...userKeys.lists(), { filters, sort, page }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: number) => [...userKeys.details(), id] as const,
}

export function useUsers(params?: {
  page?: number
  per_page?: number
  filters?: UserFilters
  sort?: UserSortOptions
}) {
  return useQuery({
    queryKey: userKeys.list(params?.filters, params?.sort, params?.page),
    queryFn: () => usersService.getUsers(params || {}),
  })
}

export function useUser(userId: number | null) {
  return useQuery({
    queryKey: userKeys.detail(userId!),
    queryFn: () => usersService.getUser(userId!),
    enabled: !!userId,
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserUpdate }) =>
      usersService.updateUser(userId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() })
      queryClient.invalidateQueries({ queryKey: userKeys.detail(data.id) })
      toast({
        title: '成功',
        description: 'ユーザー情報を更新しました',
      })
    },
    onError: (error: unknown) => {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'ユーザー情報の更新に失敗しました'
      toast({
        title: 'エラー',
        description: message,
        variant: 'destructive',
      })
    },
  })
}
