'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2, Eye, EyeOff } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
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

// バリデーションスキーマ
const signupSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z
    .string()
    .min(8, 'パスワードは8文字以上必要です')
    .regex(/[A-Z]/, 'パスワードには大文字を含める必要があります')
    .regex(/[a-z]/, 'パスワードには小文字を含める必要があります')
    .regex(/[0-9]/, 'パスワードには数字を含める必要があります')
    .regex(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/, 'パスワードには特殊文字を含める必要があります'),
  confirmPassword: z.string(),
  name: z.string().min(1, '名前を入力してください').max(100, '名前は100文字以内で入力してください'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'パスワードが一致しません',
  path: ['confirmPassword'],
})

type SignupFormData = z.infer<typeof signupSchema>

export default function SignupPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const form = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      name: '',
    },
  })

  const onSubmit = async (data: SignupFormData) => {
    setIsLoading(true)
    try {
      const response = await authService.signup({
        email: data.email,
        password: data.password,
        name: data.name,
      })

      toast({
        title: 'アカウントを作成しました',
        description: response.message,
      })

      // メール確認ページへリダイレクト
      router.push(`/auth/verify-email?email=${encodeURIComponent(data.email)}`)
    } catch (error: any) {
      console.error('Signup error:', error)
      
      // エラーメッセージの表示
      const errorMessage = error.response?.data?.error?.message || 
                          error.response?.data?.detail || 
                          'アカウントの作成に失敗しました'
      
      toast({
        title: 'エラー',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Backlog OAuth認証の開始
  const handleBacklogSignup = async () => {
    try {
      const { authorization_url, state } = await authService.getAuthorizationUrl()
      authService.saveOAuthState(state)
      window.location.href = authorization_url
    } catch (error) {
      console.error('Failed to get authorization URL:', error)
      toast({
        title: 'エラー',
        description: 'Backlog認証の開始に失敗しました',
        variant: 'destructive',
      })
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
              Team Insightで、チームの生産性を可視化し、
              データドリブンな意思決定を実現しましょう。
            </p>
            <footer className="text-sm">チーム全体のパフォーマンス向上へ</footer>
          </blockquote>
        </div>
      </div>
      <div className="p-8">
        <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[450px]">
          <Card>
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl font-bold text-center">アカウント作成</CardTitle>
              <CardDescription className="text-center">
                Team Insightを始めるためのアカウントを作成します
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Button
                  variant="outline"
                  onClick={handleBacklogSignup}
                  disabled={isLoading}
                  className="w-full"
                >
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
                  Backlogアカウントで登録
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
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>名前</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="山田太郎"
                            disabled={isLoading}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

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
                            disabled={isLoading}
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
                        <FormLabel>パスワード</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input
                              type={showPassword ? 'text' : 'password'}
                              placeholder="••••••••"
                              disabled={isLoading}
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
                        <FormDescription className="text-xs">
                          8文字以上で、大文字・小文字・数字・特殊文字を含む
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>パスワード（確認）</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input
                              type={showConfirmPassword ? 'text' : 'password'}
                              placeholder="••••••••"
                              disabled={isLoading}
                              {...field}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            >
                              {showConfirmPassword ? (
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

                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        アカウントを作成中...
                      </>
                    ) : (
                      'アカウントを作成'
                    )}
                  </Button>
                </form>
              </Form>

              <div className="text-center text-sm text-muted-foreground">
                利用規約とプライバシーポリシーに同意の上、アカウントを作成してください
              </div>
            </CardContent>
            <CardFooter>
              <div className="text-center text-sm w-full">
                すでにアカウントをお持ちですか？{' '}
                <Link href="/auth/login" className="text-primary hover:underline">
                  ログイン
                </Link>
              </div>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}