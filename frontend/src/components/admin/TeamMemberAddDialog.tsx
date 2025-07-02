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
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [role, setRole] = useState<TeamRole>(TeamRole.MEMBER)

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
    if (!selectedUserId) return

    try {
      await addMemberMutation.mutateAsync({
        user_id: selectedUserId,
        role,
      })
      
      // フォームをリセット
      setSelectedUserId(null)
      setRole(TeamRole.MEMBER)
      setSearchQuery('')
      onOpenChange(false)
    } catch (error) {
      // エラーはmutationのonErrorで処理される
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
            <Label>ユーザー選択</Label>
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
                        checked={selectedUserId === user.id}
                        onCheckedChange={(checked) =>
                          setSelectedUserId(checked ? user.id : null)
                        }
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
            disabled={addMemberMutation.isPending}
          >
            キャンセル
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedUserId || addMemberMutation.isPending}
          >
            {addMemberMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            追加
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}