'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2, Eye, EyeOff, LogIn } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { authService } from '@/services/auth.service'
import { useToast } from '@/hooks/use-toast'
import { useAppDispatch } from '@/store/hooks'
import { setUser } from '@/store/slices/authSlice'

// バリデーションスキーマ
const loginSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(1, 'パスワードを入力してください'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const dispatch = useAppDispatch()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [isBacklogLoading, setIsBacklogLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [loginError, setLoginError] = useState<string | null>(null)

  // 開発時のテスト用: testパラメータがある場合は/settings/backlogへリダイレクト
  const testMode = searchParams?.get('test') === 'backlog'
  const from = testMode ? '/settings/backlog' : (searchParams?.get('from') || '/dashboard/personal')
  const error = searchParams?.get('error')

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  // メール/パスワードでのログイン
  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    setLoginError(null) // エラーをクリア
    try {
      const response = await authService.login(data)
      
      // ユーザー情報をストアに保存
      dispatch(setUser(response.user))
      
      toast({
        title: 'ログインしました',
        description: 'ダッシュボードへ移動します',
      })

      // 元のページへリダイレクト
      router.push(from)
    } catch (error: any) {
      console.error('Login error:', error)
      
      // エラーメッセージの表示
      const errorMessage = error.response?.data?.error?.message || 
                          error.response?.data?.detail || 
                          'ログインに失敗しました'
      
      // フォーム上部にエラーを表示
      setLoginError(errorMessage)
      
      // トーストも表示（より目立つように）
      toast({
        title: 'ログインエラー',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Backlog OAuth認証の開始
  const handleBacklogLogin = async (forceAccountSelection: boolean = false) => {
    setIsBacklogLoading(true)
    try {
      const { authorization_url, state } = await authService.getAuthorizationUrl(forceAccountSelection)
      authService.saveOAuthState(state)
      window.location.href = authorization_url
    } catch (error) {
      console.error('Failed to get authorization URL:', error)
      toast({
        title: 'エラー',
        description: 'Backlog認証の開始に失敗しました',
        variant: 'destructive',
      })
      setIsBacklogLoading(false)
    }
  }

  return (
    <div className="container relative min-h-screen flex-col items-center justify-center grid lg:max-w-none lg:grid-cols-2 lg:px-0">
      <div className="relative hidden h-full flex-col bg-muted p-10 text-white dark:border-r lg:flex">
        <div className="absolute inset-0 bg-gradient-to-b from-primary to-primary-foreground" />
        <div className="relative z-20 flex items-center text-lg font-medium">
          <Link href="/">Team Insight</Link>
        </div>
        <div className="relative z-20 mt-auto">
          <blockquote className="space-y-2">
            <p className="text-lg">
              チームの生産性を可視化し、ボトルネックを特定。
              データに基づいた改善でプロジェクトを成功へ導きます。
            </p>
            <footer className="text-sm">継続的な改善のパートナー</footer>
          </blockquote>
        </div>
      </div>
      <div className="p-8">
        <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[450px]">
          <Card>
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl font-bold text-center">ログイン</CardTitle>
              <CardDescription className="text-center">
                Team Insightにログインしてダッシュボードにアクセス
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {(error || loginError) && (
                <Alert variant="destructive">
                  <AlertDescription>
                    {loginError || (error === 'auth_failed'
                      ? '認証に失敗しました。もう一度お試しください。'
                      : 'エラーが発生しました。')}
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleBacklogLogin(false)}
                  disabled={isLoading || isBacklogLoading}
                  className="w-full"
                >
                  {isBacklogLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      接続中...
                    </>
                  ) : (
                    <>
                      <svg
                        className="mr-2 h-4 w-4"
                        aria-hidden="true"
                        focusable="false"
                        data-prefix="fab"
                        data-icon="backlog"
                        role="img"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                      >
                        <path
                          fill="currentColor"
                          d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"
                        />
                      </svg>
                      Backlogアカウントでログイン
                    </>
                  )}
                </Button>
                
                <Button
                  variant="ghost"
                  onClick={() => handleBacklogLogin(true)}
                  disabled={isLoading || isBacklogLoading}
                  className="w-full text-sm text-muted-foreground hover:text-foreground"
                >
                  <svg
                    className="mr-2 h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                  別のBacklogアカウントでログイン
                </Button>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <Separator />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">または</span>
                </div>
              </div>

              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>メールアドレス</FormLabel>
                        <FormControl>
                          <Input
                            type="email"
                            placeholder="name@example.com"
                            disabled={isLoading || isBacklogLoading}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex items-center justify-between">
                          <FormLabel>パスワード</FormLabel>
                          <Link 
                            href="/auth/forgot-password" 
                            className="text-sm text-primary hover:underline"
                          >
                            パスワードを忘れた方
                          </Link>
                        </div>
                        <FormControl>
                          <div className="relative">
                            <Input
                              type={showPassword ? 'text' : 'password'}
                              placeholder="••••••••"
                              disabled={isLoading || isBacklogLoading}
                              {...field}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                              onClick={() => setShowPassword(!showPassword)}
                            >
                              {showPassword ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={isLoading || isBacklogLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ログイン中...
                      </>
                    ) : (
                      <>
                        <LogIn className="mr-2 h-4 w-4" />
                        ログイン
                      </>
                    )}
                  </Button>
                </form>
              </Form>

              <div className="text-center text-sm text-muted-foreground">
                ログインすることで、利用規約とプライバシーポリシーに同意したものとみなされます
              </div>
            </CardContent>
            <CardFooter>
              <div className="text-center text-sm w-full">
                アカウントをお持ちでない方は{' '}
                <Link href="/auth/signup" className="text-primary hover:underline">
                  新規登録
                </Link>
              </div>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}