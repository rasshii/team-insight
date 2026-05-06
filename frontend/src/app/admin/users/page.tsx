/**
 * ユーザー管理ページ (Phase 0: 組織内ユーザー一覧 + 編集に簡素化)
 *
 * 旧 RBAC ベースの一括ロール編集機能は廃止。組織内ロールは
 * /api/v1/organizations/{id}/members で管理する設計に統合済み。
 */

'use client'

import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale/ja'
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  MoreHorizontal,
  Pencil,
  Search,
  Users,
} from 'lucide-react'
import { useMemo, useState } from 'react'

import { AdminOnly } from '@/components/auth/AdminOnly'
import { Layout } from '@/components/Layout'
import { PrivateRoute } from '@/components/PrivateRoute'
import { UserEditDialog } from '@/components/admin/UserEditDialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useDebounce } from '@/hooks/useDebounce'
import { useUsers } from '@/hooks/queries/useUsers'
import type { User, UserFilters, UserSortOptions } from '@/types/users'

export default function AdminUsersPage() {
  const [page, setPage] = useState(1)
  const [perPage] = useState(20)
  const [search, setSearch] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [sortBy, setSortBy] = useState<UserSortOptions['sort_by']>('created_at')
  const [sortOrder, setSortOrder] = useState<UserSortOptions['sort_order']>('desc')
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)

  const debouncedSearch = useDebounce(search, 300)

  const filters = useMemo<UserFilters>(() => {
    const f: UserFilters = {}
    if (debouncedSearch) f.search = debouncedSearch
    if (selectedStatus !== 'all') f.is_active = selectedStatus === 'active'
    return f
  }, [debouncedSearch, selectedStatus])

  const sort = useMemo<UserSortOptions>(
    () => ({ sort_by: sortBy, sort_order: sortOrder }),
    [sortBy, sortOrder]
  )

  const { data, isLoading } = useUsers({ page, per_page: perPage, filters, sort })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / perPage)) : 1

  const handleEdit = (user: User) => {
    setEditingUser(user)
    setEditDialogOpen(true)
  }

  const renderRoleBadges = (user: User) => {
    if (user.organizations.length === 0) {
      return <span className="text-xs text-muted-foreground">所属なし</span>
    }
    return (
      <div className="flex flex-wrap gap-1">
        {user.organizations.map((m) => (
          <Badge
            key={m.organization_id}
            variant={m.role === 'ADMIN' ? 'default' : 'secondary'}
            className="text-xs"
          >
            {m.organization_slug ?? `org-${m.organization_id}`}: {m.role}
          </Badge>
        ))}
      </div>
    )
  }

  const renderStatusBadge = (user: User) =>
    user.is_active ? (
      <Badge variant="default">ログイン可</Badge>
    ) : (
      <Badge variant="destructive">ログイン不可</Badge>
    )

  return (
    <PrivateRoute>
      <AdminOnly>
        <Layout>
          <div className="container mx-auto p-6 space-y-6">
            <div>
              <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                <Users className="h-8 w-8" />
                ユーザー管理
              </h1>
              <p className="text-muted-foreground mt-1">
                組織内のユーザーを一覧で確認・編集します
              </p>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>フィルター</CardTitle>
                <CardDescription>
                  条件を指定してユーザーを絞り込みます
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="名前またはメールで検索"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger>
                      <SelectValue placeholder="ステータス" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">すべて</SelectItem>
                      <SelectItem value="active">ログイン可</SelectItem>
                      <SelectItem value="inactive">ログイン不可</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="flex gap-2">
                    <Select
                      value={sortBy}
                      onValueChange={(v) => setSortBy(v as UserSortOptions['sort_by'])}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="並び順" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="name">名前</SelectItem>
                        <SelectItem value="email">メール</SelectItem>
                        <SelectItem value="created_at">登録日</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select
                      value={sortOrder}
                      onValueChange={(v) =>
                        setSortOrder(v as UserSortOptions['sort_order'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="順序" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="asc">昇順</SelectItem>
                        <SelectItem value="desc">降順</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>ユーザー一覧</CardTitle>
                <CardDescription>
                  {data
                    ? `${data.total} 人のユーザーが登録されています`
                    : 'ユーザーを読み込んでいます...'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : (
                  <>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>ユーザー</TableHead>
                          <TableHead>所属組織 / ロール</TableHead>
                          <TableHead>ステータス</TableHead>
                          <TableHead>登録日</TableHead>
                          <TableHead className="w-[50px]" />
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {data?.users.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium">{user.name}</div>
                                <div className="text-sm text-muted-foreground">
                                  {user.email}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>{renderRoleBadges(user)}</TableCell>
                            <TableCell>{renderStatusBadge(user)}</TableCell>
                            <TableCell>
                              <div className="text-sm">
                                {formatDistanceToNow(new Date(user.created_at), {
                                  addSuffix: true,
                                  locale: ja,
                                })}
                              </div>
                            </TableCell>
                            <TableCell>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm">
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuLabel>操作</DropdownMenuLabel>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem onClick={() => handleEdit(user)}>
                                    <Pencil className="mr-2 h-4 w-4" />
                                    編集
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>

                    {totalPages > 1 && data && (
                      <div className="flex items-center justify-between mt-4">
                        <div className="text-sm text-muted-foreground">
                          {data.total} 件中{' '}
                          {(page - 1) * perPage + 1} -{' '}
                          {Math.min(page * perPage, data.total)} 件を表示
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(1)}
                            disabled={page === 1}
                          >
                            <ChevronsLeft className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(page - 1)}
                            disabled={page === 1}
                          >
                            <ChevronLeft className="h-4 w-4" />
                          </Button>
                          <div className="text-sm font-medium">
                            {page} / {totalPages}
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(page + 1)}
                            disabled={page === totalPages}
                          >
                            <ChevronRight className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(totalPages)}
                            disabled={page === totalPages}
                          >
                            <ChevronsRight className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <UserEditDialog
              user={editingUser}
              open={editDialogOpen}
              onOpenChange={setEditDialogOpen}
            />
          </div>
        </Layout>
      </AdminOnly>
    </PrivateRoute>
  )
}
