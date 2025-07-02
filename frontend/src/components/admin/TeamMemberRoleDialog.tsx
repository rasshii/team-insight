'use client'

import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useUpdateTeamMember } from '@/hooks/queries/useTeams'
import { TeamRole, TeamMember } from '@/types/team'

interface TeamMemberRoleDialogProps {
  teamId: number
  member: TeamMember
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TeamMemberRoleDialog({
  teamId,
  member,
  open,
  onOpenChange,
}: TeamMemberRoleDialogProps) {
  const [role, setRole] = useState<TeamRole>(member.role as TeamRole)

  const updateMemberMutation = useUpdateTeamMember(teamId, member.user_id)

  // メンバーが変更されたときに役割をリセット
  useEffect(() => {
    setRole(member.role as TeamRole)
  }, [member])

  const handleSubmit = async () => {
    if (role === member.role) {
      onOpenChange(false)
      return
    }

    try {
      await updateMemberMutation.mutateAsync({ role })
      onOpenChange(false)
    } catch (error) {
      // エラーはmutationのonErrorで処理される
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>メンバーの役割変更</DialogTitle>
          <DialogDescription>
            <strong>{member.user.name}</strong>さんのチーム内での役割を変更します
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label>現在の役割</Label>
            <p className="text-sm text-muted-foreground">
              {member.role === TeamRole.TEAM_LEADER
                ? 'チームリーダー'
                : 'メンバー'}
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">新しい役割</Label>
            <Select
              value={role}
              onValueChange={(value) => setRole(value as TeamRole)}
            >
              <SelectTrigger id="role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TeamRole.MEMBER}>メンバー</SelectItem>
                <SelectItem value={TeamRole.TEAM_LEADER}>
                  チームリーダー
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={updateMemberMutation.isPending}
          >
            キャンセル
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={updateMemberMutation.isPending || role === member.role}
          >
            {updateMemberMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            変更
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}