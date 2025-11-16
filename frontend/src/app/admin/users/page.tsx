/**
 * @fileoverview ユーザー管理ページ
 *
 * システムに登録されているユーザーの一覧表示、検索、フィルタリング、編集を行う管理者向けページ。
 * Backlogからのユーザー一括インポート機能も提供します。
 *
 * @module AdminUsersPage
 */

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
  Download,
  ArrowRight,
} from "lucide-react";
import { useUsers } from '@/hooks/queries/useUsers';
import { useImportBacklogUsers } from '@/hooks/queries/useSync';
import { useProjects } from '@/hooks/queries/useProjects';
import { useTeams } from '@/hooks/queries/useTeams';
import { UserEditDialog } from '@/components/admin/UserEditDialog';
import { User, UserFilters, UserSortOptions } from '@/types/users';
import { formatDistanceToNow } from 'date-fns';
import { ja } from 'date-fns/locale/ja';
import { useDebounce } from '@/hooks/useDebounce';
import Link from 'next/link';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';

/**
 * ユーザー管理ページ
 *
 * システムに登録されているユーザーを管理する管理者専用ページです。
 *
 * ## 主要機能
 * - ユーザー一覧の表形式表示
 *   - ユーザー名とメールアドレス
 *   - グローバルロールとプロジェクトロール
 *   - ログイン可/不可ステータス
 *   - 登録日時と最終ログイン日時
 * - 高度な検索とフィルタリング
 *   - テキスト検索（名前/メール）
 *   - ステータスフィルター（ログイン可/不可）
 *   - プロジェクトフィルター
 *   - チームフィルター
 *   - ソート機能（名前、メール、登録日、最終ログイン）
 * - ユーザー編集機能
 *   - ロール変更
 *   - ログイン可/不可の切り替え
 * - Backlogユーザー一括インポート
 *   - アクティブユーザーのみ/全ユーザー選択可能
 *   - デフォルトロール自動付与オプション
 * - ページネーション（20件/ページ）
 *
 * ## データフェッチ戦略
 * - React Queryでユーザーデータを取得
 * - デバウンス検索（300ms）でAPI呼び出しを最適化
 * - フィルター変更時に自動的に再取得
 *
 * ## 権限
 * - 管理者（ADMIN）ロールのみアクセス可能（AdminOnlyでラップ）
 *
 * @example
 * ```tsx
 * // App Routerでの使用
 * // app/admin/users/page.tsx
 * export default AdminUsersPage
 * ```
 *
 * @returns {JSX.Element} ユーザー管理ページのUIコンポーネント
 *
 * @remarks
 * - 検索テキストは300msのデバウンス処理が適用されます
 * - ユーザー一覧は20件ずつページネーション表示されます
 * - Backlogインポートは全プロジェクトからユーザーを収集します
 *
 * @see {@link useUsers} - ユーザー一覧取得フック
 * @see {@link useImportBacklogUsers} - Backlogユーザーインポートフック
 * @see {@link UserEditDialog} - ユーザー編集ダイアログコンポーネント
 * @see {@link AdminOnly} - 管理者権限チェックコンポーネント
 */
