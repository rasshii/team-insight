import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersService } from '@/services/users.service';
import { toast } from '@/components/ui/use-toast';
import {
  UserUpdate,
  UserRoleAssignmentRequest,
  UserRoleRemovalRequest,
  UserRoleUpdateRequest,
  UserFilters,
  UserSortOptions
} from '@/types/users';

// Query Keys
const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters?: UserFilters, sort?: UserSortOptions, page?: number) => 
    [...userKeys.lists(), { filters, sort, page }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: number) => [...userKeys.details(), id] as const,
  roles: () => ['available-roles'] as const,
};

/**
 * ユーザー一覧を取得
 */
export function useUsers(params?: {
  page?: number;
  page_size?: number;
  filters?: UserFilters;
  sort?: UserSortOptions;
}) {
  return useQuery({
    queryKey: userKeys.list(params?.filters, params?.sort, params?.page),
    queryFn: () => usersService.getUsers(params || {}),
  });
}

/**
 * 特定のユーザー詳細を取得
 */
export function useUser(userId: number | null) {
  return useQuery({
    queryKey: userKeys.detail(userId!),
    queryFn: () => usersService.getUser(userId!),
    enabled: !!userId,
  });
}

/**
 * 利用可能なロール一覧を取得
 */
export function useAvailableRoles() {
  return useQuery({
    queryKey: userKeys.roles(),
    queryFn: () => usersService.getAvailableRoles(),
  });
}

/**
 * ユーザー情報を更新
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserUpdate }) =>
      usersService.updateUser(userId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.detail(data.id) });
      toast({
        title: "成功",
        description: "ユーザー情報を更新しました",
      });
    },
    onError: (error: any) => {
      toast({
        title: "エラー",
        description: error.response?.data?.detail || "ユーザー情報の更新に失敗しました",
        variant: "destructive",
      });
    },
  });
}

/**
 * ユーザーにロールを割り当て
 */
export function useAssignRole() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserRoleAssignmentRequest }) =>
      usersService.assignRole(userId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.detail(data.id) });
      toast({
        title: "成功",
        description: "ロールを割り当てました",
      });
    },
    onError: (error: any) => {
      toast({
        title: "エラー",
        description: error.response?.data?.detail || "ロールの割り当てに失敗しました",
        variant: "destructive",
      });
    },
  });
}

/**
 * ユーザーからロールを削除
 */
export function useRemoveRole() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserRoleRemovalRequest }) =>
      usersService.removeRole(userId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.detail(data.id) });
      toast({
        title: "成功",
        description: "ロールを削除しました",
      });
    },
    onError: (error: any) => {
      toast({
        title: "エラー",
        description: error.response?.data?.detail || "ロールの削除に失敗しました",
        variant: "destructive",
      });
    },
  });
}

/**
 * ユーザーのロールを更新（一括設定）
 */
export function useUpdateRoles() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserRoleUpdateRequest }) =>
      usersService.updateRoles(userId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.detail(data.id) });
      toast({
        title: "成功",
        description: "ロールを更新しました",
      });
    },
    onError: (error: any) => {
      toast({
        title: "エラー",
        description: error.response?.data?.detail || "ロールの更新に失敗しました",
        variant: "destructive",
      });
    },
  });
}