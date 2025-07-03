'use client'

import { useState } from 'react'
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
import { useCreateTeam } from '@/hooks/queries/useTeams'

interface TeamCreateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TeamCreateDialog({ open, onOpenChange }: TeamCreateDialogProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  
  const createTeamMutation = useCreateTeam()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name.trim()) {
      return
    }

    try {
      await createTeamMutation.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
      })
      
      // フォームをリセット
      setName('')
      setDescription('')
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
            <DialogTitle>新規チーム作成</DialogTitle>
            <DialogDescription>
              新しいチームを作成します。チーム名は必須です。
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">チーム名 *</Label>
              <Input
                id="name"
                placeholder="例: フロントエンドチーム"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={createTeamMutation.isPending}
                required
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="description">説明</Label>
              <Textarea
                id="description"
                placeholder="チームの説明を入力してください"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={createTeamMutation.isPending}
                rows={3}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createTeamMutation.isPending}
            >
              キャンセル
            </Button>
            <Button
              type="submit"
              disabled={createTeamMutation.isPending || !name.trim()}
            >
              {createTeamMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              作成
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}