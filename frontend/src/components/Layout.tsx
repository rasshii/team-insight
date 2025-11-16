/**
 * @fileoverview アプリケーション共通レイアウトコンポーネント
 *
 * ナビゲーションバー、ユーザーメニュー、モバイルメニューを含む、
 * 認証済みユーザー向けの共通レイアウトを提供します。
 *
 * @module Layout
 */

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { FolderOpen, Home, LogOut, Menu, Settings, Users, UserCircle, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { PrivateRoute } from "./PrivateRoute";
import { usePermissions } from "@/hooks/usePermissions";

/**
 * レイアウトコンポーネントのプロパティ型定義
 */
interface LayoutProps {
  /** レイアウト内に表示するコンテンツ */
  children: React.ReactNode;
}

/**
 * アプリケーション共通レイアウトコンポーネント
 *
 * 認証済みユーザー向けの共通レイアウトを提供します。
 * ナビゲーションバー、ユーザーメニュー、モバイルメニューを含みます。
 *
 * ## 主要機能
 * - グローバルナビゲーション（ダッシュボード、プロジェクト、チーム）
 * - ユーザーメニュー（プロフィール、設定、ログアウト）
 * - 管理者メニュー（ユーザー管理、チーム管理）
 * - レスポンシブデザイン（モバイル/デスクトップ）
 *
 * ## 権限による表示制御
 * - 管理者メニューは管理者のみ表示
 * - 各メニュー項目は権限に応じて動的に表示/非表示
 *
 * @param {LayoutProps} props - コンポーネントのプロパティ
 * @returns {JSX.Element} レイアウトコンポーネント
 *
 * @example
 * ```tsx
 * function DashboardPage() {
 *   return (
 *     <Layout>
 *       <h1>ダッシュボード</h1>
 *       <DashboardContent />
 *     </Layout>
 *   );
 * }
 * ```
 *
 * @remarks
 * - このコンポーネントは必ずPrivateRouteでラップする必要があります
 * - モバイルメニューは768px未満で表示されます
 * - ユーザーアバターはDicebearを使用して自動生成されます
 *
 * @see {@link PrivateRoute} - 認証保護ラッパーコンポーネント
 * @see {@link useAuth} - 認証状態管理フック
 * @see {@link usePermissions} - 権限チェックフック
 */
export function Layout({ children }: LayoutProps) {
  const { user, logout, isAuthenticated, isInitialized } = useAuth();
  const permissions = usePermissions();
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const navigation = [
    { name: "ダッシュボード", href: "/dashboard", icon: Home },
    { name: "プロジェクト", href: "/projects", icon: FolderOpen },
    { name: "チーム", href: "/teams", icon: Users },
  ];

  return (
    <PrivateRoute>
      <div className="min-h-screen bg-background">
        <nav className="border-b bg-card">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center">
                <Link href="/" className="flex items-center space-x-2">
                  <span className="text-xl font-bold">Team Insight</span>
                </Link>

                {/* デスクトップナビゲーション */}
                <div className="hidden md:block">
                  <div className="ml-10 flex items-baseline space-x-4">
                    {navigation.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.name}
                          href={item.href}
                          className="flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                        >
                          <Icon className="h-4 w-4" />
                          <span>{item.name}</span>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {user && (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        className="relative h-8 w-8 rounded-full"
                      >
                        <Avatar className="h-8 w-8">
                          <AvatarImage
                            src={`https://api.dicebear.com/7.x/initials/svg?seed=${user.name}`}
                            alt={user.name}
                          />
                          <AvatarFallback>
                            {user.name.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                      className="w-56"
                      align="end"
                      forceMount
                    >
                      <DropdownMenuLabel className="font-normal">
                        <div className="flex flex-col space-y-1">
                          <p className="text-sm font-medium leading-none">
                            {user.name}
                          </p>
                          <p className="text-xs leading-none text-muted-foreground">
                            {user.email}
                          </p>
                        </div>
                      </DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link href="/settings/profile">
                          <UserCircle className="mr-2 h-4 w-4" />
                          <span>プロフィール</span>
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href="/settings">
                          <Settings className="mr-2 h-4 w-4" />
                          <span>設定</span>
                        </Link>
                      </DropdownMenuItem>
                      {permissions && permissions.isAdmin?.() && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuLabel className="text-xs">管理者メニュー</DropdownMenuLabel>
                          <DropdownMenuItem asChild>
                            <Link href="/admin/users">
                              <Users className="mr-2 h-4 w-4" />
                              <span>ユーザー管理</span>
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link href="/admin/teams">
                              <Users className="mr-2 h-4 w-4" />
                              <span>チーム管理</span>
                            </Link>
                          </DropdownMenuItem>
                        </>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={handleLogout}>
                        <LogOut className="mr-2 h-4 w-4" />
                        <span>ログアウト</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}

                {/* モバイルメニューボタン */}
                <div className="md:hidden">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  >
                    <Menu className="h-6 w-6" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* モバイルメニュー */}
          {isMobileMenuOpen && (
            <div className="md:hidden">
              <div className="space-y-1 px-2 pb-3 pt-2 sm:px-3">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className="flex items-center space-x-2 rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
                {permissions.isAdmin() && (
                  <>
                    <div className="my-2 border-t border-border" />
                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground">
                      管理者メニュー
                    </div>
                    <Link
                      href="/admin/users"
                      className="flex items-center space-x-2 rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      <Users className="h-4 w-4" />
                      <span>ユーザー管理</span>
                    </Link>
                    <Link
                      href="/admin/teams"
                      className="flex items-center space-x-2 rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      <Users className="h-4 w-4" />
                      <span>チーム管理</span>
                    </Link>
                  </>
                )}
              </div>
            </div>
          )}
        </nav>


        <main className="flex-1">{children}</main>
      </div>
    </PrivateRoute>
  );
}
