"use client";

import { useState, useMemo } from 'react';
import { Layout } from "@/components/Layout";
import { PrivateRoute } from "@/components/PrivateRoute";
import { AdminOnly } from "@/components/auth/AdminOnly";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Users,
  Search,
  MoreHorizontal,
  Pencil,
  ShieldCheck,
  ShieldOff,
  UserCheck,
  UserX,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useUsers } from '@/hooks/queries/useUsers';
import { UserEditDialog } from '@/components/admin/UserEditDialog';
import { User, UserFilters, UserSortOptions } from '@/types/users';
import { formatDistanceToNow } from 'date-fns';
import { ja } from 'date-fns/locale/ja';
import { useDebounce } from '@/hooks/useDebounce';

export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<UserSortOptions['sort_by']>('created_at');
  const [sortOrder, setSortOrder] = useState<UserSortOptions['sort_order']>('desc');
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const debouncedSearch = useDebounce(search, 300);

  // フィルター構築
  const filters = useMemo<UserFilters>(() => {
    const f: UserFilters = {};
    if (debouncedSearch) f.search = debouncedSearch;
    if (selectedStatus !== 'all') {
      f.is_active = selectedStatus === 'active';
    }
    if (selectedRole !== 'all') {
      // ロールIDの実装は後で追加
    }
    return f;
  }, [debouncedSearch, selectedStatus, selectedRole]);

  // ソートオプション
  const sort = useMemo<UserSortOptions>(() => ({
    sort_by: sortBy,
    sort_order: sortOrder,
  }), [sortBy, sortOrder]);

  const { data, isLoading } = useUsers({ page, page_size: pageSize, filters, sort });

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setEditDialogOpen(true);
  };

  const getRoleBadges = (user: User) => {
    return user.user_roles.map((ur) => (
      <Badge key={ur.id} variant="secondary" className="text-xs">
        {ur.role.name === 'ADMIN' ? '管理者' :
         ur.role.name === 'PROJECT_LEADER' ? 'プロジェクトリーダー' :
         ur.role.name === 'MEMBER' ? 'メンバー' :
         ur.role.name}
      </Badge>
    ));
  };

  const getStatusBadge = (user: User) => {
    if (!user.is_active) {
      return <Badge variant="destructive">無効</Badge>;
    }
    if (!user.is_email_verified) {
      return <Badge variant="outline">メール未確認</Badge>;
    }
    return <Badge variant="default">有効</Badge>;
  };

  return (
    <PrivateRoute>
      <AdminOnly>
        <Layout>
          <div className="container mx-auto p-6 space-y-6">
            {/* ヘッダー */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                  <Users className="h-8 w-8" />
                  ユーザー管理
                </h1>
                <p className="text-muted-foreground mt-1">
                  システムに登録されているユーザーを管理します
                </p>
              </div>
            </div>

            {/* フィルターセクション */}
            <Card>
              <CardHeader>
                <CardTitle>フィルター</CardTitle>
                <CardDescription>
                  条件を指定してユーザーを絞り込みます
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
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
                      <SelectItem value="active">有効</SelectItem>
                      <SelectItem value="inactive">無効</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
                    <SelectTrigger>
                      <SelectValue placeholder="並び順" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="name">名前</SelectItem>
                      <SelectItem value="email">メール</SelectItem>
                      <SelectItem value="created_at">登録日</SelectItem>
                      <SelectItem value="last_login_at">最終ログイン</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={sortOrder} onValueChange={(v) => setSortOrder(v as any)}>
                    <SelectTrigger>
                      <SelectValue placeholder="順序" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="asc">昇順</SelectItem>
                      <SelectItem value="desc">降順</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* ユーザーテーブル */}
            <Card>
              <CardHeader>
                <CardTitle>ユーザー一覧</CardTitle>
                <CardDescription>
                  {data ? `${data.total}人のユーザーが登録されています` : 'ユーザーを読み込んでいます...'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : (
                  <>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>ユーザー</TableHead>
                          <TableHead>ロール</TableHead>
                          <TableHead>ステータス</TableHead>
                          <TableHead>登録日</TableHead>
                          <TableHead>最終ログイン</TableHead>
                          <TableHead className="w-[50px]"></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {data?.users.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium">{user.name}</div>
                                <div className="text-sm text-muted-foreground">{user.email}</div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-1 flex-wrap">
                                {getRoleBadges(user)}
                              </div>
                            </TableCell>
                            <TableCell>{getStatusBadge(user)}</TableCell>
                            <TableCell>
                              <div className="text-sm">
                                {formatDistanceToNow(new Date(user.created_at), {
                                  addSuffix: true,
                                  locale: ja,
                                })}
                              </div>
                            </TableCell>
                            <TableCell>
                              {user.last_login_at ? (
                                <div className="text-sm">
                                  {formatDistanceToNow(new Date(user.last_login_at), {
                                    addSuffix: true,
                                    locale: ja,
                                  })}
                                </div>
                              ) : (
                                <span className="text-sm text-muted-foreground">未ログイン</span>
                              )}
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

                    {/* ページネーション */}
                    {data && data.total_pages > 1 && (
                      <div className="flex items-center justify-between mt-4">
                        <div className="text-sm text-muted-foreground">
                          {data.total}件中 {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, data.total)}件を表示
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
                            {page} / {data.total_pages}
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(page + 1)}
                            disabled={page === data.total_pages}
                          >
                            <ChevronRight className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(data.total_pages)}
                            disabled={page === data.total_pages}
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

            {/* 編集ダイアログ */}
            <UserEditDialog
              user={editingUser}
              open={editDialogOpen}
              onOpenChange={setEditDialogOpen}
            />
          </div>
        </Layout>
      </AdminOnly>
    </PrivateRoute>
  );
}