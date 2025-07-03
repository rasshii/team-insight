'use client'

import { Loader2, AlertTriangle } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useRemoveTeamMember } from '@/hooks/queries/useTeams'
import { TeamMember } from '@/types/team'

interface TeamMemberRemoveDialogProps {
  teamId: number
  member: TeamMember
  isLastLeader: boolean
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TeamMemberRemoveDialog({
  teamId,
  member,
  isLastLeader,
  open,
  onOpenChange,
}: TeamMemberRemoveDialogProps) {
  const removeMemberMutation = useRemoveTeamMember(teamId)

  const handleRemove = async () => {
    try {
      await removeMemberMutation.mutateAsync(member.user_id)
      onOpenChange(false)
    } catch (error) {
      // エラーはmutationのonErrorで処理される
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            メンバー削除の確認
          </AlertDialogTitle>
          <AlertDialogDescription>
            <strong>{member.user.name}</strong>
            さんをチームから削除しようとしています。
          </AlertDialogDescription>
          <div className="mt-4 space-y-2">
            {isLastLeader && (
              <div className="text-destructive font-medium">
                このメンバーは最後のチームリーダーです。削除することはできません。
              </div>
            )}
            {!isLastLeader && (
              <div>この操作は取り消すことができません。本当に削除してもよろしいですか？</div>
            )}
          </div>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={removeMemberMutation.isPending}>
            キャンセル
          </AlertDialogCancel>
          {!isLastLeader && (
            <AlertDialogAction
              onClick={handleRemove}
              disabled={removeMemberMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {removeMemberMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              削除する
            </AlertDialogAction>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}