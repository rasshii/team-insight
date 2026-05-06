'use client'

import { Building2, Hash, Mail, User, Users } from 'lucide-react'

import { Layout } from '@/components/Layout'
import { PrivateRoute } from '@/components/PrivateRoute'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { useAppSelector } from '@/store/hooks'

/**
 * プロフィール設定ページ (Phase 0: organizations 表示)
 */
export default function ProfileSettingsPage() {
  const user = useAppSelector((state) => state.auth.user)

  if (!user) {
    return null
  }

  return (
    <PrivateRoute>
      <Layout>
        <div className="container mx-auto py-8 max-w-4xl">
          <h1 className="text-3xl font-bold mb-8">プロフィール設定</h1>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  基本情報
                </CardTitle>
                <CardDescription>ユーザー基本情報</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>名前</Label>
                  <p className="text-lg font-medium mt-1">
                    {user.name ?? user.full_name ?? '-'}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  メールアドレス
                </CardTitle>
                <CardDescription>登録されているメールアドレス</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  <p className="text-lg font-medium">
                    {user.email ?? '未設定'}
                  </p>
                  {user.email && (
                    <p className="text-sm text-muted-foreground">
                      レポート配信やシステム通知はこのアドレスに送信されます
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  所属組織とロール
                </CardTitle>
                <CardDescription>
                  Team Insight 上で参加している組織と、そこでのロールです
                </CardDescription>
              </CardHeader>
              <CardContent>
                {user.organizations.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    どの組織にも所属していません
                  </p>
                ) : (
                  <ul className="space-y-3">
                    {user.organizations.map((m) => (
                      <li
                        key={m.organization_id}
                        className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                      >
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">
                            {m.organization_name ?? `org-${m.organization_id}`}
                          </span>
                          {m.organization_slug && (
                            <span className="text-xs text-muted-foreground">
                              ({m.organization_slug})
                            </span>
                          )}
                        </div>
                        <Badge
                          variant={
                            m.role === 'ADMIN'
                              ? 'destructive'
                              : m.role === 'PROJECT_LEADER'
                              ? 'default'
                              : 'secondary'
                          }
                        >
                          {m.role}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Hash className="h-5 w-5" />
                  アカウント状態
                </CardTitle>
                <CardDescription>アカウントのステータス情報</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>ログイン状態</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      システムへのアクセス可否
                    </p>
                  </div>
                  <Badge variant={user.is_active ? 'default' : 'destructive'}>
                    {user.is_active ? '有効' : '無効'}
                  </Badge>
                </div>
                {user.is_system_admin && (
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>System Admin</Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        全組織横断の管理権限
                      </p>
                    </div>
                    <Badge variant="default">付与済み</Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </Layout>
    </PrivateRoute>
  )
}
