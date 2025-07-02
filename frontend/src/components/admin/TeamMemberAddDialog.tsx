'use client'

import { useState, useMemo } from 'react'
import { Loader2, Search } from 'lucide-react'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Checkbox } from '@/components/ui/checkbox'
import { useUsers } from '@/hooks/queries/useUsers'
import { useAddTeamMember } from '@/hooks/queries/useTeams'
import { TeamRole } from '@/types/team'

interface TeamMemberAddDialogProps {
  teamId: number
  existingMemberIds: number[]
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TeamMemberAddDialog({
  teamId,
  existingMemberIds,
  open,
  onOpenChange,
}: TeamMemberAddDialogProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([])
  const [role, setRole] = useState<TeamRole>(TeamRole.MEMBER)
  const [isAddingMembers, setIsAddingMembers] = useState(false)

  const { data: usersData, isLoading } = useUsers({
    page: 1,
    per_page: 100,
    is_active: true,
  })

  const addMemberMutation = useAddTeamMember(teamId)

  // 既存メンバーを除外したユーザーリスト
  const availableUsers = useMemo(() => {
    if (!usersData?.users) return []
    
    return usersData.users
      .filter((user) => !existingMemberIds.includes(user.id))
      .filter((user) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
          user.name.toLowerCase().includes(query) ||
          user.email?.toLowerCase().includes(query) ||
          user.user_id?.toLowerCase().includes(query)
        )
      })
  }, [usersData, existingMemberIds, searchQuery])

  const handleSubmit = async () => {
    if (selectedUserIds.length === 0) return

    setIsAddingMembers(true)
    
    try {
      // 選択されたユーザーを順番に追加
      for (const userId of selectedUserIds) {
        await addMemberMutation.mutateAsync({
          user_id: userId,
          role,
        })
      }
      
      // フォームをリセット
      setSelectedUserIds([])
      setRole(TeamRole.MEMBER)
      setSearchQuery('')
      onOpenChange(false)
    } catch (error) {
      // エラーはmutationのonErrorで処理される
    } finally {
      setIsAddingMembers(false)
    }
  }

  const toggleUserSelection = (userId: number) => {
    setSelectedUserIds(prev => {
      if (prev.includes(userId)) {
        return prev.filter(id => id !== userId)
      } else {
        return [...prev, userId]
      }
    })
  }

  const toggleAllUsers = () => {
    if (selectedUserIds.length === availableUsers.length) {
      setSelectedUserIds([])
    } else {
      setSelectedUserIds(availableUsers.map(user => user.id))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>メンバー追加</DialogTitle>
          <DialogDescription>
            チームに追加するユーザーを選択してください
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 検索フィールド */}
          <div className="space-y-2">
            <Label>ユーザー検索</Label>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="名前、メールアドレスで検索"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {/* ユーザー選択 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>ユーザー選択</Label>
              {availableUsers.length > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={toggleAllUsers}
                  className="h-auto px-2 py-1 text-xs"
                >
                  {selectedUserIds.length === availableUsers.length
                    ? 'すべて解除'
                    : 'すべて選択'}
                </Button>
              )}
            </div>
            <ScrollArea className="h-[200px] rounded-md border p-4">
              {isLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : availableUsers.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground">
                  追加可能なユーザーがいません
                </p>
              ) : (
                <div className="space-y-2">
                  {availableUsers.map((user) => (
                    <label
                      key={user.id}
                      className="flex items-center space-x-2 cursor-pointer hover:bg-accent p-2 rounded"
                    >
                      <Checkbox
                        checked={selectedUserIds.includes(user.id)}
                        onCheckedChange={() => toggleUserSelection(user.id)}
                      />
                      <div className="flex-1">
                        <div className="font-medium">{user.name}</div>
                        {user.email && (
                          <div className="text-sm text-muted-foreground">
                            {user.email}
                          </div>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </ScrollArea>
            {selectedUserIds.length > 0 && (
              <p className="text-sm text-muted-foreground">
                {selectedUserIds.length}人のユーザーを選択中
              </p>
            )}
          </div>

          {/* 役割選択 */}
          <div className="space-y-2">
            <Label>役割</Label>
            <Select
              value={role}
              onValueChange={(value) => setRole(value as TeamRole)}
            >
              <SelectTrigger>
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
            disabled={isAddingMembers}
          >
            キャンセル
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={selectedUserIds.length === 0 || isAddingMembers}
          >
            {isAddingMembers && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {isAddingMembers
              ? '追加中...'
              : selectedUserIds.length > 0
              ? `${selectedUserIds.length}人を追加`
              : '追加'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}