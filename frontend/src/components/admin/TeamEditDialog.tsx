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
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useUpdateTeam } from '@/hooks/queries/useTeams'
import { Team } from '@/types/team'

interface TeamEditDialogProps {
  team: Team
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TeamEditDialog({ team, open, onOpenChange }: TeamEditDialogProps) {
  const [name, setName] = useState(team.name)
  const [description, setDescription] = useState(team.description || '')
  
  const updateTeamMutation = useUpdateTeam(team.id)

  // チームが変更されたときにフォームをリセット
  useEffect(() => {
    setName(team.name)
    setDescription(team.description || '')
  }, [team])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name.trim()) {
      return
    }

    try {
      await updateTeamMutation.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
      })
      
      onOpenChange(false)
    } catch (error) {
      // エラーはmutationのonErrorで処理される
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>チーム編集</DialogTitle>
            <DialogDescription>
              チーム情報を編集します
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">チーム名 *</Label>
              <Input
                id="edit-name"
                placeholder="例: フロントエンドチーム"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={updateTeamMutation.isPending}
                required
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="edit-description">説明</Label>
              <Textarea
                id="edit-description"
                placeholder="チームの説明を入力してください"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={updateTeamMutation.isPending}
                rows={3}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateTeamMutation.isPending}
            >
              キャンセル
            </Button>
            <Button
              type="submit"
              disabled={updateTeamMutation.isPending || !name.trim()}
            >
              {updateTeamMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              更新
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}