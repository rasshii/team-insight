'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CheckCircle2, PlayCircle, AlertCircle, MessageSquare, GitPullRequest } from 'lucide-react'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'

interface TeamActivityTimelineProps {
  teamId: number
}

// ダミーデータ（実際のAPIから取得するまでの仮データ）
const getActivities = (teamId: number) => {
  const now = new Date()
  const activities = [
    {
      id: 1,
      type: 'task_completed',
      user: { name: '田中太郎', initials: 'TT' },
      title: 'ユーザー認証機能の実装',
      timestamp: new Date(now.getTime() - 1000 * 60 * 30), // 30分前
      details: 'バックエンドAPIとフロントエンドの統合完了',
    },
    {
      id: 2,
      type: 'task_started',
      user: { name: '山田花子', initials: 'YH' },
      title: 'ダッシュボードのデザイン更新',
      timestamp: new Date(now.getTime() - 1000 * 60 * 60 * 2), // 2時間前
      details: '新しいUIコンポーネントの実装開始',
    },
    {
      id: 3,
      type: 'comment',
      user: { name: '佐藤次郎', initials: 'SJ' },
      title: 'コードレビューのフィードバック',
      timestamp: new Date(now.getTime() - 1000 * 60 * 60 * 4), // 4時間前
      details: 'パフォーマンス改善の提案を追加',
    },
    {
      id: 4,
      type: 'pr_merged',
      user: { name: '鈴木三郎', initials: 'SS' },
      title: 'feature/user-profile ブランチをマージ',
      timestamp: new Date(now.getTime() - 1000 * 60 * 60 * 6), // 6時間前
      details: 'ユーザープロフィール機能の実装完了',
    },
    {
      id: 5,
      type: 'issue_created',
      user: { name: '高橋一郎', initials: 'TI' },
      title: 'バグ報告: ログイン時のエラー',
      timestamp: new Date(now.getTime() - 1000 * 60 * 60 * 24), // 1日前
      details: '特定の条件下でログインが失敗する問題',
    },
  ]

  return activities
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'task_completed':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'task_started':
      return <PlayCircle className="h-4 w-4 text-blue-500" />
    case 'comment':
      return <MessageSquare className="h-4 w-4 text-purple-500" />
    case 'pr_merged':
      return <GitPullRequest className="h-4 w-4 text-orange-500" />
    case 'issue_created':
      return <AlertCircle className="h-4 w-4 text-red-500" />
    default:
      return null
  }
}

const getActivityLabel = (type: string) => {
  switch (type) {
    case 'task_completed':
      return { label: 'タスク完了', variant: 'default' as const }
    case 'task_started':
      return { label: 'タスク開始', variant: 'secondary' as const }
    case 'comment':
      return { label: 'コメント', variant: 'outline' as const }
    case 'pr_merged':
      return { label: 'PRマージ', variant: 'default' as const }
    case 'issue_created':
      return { label: 'Issue作成', variant: 'destructive' as const }
    default:
      return { label: 'その他', variant: 'secondary' as const }
  }
}

export function TeamActivityTimeline({ teamId }: TeamActivityTimelineProps) {
  const activities = getActivities(teamId)

  return (
    <Card>
      <CardHeader>
        <CardTitle>最近のアクティビティ</CardTitle>
        <CardDescription>
          チームメンバーの活動履歴
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-4">
            {activities.map((activity, index) => {
              const { label, variant } = getActivityLabel(activity.type)
              const isLast = index === activities.length - 1

              return (
                <div key={activity.id} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback>{activity.user.initials}</AvatarFallback>
                    </Avatar>
                    {!isLast && (
                      <div className="w-px h-full bg-border mt-2" />
                    )}
                  </div>

                  <div className="flex-1 space-y-2 pb-6">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          {getActivityIcon(activity.type)}
                          <span className="font-semibold">{activity.user.name}</span>
                          <Badge variant={variant} className="text-xs">
                            {label}
                          </Badge>
                        </div>
                        <h4 className="text-sm font-medium">{activity.title}</h4>
                        <p className="text-sm text-muted-foreground">
                          {activity.details}
                        </p>
                      </div>
                      <time className="text-xs text-muted-foreground">
                        {format(activity.timestamp, 'HH:mm', { locale: ja })}
                        <br />
                        {format(activity.timestamp, 'MM/dd', { locale: ja })}
                      </time>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}