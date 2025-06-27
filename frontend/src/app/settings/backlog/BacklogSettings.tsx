'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, AlertCircle, Loader2, ExternalLink } from 'lucide-react'
import { useBacklogConnection, useConnectBacklogApiKey, useConnectBacklogOAuth, useDisconnectBacklog, useTestBacklogConnection } from '@/hooks/queries/useBacklog'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const apiKeySchema = z.object({
  space_key: z.string().min(1, 'スペースキーを入力してください'),
  api_key: z.string().min(1, 'APIキーを入力してください'),
})

type ApiKeyFormData = z.infer<typeof apiKeySchema>

export default function BacklogSettingsPage() {
  const router = useRouter()
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const [testMessage, setTestMessage] = useState<string>('')

  // React Query hooks
  const { data: connection, isLoading: isLoadingConnection } = useBacklogConnection()
  const connectApiKeyMutation = useConnectBacklogApiKey()
  const connectOAuthMutation = useConnectBacklogOAuth()
  const disconnectMutation = useDisconnectBacklog()
  const testConnectionMutation = useTestBacklogConnection()

  // Form setup
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ApiKeyFormData>({
    resolver: zodResolver(apiKeySchema),
  })

  const handleTestConnection = async () => {
    setTestStatus('testing')
    setTestMessage('')

    testConnectionMutation.mutate(undefined, {
      onSuccess: (data) => {
        setTestStatus('success')
        setTestMessage(data.message)
      },
      onError: (error: any) => {
        setTestStatus('error')
        setTestMessage(error.response?.data?.detail || '接続テストに失敗しました')
      },
    })
  }

  const handleApiKeySubmit = async (data: ApiKeyFormData) => {
    connectApiKeyMutation.mutate(data, {
      onSuccess: () => {
        reset()
        setTestStatus('idle')
        setTestMessage('')
      },
    })
  }

  const handleOAuthConnect = () => {
    connectOAuthMutation.mutate(undefined, {
      onSuccess: (data) => {
        if (data.auth_url) {
          window.location.href = data.auth_url
        }
      },
    })
  }

  const handleDisconnect = () => {
    if (window.confirm('Backlog連携を解除してもよろしいですか？')) {
      disconnectMutation.mutate(undefined, {
        onSuccess: () => {
          setTestStatus('idle')
          setTestMessage('')
        },
      })
    }
  }

  if (isLoadingConnection) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container max-w-4xl mx-auto py-8">
      <Card>
        <CardHeader>
          <CardTitle>Backlog連携設定</CardTitle>
          <CardDescription>
            BacklogのAPIと連携して、プロジェクトやタスクのデータを取得します
          </CardDescription>
        </CardHeader>
        <CardContent>
          {connection?.is_connected ? (
            <div className="space-y-6">
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  Backlogと連携済みです
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div>
                  <Label>スペースキー</Label>
                  <p className="text-sm text-muted-foreground mt-1">{connection.space_key}</p>
                </div>

                <div>
                  <Label>連携方法</Label>
                  <Badge variant="outline" className="mt-1">
                    {connection.connection_type === 'api_key' ? 'APIキー' : 'OAuth'}
                  </Badge>
                </div>

                <div>
                  <Label>連携日時</Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    {connection.connected_at ? new Date(connection.connected_at).toLocaleString('ja-JP') : '-'}
                  </p>
                </div>

                {connection.last_sync_at && (
                  <div>
                    <Label>最終同期日時</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      {new Date(connection.last_sync_at).toLocaleString('ja-JP')}
                    </p>
                  </div>
                )}
              </div>

              <div className="flex gap-4">
                <Button
                  onClick={handleTestConnection}
                  disabled={testStatus === 'testing'}
                  variant="outline"
                >
                  {testStatus === 'testing' ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      テスト中...
                    </>
                  ) : (
                    '接続テスト'
                  )}
                </Button>
                <Button
                  onClick={handleDisconnect}
                  variant="destructive"
                  disabled={disconnectMutation.isPending}
                >
                  {disconnectMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      解除中...
                    </>
                  ) : (
                    '連携解除'
                  )}
                </Button>
              </div>

              {testStatus !== 'idle' && (
                <Alert variant={testStatus === 'success' ? 'default' : 'destructive'}>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{testMessage}</AlertDescription>
                </Alert>
              )}
            </div>
          ) : (
            <Tabs defaultValue="api-key" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="api-key">APIキー</TabsTrigger>
                <TabsTrigger value="oauth">OAuth</TabsTrigger>
              </TabsList>

              <TabsContent value="api-key" className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    BacklogのAPIキーを使用して連携します。APIキーは個人設定から取得できます。
                  </p>
                  <a
                    href="https://support-ja.backlog.com/hc/ja/articles/360035641754"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                  >
                    APIキーの取得方法
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <form onSubmit={handleSubmit(handleApiKeySubmit)} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="space_key">スペースキー</Label>
                    <Input
                      id="space_key"
                      placeholder="your-space"
                      {...register('space_key')}
                    />
                    {errors.space_key && (
                      <p className="text-sm text-destructive">{errors.space_key.message}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      https://your-space.backlog.jp の "your-space" 部分
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="api_key">APIキー</Label>
                    <Input
                      id="api_key"
                      type="password"
                      placeholder="APIキーを入力"
                      {...register('api_key')}
                    />
                    {errors.api_key && (
                      <p className="text-sm text-destructive">{errors.api_key.message}</p>
                    )}
                  </div>

                  <Button
                    type="submit"
                    disabled={connectApiKeyMutation.isPending}
                    className="w-full"
                  >
                    {connectApiKeyMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        連携中...
                      </>
                    ) : (
                      '連携する'
                    )}
                  </Button>
                </form>

                {connectApiKeyMutation.isError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {(connectApiKeyMutation.error as any)?.response?.data?.detail || '連携に失敗しました'}
                    </AlertDescription>
                  </Alert>
                )}
              </TabsContent>

              <TabsContent value="oauth" className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Backlogアカウントでログインして連携します。より安全な連携方法です。
                  </p>
                </div>

                <Button
                  onClick={handleOAuthConnect}
                  disabled={connectOAuthMutation.isPending}
                  className="w-full"
                >
                  {connectOAuthMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      認証ページへ移動中...
                    </>
                  ) : (
                    'Backlogでログイン'
                  )}
                </Button>

                {connectOAuthMutation.isError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {(connectOAuthMutation.error as any)?.response?.data?.detail || '認証の開始に失敗しました'}
                    </AlertDescription>
                  </Alert>
                )}
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  )
}