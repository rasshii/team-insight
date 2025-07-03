'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Loader2, AlertCircle, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { authService } from '@/services/auth.service'
import { useToast } from '@/hooks/use-toast'

export function SimpleLoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const error = searchParams?.get('error')

  const handleBacklogLogin = async () => {
    setIsLoading(true)
    
    try {
      // OAuth認証URLを取得して遷移
      const { authorization_url, state } = await authService.getAuthorizationUrl(false)
      authService.saveOAuthState(state)
      window.location.href = authorization_url
    } catch (error) {
      console.error('Failed to get authorization URL:', error)
      toast({
        title: 'エラー',
        description: 'Backlog認証の開始に失敗しました',
        variant: 'destructive',
      })
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <Card className="w-[450px] shadow-xl">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-3xl font-bold">Team Insight</CardTitle>
          <CardDescription className="text-base">
            チームの生産性を可視化・分析するプラットフォーム
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* スペース情報 */}
          <Alert>
            <AlertDescription className="text-center">
              <strong>nulab-exam</strong> スペースのメンバー専用
            </AlertDescription>
          </Alert>

          {/* エラー表示 */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error === 'auth_failed' ? '認証に失敗しました。もう一度お試しください。' :
                 error === 'space_not_allowed' ? (
                   <>
                     <p className="font-semibold">このBacklogスペースへのアクセス権限がありません。</p>
                     <p className="text-sm mt-2">
                       別のBacklogアカウントでログインしている可能性があります。
                     </p>
                     <p className="text-sm mt-2">
                       上記の「ログイン前の確認事項」に記載された方法（プライベートブラウジング等）をお試しください。
                     </p>
                   </>
                 ) :
                 error === 'domain_not_allowed' ? '組織外のメールアドレスではアクセスできません。' :
                 'エラーが発生しました。'}
              </AlertDescription>
            </Alert>
          )}

          {/* 重要な注意事項 */}
          <Alert variant="default" className="border-orange-200 bg-orange-50 dark:bg-orange-950">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            <AlertTitle className="text-orange-800 dark:text-orange-200">ログイン前の確認事項</AlertTitle>
            <AlertDescription className="mt-2 space-y-2 text-sm text-orange-700 dark:text-orange-300">
              <p className="font-semibold">別のBacklogスペースのアカウントでログイン中の方へ：</p>
              <p>Team Insightは<strong>nulab-examスペース専用</strong>のツールです。</p>
              <p>別のスペースのアカウントでログイン中の場合は、以下のいずれかの方法をお試しください：</p>
              <div className="space-y-3 ml-2">
                <div className="border-l-2 border-orange-400 pl-3">
                  <p className="font-medium">方法1: プライベートブラウジングを使用（推奨）</p>
                  <p className="text-xs">新しいプライベート/シークレットウィンドウを開いてアクセス</p>
                </div>
                <div className="border-l-2 border-orange-400 pl-3">
                  <p className="font-medium">方法2: 別のブラウザを使用</p>
                  <p className="text-xs">Chrome、Firefox、Safari など別のブラウザでアクセス</p>
                </div>
                <div className="border-l-2 border-orange-400 pl-3">
                  <p className="font-medium">方法3: Cookieをクリア</p>
                  <p className="text-xs">ブラウザの設定からnulab.comのCookieを削除</p>
                </div>
              </div>
            </AlertDescription>
          </Alert>


          {/* ログインボタン */}
          <Button
            onClick={handleBacklogLogin}
            disabled={isLoading}
            className="w-full h-12 text-base"
            size="lg"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                接続中...
              </>
            ) : (
              <>
                <svg
                  className="mr-2 h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
                </svg>
                Backlogアカウントでログイン
              </>
            )}
          </Button>

          <div className="text-center text-sm text-muted-foreground">
            <p>Backlogアカウントをお持ちでない方は</p>
            <p>スペース管理者にお問い合わせください</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}