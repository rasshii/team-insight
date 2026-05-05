'use client'

import { AlertCircle, Info } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

/**
 * ログイン画面 (Phase 6 で Backlog OAuth ボタンを削除済み)
 *
 * Phase 1 でローカル ID/パスワード認証フォーム (react-hook-form + zod) を実装する。
 * それまでは「移行中」のメッセージを表示する暫定実装。
 */
export function SimpleLoginContent() {
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
          <Alert>
            <Info className="h-4 w-4" />
            <AlertTitle>独立アプリへ移行中</AlertTitle>
            <AlertDescription className="text-sm">
              Backlog 連携を廃止し、ID/パスワード認証への移行作業中です。
              新ログイン画面は Phase 1 で実装予定です。
            </AlertDescription>
          </Alert>

          <Alert variant="default" className="border-orange-200 bg-orange-50 dark:bg-orange-950">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            <AlertTitle className="text-orange-800 dark:text-orange-200">管理者の方へ</AlertTitle>
            <AlertDescription className="mt-2 space-y-2 text-sm text-orange-700 dark:text-orange-300">
              <p>初期管理者アカウントの作成は <code>make seed-default-org</code> で実行できます (Phase 7 以降)。</p>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  )
}
