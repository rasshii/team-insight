/**
 * 組織関連の React Query フック (Phase 0)
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useToast } from '@/hooks/use-toast'
import { getApiErrorMessage } from '@/lib/api-client'
import { queryKeys } from '@/lib/react-query'
import {
  organizationService,
  type OrganizationCreateRequest,
  type OrganizationMemberCreateRequest,
  type OrganizationMemberUpdateRequest,
  type OrganizationUpdateRequest,
} from '@/services/organization.service'

export const useMyOrganizations = () =>
  useQuery({
    queryKey: queryKeys.organizations.mine,
    queryFn: () => organizationService.listMine(),
  })

export const useOrganization = (organizationId: number | null) =>
  useQuery({
    queryKey: queryKeys.organizations.detail(organizationId ?? 0),
    queryFn: () => organizationService.get(organizationId!),
    enabled: organizationId !== null,
  })

export const useUpdateOrganization = (organizationId: number) => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: OrganizationUpdateRequest) =>
      organizationService.update(organizationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.detail(organizationId),
      })
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations.mine })
      toast({ title: '組織情報を更新しました' })
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}

export const useOrganizationMembers = (organizationId: number | null) =>
  useQuery({
    queryKey: queryKeys.organizations.members(organizationId ?? 0),
    queryFn: () => organizationService.listMembers(organizationId!),
    enabled: organizationId !== null,
  })

export const useAddOrganizationMember = (organizationId: number) => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: OrganizationMemberCreateRequest) =>
      organizationService.addMember(organizationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.members(organizationId),
      })
      toast({ title: 'メンバーを追加しました' })
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}

export const useUpdateOrganizationMember = (organizationId: number) => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: number
      payload: OrganizationMemberUpdateRequest
    }) =>
      organizationService.updateMemberRole(organizationId, userId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.members(organizationId),
      })
      toast({ title: 'メンバーロールを更新しました' })
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}

export const useRemoveOrganizationMember = (organizationId: number) => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (userId: number) =>
      organizationService.removeMember(organizationId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.members(organizationId),
      })
      toast({ title: 'メンバーを削除しました' })
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}

// System Admin 用
export const useSystemOrganizations = () =>
  useQuery({
    queryKey: queryKeys.organizations.systemList,
    queryFn: () => organizationService.listAll(),
  })

export const useCreateOrganization = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (payload: OrganizationCreateRequest) =>
      organizationService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.systemList,
      })
      toast({ title: '組織を作成しました' })
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}

export const useDeleteOrganization = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (organizationId: number) =>
      organizationService.deleteOrganization(organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.organizations.systemList,
      })
      toast({ title: '組織を削除しました' })
    },
    onError: (error) => {
      toast({
        title: 'エラー',
        description: getApiErrorMessage(error),
        variant: 'destructive',
      })
    },
  })
}
