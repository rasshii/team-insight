'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Loader2, Mail, CheckCircle, XCircle, RefreshCw } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { authService } from '@/services/auth.service'
import { useToast } from '@/hooks/use-toast'

function VerifyEmailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'pending'>('pending')
  const [email, setEmail] = useState<string>('')
  const [isResending, setIsResending] = useState(false)

  const token = searchParams?.get('token')
  const emailParam = searchParams?.get('email')

  useEffect(() => {
    if (emailParam) {
      setEmail(decodeURIComponent(emailParam))
    }
  }, [emailParam])

  useEffect(() => {
    if (token) {
      verifyEmail(token)
    }
  }, [token])

  const verifyEmail = async (verificationToken: string) => {
    setStatus('loading')
    try {
      const response = await authService.confirmEmailVerification({ token: verificationToken })
      
      setStatus('success')
      toast({
        title: 'メールアドレスを確認しました',
        description: response.message,
      })

      // 3秒後にログインページへリダイレクト
      setTimeout(() => {
        router.push('/auth/login')
      }, 3000)
    } catch (error: any) {
      console.error('Email verification error:', error)
      setStatus('error')
      
      const errorMessage = error.response?.data?.error?.message || 
                          error.response?.data?.detail || 
                          'メールアドレスの確認に失敗しました'
      
      toast({
        title: 'エラー',
        description: errorMessage,
        variant: 'destructive',
      })
    }
  }

  const handleResendEmail = async () => {
    if (!email) {
      toast({
        title: 'エラー',
        description: 'メールアドレスが指定されていません',
        variant: 'destructive',
      })
      return
    }

    setIsResending(true)
    try {
      const response = await authService.requestEmailVerification({ email })
      
      toast({
        title: '確認メールを送信しました',
        description: response.message,
      })
    } catch (error: any) {
      console.error('Resend email error:', error)
      
      const errorMessage = error.response?.data?.error?.message || 
                          error.response?.data?.detail || 
                          '確認メールの送信に失敗しました'
      
      toast({
        title: 'エラー',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setIsResending(false)
    }
  }

  return (
    <div className="container relative min-h-screen flex-col items-center justify-center grid lg:max-w-none lg:px-0">
      <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[450px]">
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">
              メールアドレスの確認
            </CardTitle>
            <CardDescription className="text-center">
              {status === 'pending' && 'メールアドレスの確認を行います'}
              {status === 'loading' && 'メールアドレスを確認しています...'}
              {status === 'success' && 'メールアドレスの確認が完了しました'}
              {status === 'error' && 'メールアドレスの確認に失敗しました'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {status === 'pending' && !token && (
              <>
                <div className="flex flex-col items-center space-y-4">
                  <div className="rounded-full bg-muted p-4">
                    <Mail className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <div className="text-center space-y-2">
                    <p className="text-sm text-muted-foreground">
                      アカウント登録ありがとうございます。
                    </p>
                    {email && (
                      <p className="text-sm font-medium">
                        {email} に確認メールを送信しました。
                      </p>
                    )}
                    <p className="text-sm text-muted-foreground">
                      メール内のリンクをクリックして、メールアドレスの確認を完了してください。
                    </p>
                  </div>
                </div>
                
                <Alert>
                  <AlertDescription>
                    メールが届かない場合は、迷惑メールフォルダをご確認いただくか、
                    下のボタンから再送信してください。
                  </AlertDescription>
                </Alert>

                {email && (
                  <Button
                    onClick={handleResendEmail}
                    disabled={isResending}
                    variant="outline"
                    className="w-full"
                  >
                    {isResending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        送信中...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        確認メールを再送信
                      </>
                    )}
                  </Button>
                )}
              </>
            )}

            {status === 'loading' && (
              <div className="flex flex-col items-center space-y-4 py-8">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">
                  メールアドレスを確認しています...
                </p>
              </div>
            )}

            {status === 'success' && (
              <div className="flex flex-col items-center space-y-4 py-8">
                <div className="rounded-full bg-green-100 p-4">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <div className="text-center space-y-2">
                  <p className="text-lg font-medium">
                    メールアドレスの確認が完了しました！
                  </p>
                  <p className="text-sm text-muted-foreground">
                    まもなくログインページへ移動します...
                  </p>
                </div>
              </div>
            )}

            {status === 'error' && (
              <div className="flex flex-col items-center space-y-4 py-8">
                <div className="rounded-full bg-red-100 p-4">
                  <XCircle className="h-8 w-8 text-red-600" />
                </div>
                <div className="text-center space-y-2">
                  <p className="text-lg font-medium">
                    メールアドレスの確認に失敗しました
                  </p>
                  <p className="text-sm text-muted-foreground">
                    確認リンクの有効期限が切れているか、
                    既に使用されている可能性があります。
                  </p>
                </div>
                
                {email && (
                  <Button
                    onClick={handleResendEmail}
                    disabled={isResending}
                    variant="outline"
                    className="w-full"
                  >
                    {isResending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        送信中...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        確認メールを再送信
                      </>
                    )}
                  </Button>
                )}
              </div>
            )}
          </CardContent>
          <CardFooter>
            <div className="text-center text-sm w-full">
              <Link href="/auth/login" className="text-primary hover:underline">
                ログインページへ戻る
              </Link>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">読み込み中...</p>
          </div>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  )
}