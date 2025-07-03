'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { MoreHorizontal, Edit, Trash2, Users } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'
import { Team, TeamWithStats } from '@/types/team'
import { TeamEditDialog } from './TeamEditDialog'
import { TeamDeleteDialog } from './TeamDeleteDialog'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'

interface TeamListTableProps {
  teams: (Team | TeamWithStats)[]
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
}

export function TeamListTable({
  teams,
  total,
  page,
  pageSize,
  onPageChange,
}: TeamListTableProps) {
  const router = useRouter()
  const [editingTeam, setEditingTeam] = useState<Team | null>(null)
  const [deletingTeam, setDeletingTeam] = useState<Team | null>(null)
  
  const totalPages = Math.ceil(total / pageSize)

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>チーム名</TableHead>
              <TableHead>説明</TableHead>
              <TableHead className="text-center">メンバー数</TableHead>
              <TableHead className="text-center">アクティブタスク</TableHead>
              <TableHead className="text-center">今月の完了</TableHead>
              <TableHead>作成日</TableHead>
              <TableHead className="w-[100px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {teams.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <p className="text-muted-foreground">
                    チームが登録されていません
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              teams.map((team) => {
                const withStats = team as TeamWithStats
                return (
                  <TableRow key={team.id}>
                    <TableCell className="font-medium">{team.name}</TableCell>
                    <TableCell className="max-w-[300px] truncate">
                      {team.description || '-'}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary">
                        {withStats.member_count || team.members?.length || 0}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {withStats.active_tasks_count !== undefined ? (
                        <Badge variant="outline">
                          {withStats.active_tasks_count}
                        </Badge>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {withStats.completed_tasks_this_month !== undefined ? (
                        <Badge variant="default">
                          {withStats.completed_tasks_this_month}
                        </Badge>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {format(new Date(team.created_at), 'yyyy/MM/dd', {
                        locale: ja,
                      })}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            className="h-8 w-8 p-0"
                          >
                            <span className="sr-only">メニューを開く</span>
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>操作</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => router.push(`/admin/teams/${team.id}`)}
                          >
                            <Users className="mr-2 h-4 w-4" />
                            メンバー管理
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => setEditingTeam(team)}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            編集
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setDeletingTeam(team)}
                            className="text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            削除
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* ページネーション */}
      {totalPages > 1 && (
        <div className="mt-4">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => onPageChange(Math.max(1, page - 1))}
                  className={
                    page === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'
                  }
                />
              </PaginationItem>
              
              {[...Array(totalPages)].map((_, i) => {
                const pageNumber = i + 1
                // 現在のページの前後2ページのみ表示
                if (
                  pageNumber === 1 ||
                  pageNumber === totalPages ||
                  Math.abs(pageNumber - page) <= 2
                ) {
                  return (
                    <PaginationItem key={pageNumber}>
                      <PaginationLink
                        onClick={() => onPageChange(pageNumber)}
                        isActive={pageNumber === page}
                        className="cursor-pointer"
                      >
                        {pageNumber}
                      </PaginationLink>
                    </PaginationItem>
                  )
                }
                // 省略記号を表示
                if (Math.abs(pageNumber - page) === 3) {
                  return (
                    <PaginationItem key={pageNumber}>
                      <span className="px-3">...</span>
                    </PaginationItem>
                  )
                }
                return null
              })}
              
              <PaginationItem>
                <PaginationNext
                  onClick={() => onPageChange(Math.min(totalPages, page + 1))}
                  className={
                    page === totalPages
                      ? 'pointer-events-none opacity-50'
                      : 'cursor-pointer'
                  }
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}

      {/* 編集ダイアログ */}
      {editingTeam && (
        <TeamEditDialog
          team={editingTeam}
          open={!!editingTeam}
          onOpenChange={(open) => !open && setEditingTeam(null)}
        />
      )}

      {/* 削除確認ダイアログ */}
      {deletingTeam && (
        <TeamDeleteDialog
          team={deletingTeam}
          open={!!deletingTeam}
          onOpenChange={(open) => !open && setDeletingTeam(null)}
        />
      )}
    </>
  )
}