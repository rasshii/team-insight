'use client'

import { Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { useUpdateUser } from '@/hooks/queries/useUsers'
import type { User } from '@/types/users'

interface UserEditDialogProps {
  user: User | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * ユーザー基本情報編集ダイアログ (Phase 0: ロール編集は組織メンバーシップ画面に分離)
 */
export function UserEditDialog({
  user,
  open,
  onOpenChange,
}: UserEditDialogProps) {
  const [name, setName] = useState('')
  const [isActive, setIsActive] = useState(true)

  const updateUserMutation = useUpdateUser()
  const isLoading = updateUserMutation.isPending

  useEffect(() => {
    if (user) {
      setName(user.name ?? '')
      setIsActive(user.is_active)
    } else {
      setName('')
      setIsActive(true)
    }
  }, [user])

  const handleSubmit = async () => {
    if (!user) return
    try {
      await updateUserMutation.mutateAsync({
        userId: user.id,
        data: { name, is_active: isActive },
      })
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to update user:', error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>ユーザー編集</DialogTitle>
          <DialogDescription>
            ユーザー基本情報を編集します。組織内ロールは組織メンバー管理画面で変更してください。
          </DialogDescription>
        </DialogHeader>

        {user && (
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>メールアドレス</Label>
              <Input value={user.email ?? ''} disabled />
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">名前</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="ユーザー名を入力"
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="is-active">アカウント状態</Label>
              <div className="flex items-center space-x-2">
                <Switch
                  id="is-active"
                  checked={isActive}
                  onCheckedChange={setIsActive}
                />
                <span className="text-sm text-muted-foreground">
                  {isActive ? 'ログイン可' : 'ログイン不可'}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>所属組織</Label>
              {user.organizations.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  どの組織にも所属していません
                </p>
              ) : (
                <ul className="space-y-1 text-sm">
                  {user.organizations.map((m) => (
                    <li
                      key={m.organization_id}
                      className="flex justify-between"
                    >
                      <span>{m.organization_name}</span>
                      <span className="text-muted-foreground">{m.role}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="space-y-2">
              <Label>その他の情報</Label>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>
                  登録日:{' '}
                  {new Date(user.created_at).toLocaleDateString('ja-JP')}
                </div>
                {user.last_login_at && (
                  <div>
                    最終ログイン:{' '}
                    {new Date(user.last_login_at).toLocaleDateString('ja-JP')}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            キャンセル
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
