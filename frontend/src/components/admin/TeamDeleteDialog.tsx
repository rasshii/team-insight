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
import { useDeleteTeam } from '@/hooks/queries/useTeams'
import { Team } from '@/types/team'

interface TeamDeleteDialogProps {
  team: Team
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TeamDeleteDialog({ team, open, onOpenChange }: TeamDeleteDialogProps) {
  const deleteTeamMutation = useDeleteTeam()

  const handleDelete = async () => {
    try {
      await deleteTeamMutation.mutateAsync(team.id)
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
            チームの削除確認
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-2">
            チーム「<strong>{team.name}</strong>」を削除しようとしています。
            この操作は取り消すことができません。チームに関連するすべてのデータが削除されます。
          </AlertDialogDescription>
          <div className="mt-4 text-destructive font-medium">
            本当に削除してもよろしいですか？
          </div>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteTeamMutation.isPending}>
            キャンセル
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deleteTeamMutation.isPending}
            className="bg-destructive hover:bg-destructive/90"
          >
            {deleteTeamMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            削除する
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}