export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedProject, setSelectedProject] = useState<string>('all');
  const [selectedTeam, setSelectedTeam] = useState<string>('all');
  const [sortBy, setSortBy] = useState<UserSortOptions['sort_by']>('created_at');
  const [sortOrder, setSortOrder] = useState<UserSortOptions['sort_order']>('desc');
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importMode, setImportMode] = useState<'all' | 'active_only'>('active_only');
  const [assignDefaultRole, setAssignDefaultRole] = useState(true);

  const debouncedSearch = useDebounce(search, 300);
  const importUsersMutation = useImportBacklogUsers();

  // プロジェクトとチームのデータを取得
  const { data: projectsData } = useProjects();
  const { data: teamsData } = useTeams();

  /**
   * フィルター構築
   *
   * ユーザーが選択したフィルター条件をまとめて、
   * APIリクエスト用のフィルターオブジェクトを生成します。
   *
   * @returns {UserFilters} APIリクエスト用フィルターオブジェクト
   */
  const filters = useMemo<UserFilters>(() => {
    const f: UserFilters = {};
    if (debouncedSearch) f.search = debouncedSearch;
    if (selectedStatus !== 'all') {
      f.is_active = selectedStatus === 'active';
    }
    if (selectedRole !== 'all') {
      // ロールIDの実装は後で追加
    }
    if (selectedProject !== 'all') {
      f.project_id = parseInt(selectedProject);
    }
    if (selectedTeam !== 'all') {
      f.team_id = parseInt(selectedTeam);
    }
    return f;
  }, [debouncedSearch, selectedStatus, selectedRole, selectedProject, selectedTeam]);

  /**
   * ソートオプション
   *
   * ユーザーが選択したソート条件をまとめて、
   * APIリクエスト用のソートオプションを生成します。
   *
   * @returns {UserSortOptions} APIリクエスト用ソートオプション
   */
  const sort = useMemo<UserSortOptions>(() => ({
    sort_by: sortBy,
    sort_order: sortOrder,
  }), [sortBy, sortOrder]);

  const { data, isLoading } = useUsers({ page, page_size: pageSize, filters, sort });

  /**
   * ユーザー編集ハンドラー
   *
   * 編集対象のユーザーを設定し、編集ダイアログを開きます。
   *
   * @param {User} user - 編集対象のユーザーオブジェクト
   */
  const handleEdit = (user: User) => {
    setEditingUser(user);
    setEditDialogOpen(true);
  };

  /**
   * ロールバッジの生成
   *
   * ユーザーのロール情報（グローバルロールとプロジェクトロール）を
   * バッジ形式で表示するためのJSX要素を生成します。
   *
   * @param {User} user - ロール情報を持つユーザーオブジェクト
   * @returns {JSX.Element} ロールバッジのJSX要素
   */
  const getRoleBadges = (user: User) => {
    // グローバルロールとプロジェクトロールを分けて整理
    const globalRoles = user.user_roles.filter(ur => !ur.project_id);
    const projectRoles = user.user_roles.filter(ur => ur.project_id);

    return (
      <div className="space-y-1">
        {/* グローバルロール */}
        {globalRoles.length > 0 && (
          <div className="flex gap-1 flex-wrap items-center">
            <span className="text-xs text-muted-foreground">全体:</span>
            {globalRoles.map((ur) => (
              <Badge key={ur.id} variant="default" className="text-xs">
                {ur.role.name === 'ADMIN' ? '管理者' :
                 ur.role.name === 'PROJECT_LEADER' ? 'プロジェクトリーダー' :
                 ur.role.name === 'MEMBER' ? 'メンバー' :
                 ur.role.name}
              </Badge>
            ))}
          </div>
        )}
        
        {/* プロジェクトロール */}
        {projectRoles.length > 0 && (
          <div className="flex gap-1 flex-wrap items-center">
            <span className="text-xs text-muted-foreground">プロジェクト:</span>
            {projectRoles.map((ur) => (
              <Badge key={ur.id} variant="secondary" className="text-xs">
                {ur.role.name === 'PROJECT_LEADER' ? 'リーダー' :
                 ur.role.name === 'MEMBER' ? 'メンバー' :
                 ur.role.name}
                {ur.project_id && <span className="ml-1 opacity-70">(P{ur.project_id})</span>}
              </Badge>
            ))}
          </div>
        )}
        
        {/* ロールがない場合 */}
        {user.user_roles.length === 0 && (
          <span className="text-xs text-muted-foreground">ロールなし</span>
        )}
      </div>
    );
  };

  /**
   * ステータスバッジの生成
   *
   * ユーザーのログイン可/不可ステータスをバッジ形式で表示します。
   *
   * @param {User} user - ステータス情報を持つユーザーオブジェクト
   * @returns {JSX.Element} ステータスバッジのJSX要素
   */
  const getStatusBadge = (user: User) => {
    if (!user.is_active) {
      return <Badge variant="destructive">ログイン不可</Badge>;
    }
    return <Badge variant="default">ログイン可</Badge>;
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
              <Link href="/admin/teams">
                <Button variant="outline" className="gap-2">
                  チーム管理へ
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
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
                <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
                  <div className="relative md:col-span-2 lg:col-span-1">
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
                  <Select value={selectedProject} onValueChange={setSelectedProject}>
                    <SelectTrigger>
                      <SelectValue placeholder="プロジェクト" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">すべてのプロジェクト</SelectItem>
                      {projectsData?.projects.map((project) => (
                        <SelectItem key={project.id} value={project.id.toString()}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={selectedTeam} onValueChange={setSelectedTeam}>
                    <SelectTrigger>
                      <SelectValue placeholder="チーム" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">すべてのチーム</SelectItem>
                      {teamsData?.teams.map((team) => (
                        <SelectItem key={team.id} value={team.id.toString()}>
                          {team.name}
                        </SelectItem>
                      ))}
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
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>ユーザー一覧</CardTitle>
                    <CardDescription>
                      {data ? `${data.total}人のユーザーが登録されています` : 'ユーザーを読み込んでいます...'}
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => setImportDialogOpen(true)}
                    disabled={importUsersMutation.isPending}
                  >
                    {importUsersMutation.isPending ? (
                      <>
                        <span className="animate-spin mr-2">⏳</span>
                        インポート中...
                      </>
                    ) : (
                      <>
                        <Download className="mr-2 h-4 w-4" />
                        Backlogから一括インポート
                      </>
                    )}
                  </Button>
                </div>
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
                              {getRoleBadges(user)}
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

            {/* インポートダイアログ */}
            <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Backlogユーザーの一括インポート</DialogTitle>
                  <DialogDescription>
                    Backlogの全プロジェクトからユーザー情報を収集し、Team Insightに登録します。
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>インポートモード</Label>
                    <Select
                      value={importMode}
                      onValueChange={(value: 'all' | 'active_only') => setImportMode(value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active_only">アクティブユーザーのみ</SelectItem>
                        <SelectItem value="all">全ユーザー（非アクティブ含む）</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="assignDefaultRole"
                      checked={assignDefaultRole}
                      onCheckedChange={(checked) => setAssignDefaultRole(checked as boolean)}
                    />
                    <Label
                      htmlFor="assignDefaultRole"
                      className="text-sm font-normal cursor-pointer"
                    >
                      新規ユーザーにMEMBERロールを自動付与
                    </Label>
                  </div>
                  <div className="rounded-lg bg-muted p-3">
                    <p className="text-sm text-muted-foreground">
                      注意: この操作により、Backlogの全プロジェクトメンバーがインポートされます。
                      処理には時間がかかる場合があります。
                    </p>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setImportDialogOpen(false)}
                    disabled={importUsersMutation.isPending}
                  >
                    キャンセル
                  </Button>
                  <Button
                    onClick={() => {
                      importUsersMutation.mutate({
                        mode: importMode,
                        assignDefaultRole: assignDefaultRole,
                      }, {
                        onSuccess: () => {
                          setImportDialogOpen(false);
                        }
                      });
                    }}
                    disabled={importUsersMutation.isPending}
                  >
                    {importUsersMutation.isPending ? 'インポート中...' : 'インポート開始'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </Layout>
      </AdminOnly>
    </PrivateRoute>
  );
}