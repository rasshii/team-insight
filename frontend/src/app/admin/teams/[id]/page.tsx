'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Plus, Shield, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useTeam } from '@/hooks/queries/useTeams'
import { TeamMemberAddDialog } from '@/components/admin/TeamMemberAddDialog'
import { TeamMemberRoleDialog } from '@/components/admin/TeamMemberRoleDialog'
import { TeamMemberRemoveDialog } from '@/components/admin/TeamMemberRemoveDialog'
import { TeamRole, TeamMember } from '@/types/team'
import { MoreHorizontal } from 'lucide-react'

export default function TeamDetailPage() {
  const params = useParams()
  const router = useRouter()
  const teamId = Number(params.id)
  
  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false)
  const [editingMember, setEditingMember] = useState<TeamMember | null>(null)
  const [removingMember, setRemovingMember] = useState<TeamMember | null>(null)

  const { data: team, isLoading, error } = useTeam(teamId)

  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              チーム情報の取得に失敗しました
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64 mt-2" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!team) {
    return null
  }

  const getRoleBadge = (role: string) => {
    if (role === TeamRole.TEAM_LEADER) {
      return (
        <Badge variant="default" className="gap-1">
          <Shield className="h-3 w-3" />
          チームリーダー
        </Badge>
      )
    }
    return (
      <Badge variant="secondary" className="gap-1">
        <User className="h-3 w-3" />
        メンバー
      </Badge>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/admin/teams')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{team.name}</h1>
          {team.description && (
            <p className="text-muted-foreground mt-1">{team.description}</p>
          )}
        </div>
      </div>

      {/* 統計情報 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">メンバー数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{team.member_count}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              アクティブタスク
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{team.active_tasks_count}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              今月の完了タスク
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {team.completed_tasks_this_month}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* メンバー一覧 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>チームメンバー</CardTitle>
              <CardDescription>
                このチームに所属するメンバーを管理します
              </CardDescription>
            </div>
            <Button onClick={() => setIsAddMemberOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              メンバー追加
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名前</TableHead>
                  <TableHead>メールアドレス</TableHead>
                  <TableHead>役割</TableHead>
                  <TableHead>参加日</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {team.members.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8">
                      <p className="text-muted-foreground">
                        メンバーがいません
                      </p>
                    </TableCell>
                  </TableRow>
                ) : (
                  team.members.map((member) => (
                    <TableRow key={member.id}>
                      <TableCell className="font-medium">
                        {member.user.name}
                      </TableCell>
                      <TableCell>{member.user.email || '-'}</TableCell>
                      <TableCell>{getRoleBadge(member.role)}</TableCell>
                      <TableCell>
                        {new Date(member.joined_at).toLocaleDateString('ja-JP')}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">メニューを開く</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>操作</DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => setEditingMember(member)}
                            >
                              役割を変更
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => setRemovingMember(member)}
                              className="text-destructive"
                              disabled={
                                member.role === TeamRole.TEAM_LEADER &&
                                team.members.filter(
                                  (m) => m.role === TeamRole.TEAM_LEADER
                                ).length === 1
                              }
                            >
                              チームから削除
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* メンバー追加ダイアログ */}
      <TeamMemberAddDialog
        teamId={teamId}
        existingMemberIds={team.members.map((m) => m.user_id)}
        open={isAddMemberOpen}
        onOpenChange={setIsAddMemberOpen}
      />

      {/* メンバー役割変更ダイアログ */}
      {editingMember && (
        <TeamMemberRoleDialog
          teamId={teamId}
          member={editingMember}
          open={!!editingMember}
          onOpenChange={(open) => !open && setEditingMember(null)}
        />
      )}

      {/* メンバー削除確認ダイアログ */}
      {removingMember && (
        <TeamMemberRemoveDialog
          teamId={teamId}
          member={removingMember}
          isLastLeader={
            removingMember.role === TeamRole.TEAM_LEADER &&
            team.members.filter((m) => m.role === TeamRole.TEAM_LEADER)
              .length === 1
          }
          open={!!removingMember}
          onOpenChange={(open) => !open && setRemovingMember(null)}
        />
      )}
    </div>
  )
}