'use client'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ExternalLink, Info } from 'lucide-react'

export function BacklogAccountGuide() {
  const spaceUrl = 'https://nulab-exam.backlog.jp'
  
  return (
    <Card className="w-full max-w-2xl mx-auto shadow-xl">
      <CardHeader>
        <CardTitle className="text-2xl">Team Insight - nulab-examスペース専用</CardTitle>
        <CardDescription>
          このツールはnulab-examスペースのメンバー専用です
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>別のBacklogアカウントでログイン中の場合</AlertTitle>
          <AlertDescription className="mt-2 space-y-2">
            <p>現在、別のBacklogスペースのアカウントでログインしているようです。</p>
            <p>Team Insightを使用するには、<strong>nulab-examスペース</strong>のアカウントでログインする必要があります。</p>
          </AlertDescription>
        </Alert>
        
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">ログイン手順</h3>
          
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                1
              </div>
              <div className="flex-1">
                <p className="font-medium">現在のNulabアカウントからログアウト</p>
                <p className="text-sm text-muted-foreground mt-1">
                  別のBacklogスペースでログイン中の場合は、一度ログアウトする必要があります。
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => window.open('https://apps.nulab.com/logout', '_blank')}
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Nulabからログアウト
                </Button>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                2
              </div>
              <div className="flex-1">
                <p className="font-medium">nulab-examスペースにログイン</p>
                <p className="text-sm text-muted-foreground mt-1">
                  ログアウト後、nulab-examスペースのアカウントでログインしてください。
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => window.open(spaceUrl, '_blank')}
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  nulab-examスペースへ
                </Button>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <div className="flex-1">
                <p className="font-medium">Team Insightに再アクセス</p>
                <p className="text-sm text-muted-foreground mt-1">
                  nulab-examスペースにログイン後、このページに戻ってログインボタンをクリックしてください。
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="border-t pt-4">
          <p className="text-sm text-muted-foreground">
            nulab-examスペースのアカウントをお持ちでない方は、スペース管理者にお問い合わせください。
          </p>
        </div>
      </CardContent>
    </Card>
  )
}