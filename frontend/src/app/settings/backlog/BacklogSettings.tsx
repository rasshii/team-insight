'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { useBacklogConnection, useConnectBacklogOAuth, useDisconnectBacklog, useTestBacklogConnection, useUpdateBacklogSpaceKey } from '@/hooks/queries/useBacklog'

export default function BacklogSettingsPage() {
  const router = useRouter()
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const [testMessage, setTestMessage] = useState<string>('')
  const [isEditingSpaceKey, setIsEditingSpaceKey] = useState(false)
  const [newSpaceKey, setNewSpaceKey] = useState('')

  // React Query hooks
  const { data: connection, isLoading: isLoadingConnection } = useBacklogConnection()
  const connectOAuthMutation = useConnectBacklogOAuth()
  const disconnectMutation = useDisconnectBacklog()
  const testConnectionMutation = useTestBacklogConnection()
  const updateSpaceKeyMutation = useUpdateBacklogSpaceKey()

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


  // 直接実行用の関数
  const handleOAuthDirectConnect = async () => {
    const spaceKeyInput = document.getElementById('oauth_space_key') as HTMLInputElement
    const spaceKey = spaceKeyInput?.value
    
    if (!spaceKey) {
      alert('スペースキーを入力してください')
      return
    }
    
    try {
      const url = `/api/v1/auth/backlog/authorize?space_key=${encodeURIComponent(spaceKey)}`
      
      // 直接APIを呼び出す
      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.authorization_url) {
        window.location.href = data.authorization_url
      } else {
        alert('認証URLの取得に失敗しました')
      }
    } catch (error) {
      alert('OAuth認証の開始に失敗しました')
    }
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
                  {isEditingSpaceKey ? (
                    <div className="flex gap-2 mt-1">
                      <Input
                        value={newSpaceKey}
                        onChange={(e) => setNewSpaceKey(e.target.value)}
                        placeholder="your-space"
                        className="flex-1"
                      />
                      <Button
                        size="sm"
                        onClick={() => {
                          updateSpaceKeyMutation.mutate(
                            { space_key: newSpaceKey },
                            {
                              onSuccess: () => {
                                setIsEditingSpaceKey(false)
                                setNewSpaceKey('')
                              },
                            }
                          )
                        }}
                        disabled={!newSpaceKey || updateSpaceKeyMutation.isPending}
                      >
                        保存
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setIsEditingSpaceKey(false)
                          setNewSpaceKey('')
                        }}
                      >
                        キャンセル
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 mt-1">
                      <p className="text-sm text-muted-foreground">{connection.space_key || '未設定'}</p>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-primary"
                        onClick={() => {
                          setNewSpaceKey(connection.space_key || '')
                          setIsEditingSpaceKey(true)
                        }}
                      >
                        編集
                      </Button>
                    </div>
                  )}
                </div>

                <div>
                  <Label>連携方法</Label>
                  <Badge variant="outline" className="mt-1">
                    OAuth
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
            <div className="space-y-4">
                
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Backlogアカウントでログインして連携します。より安全な連携方法です。
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="oauth_space_key">スペースキー</Label>
                    <Input
                      id="oauth_space_key"
                      placeholder="your-space"
                    />
                    <p className="text-xs text-muted-foreground">
                      https://your-space.backlog.jp の "your-space" 部分
                    </p>
                  </div>

                  <Button
                    type="button"
                    className="w-full pointer-events-auto"
                    disabled={false}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleOAuthDirectConnect()
                    }}
                  >
                    Backlogでログイン
                  </Button>
                </div>

                {connectOAuthMutation.isError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {(connectOAuthMutation.error as any)?.response?.data?.detail || '認証の開始に失敗しました'}
                    </AlertDescription>
                  </Alert>
                )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}