'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CheckCircle2, PlayCircle, Plus, Edit, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { useTeamActivities } from '@/hooks/queries/useTeams'
import { Skeleton } from '@/components/ui/skeleton'

interface TeamActivityTimelineProps {
  teamId: number
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'in_progress':
      return <PlayCircle className="h-4 w-4 text-blue-500" />
    case 'created':
      return <Plus className="h-4 w-4 text-purple-500" />
    case 'updated':
      return <Edit className="h-4 w-4 text-orange-500" />
    default:
      return <AlertCircle className="h-4 w-4 text-gray-500" />
  }
}

const getActivityLabel = (type: string) => {
  switch (type) {
    case 'completed':
      return { label: 'タスク完了', variant: 'default' as const }
    case 'in_progress':
      return { label: 'タスク開始', variant: 'secondary' as const }
    case 'created':
      return { label: '新規作成', variant: 'outline' as const }
    case 'updated':
      return { label: '更新', variant: 'outline' as const }
    default:
      return { label: 'その他', variant: 'secondary' as const }
  }
}

export function TeamActivityTimeline({ teamId }: TeamActivityTimelineProps) {
  const { data: activities, isLoading, error } = useTeamActivities(teamId, 20)

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>最近のアクティビティ</CardTitle>
          <CardDescription>
            チームメンバーの活動履歴
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-3 w-[300px]" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !activities) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>最近のアクティビティ</CardTitle>
          <CardDescription>
            チームメンバーの活動履歴
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p>データの取得に失敗しました</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!activities || activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>最近のアクティビティ</CardTitle>
          <CardDescription>
            チームメンバーの活動履歴
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p>アクティビティがありません</p>
            <p className="text-sm mt-2">タスクの作成・更新を行うと、ここに表示されます</p>
          </div>
        </CardContent>
      </Card>
    )
  }

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
            {activities.map((activity: any, index: number) => {
              const { label, variant } = getActivityLabel(activity.type)
              const isLast = index === activities.length - 1
              const initials = activity.user.name
                .split(' ')
                .map((n: string) => n[0])
                .join('')
                .toUpperCase()
                .slice(0, 2)

              const timestamp = new Date(activity.timestamp)

              return (
                <div key={activity.id} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback>{initials}</AvatarFallback>
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
                          {activity.message}
                        </p>
                      </div>
                      <time className="text-xs text-muted-foreground">
                        {format(timestamp, 'HH:mm', { locale: ja })}
                        <br />
                        {format(timestamp, 'MM/dd', { locale: ja })}
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