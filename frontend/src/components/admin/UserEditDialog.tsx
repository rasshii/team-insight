"use client";

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { User, AvailableRole } from '@/types/users';
import { useUpdateUser, useAssignRole, useRemoveRole, useAvailableRoles } from '@/hooks/queries/useUsers';

interface UserEditDialogProps {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UserEditDialog({ user, open, onOpenChange }: UserEditDialogProps) {
  const [name, setName] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [selectedRoles, setSelectedRoles] = useState<number[]>([]);
  
  const updateUserMutation = useUpdateUser();
  const assignRoleMutation = useAssignRole();
  const removeRoleMutation = useRemoveRole();
  const { data: availableRoles, isLoading: rolesLoading } = useAvailableRoles();
  
  const isLoading = updateUserMutation.isPending || assignRoleMutation.isPending || removeRoleMutation.isPending;

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setIsActive(user.is_active);
      setSelectedRoles(user.user_roles.map(ur => ur.role_id));
    } else {
      // ダイアログが閉じられたときに状態をリセット
      setName('');
      setIsActive(true);
      setSelectedRoles([]);
    }
  }, [user]);

  const handleSubmit = async () => {
    if (!user) return;

    try {
      // ユーザー情報を更新
      await updateUserMutation.mutateAsync({
        userId: user.id,
        data: { name, is_active: isActive }
      });

      // 現在のロールと新しいロールを比較
      const currentRoleIds = user.user_roles.map(ur => ur.role_id);
      const rolesToAdd = selectedRoles.filter(id => !currentRoleIds.includes(id));
      const rolesToRemove = user.user_roles.filter(ur => !selectedRoles.includes(ur.role_id));

      // ロールを追加
      if (rolesToAdd.length > 0) {
        await assignRoleMutation.mutateAsync({
          userId: user.id,
          data: {
            assignments: rolesToAdd.map(roleId => ({
              role_id: roleId,
              project_id: null
            }))
          }
        });
      }

      // ロールを削除
      if (rolesToRemove.length > 0) {
        await removeRoleMutation.mutateAsync({
          userId: user.id,
          data: {
            user_role_ids: rolesToRemove.map(ur => ur.id)
          }
        });
      }

      // 成功時のみダイアログを閉じる
      onOpenChange(false);
    } catch (error) {
      // エラーはuseMutationのonErrorで処理
      console.error('Failed to update user:', error);
    }
  };

  const handleRoleToggle = (roleId: number) => {
    setSelectedRoles(prev => 
      prev.includes(roleId)
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>ユーザー編集</DialogTitle>
          <DialogDescription>
            ユーザー情報とロールを編集します
          </DialogDescription>
        </DialogHeader>
        
        {user && (
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>メールアドレス</Label>
              <Input value={user.email || ''} disabled />
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
              <Label>ロール</Label>
              {rolesLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              ) : (
                <div className="space-y-2">
                  {availableRoles?.map((role) => (
                    <div key={role.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={`role-${role.id}`}
                        checked={selectedRoles.includes(role.id)}
                        onCheckedChange={() => handleRoleToggle(role.id)}
                      />
                      <Label
                        htmlFor={`role-${role.id}`}
                        className="text-sm font-normal cursor-pointer"
                      >
                        {role.name}
                        {role.description && (
                          <span className="text-xs text-muted-foreground ml-2">
                            {role.description}
                          </span>
                        )}
                      </Label>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="space-y-2">
              <Label>その他の情報</Label>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>Backlog ID: {user.backlog_id || 'なし'}</div>
                <div>登録日: {new Date(user.created_at).toLocaleDateString('ja-JP')}</div>
                {user.last_login_at && (
                  <div>最終ログイン: {new Date(user.last_login_at).toLocaleDateString('ja-JP')}</div>
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
  );
}