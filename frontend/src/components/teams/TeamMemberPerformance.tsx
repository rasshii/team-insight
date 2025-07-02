'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Shield, User, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { TeamMember, TeamRole } from '@/types/team'

interface TeamMemberPerformanceProps {
  teamId: number
  members: TeamMember[]
}

// ダミーデータ（実際のAPIから取得するまでの仮データ）
const getMemberPerformance = (memberId: number) => {
  const performances = [
    { completedTasks: 15, activeTasks: 3, efficiency: 92, trend: 'up' },
    { completedTasks: 12, activeTasks: 5, efficiency: 78, trend: 'down' },
    { completedTasks: 18, activeTasks: 2, efficiency: 88, trend: 'stable' },
    { completedTasks: 8, activeTasks: 7, efficiency: 65, trend: 'down' },
    { completedTasks: 20, activeTasks: 1, efficiency: 95, trend: 'up' },
  ]
  return performances[memberId % performances.length]
}

export function TeamMemberPerformance({ teamId, members }: TeamMemberPerformanceProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>メンバー別パフォーマンス</CardTitle>
        <CardDescription>
          各メンバーのタスク完了状況と生産性を表示します
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {members.map((member) => {
            const performance = getMemberPerformance(member.user_id)
            const initials = member.user.name
              .split(' ')
              .map((n) => n[0])
              .join('')
              .toUpperCase()
              .slice(0, 2)

            return (
              <div
                key={member.id}
                className="flex items-center gap-4 p-4 rounded-lg border"
              >
                <Avatar className="h-12 w-12">
                  <AvatarFallback>{initials}</AvatarFallback>
                </Avatar>

                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold">{member.user.name}</h4>
                    {member.role === TeamRole.TEAM_LEADER ? (
                      <Badge variant="default" className="gap-1">
                        <Shield className="h-3 w-3" />
                        リーダー
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="gap-1">
                        <User className="h-3 w-3" />
                        メンバー
                      </Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">完了タスク</p>
                      <p className="font-medium">{performance.completedTasks}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">進行中</p>
                      <p className="font-medium">{performance.activeTasks}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">効率性</p>
                      <div className="flex items-center gap-1">
                        <p className="font-medium">{performance.efficiency}%</p>
                        {performance.trend === 'up' && (
                          <TrendingUp className="h-3 w-3 text-green-500" />
                        )}
                        {performance.trend === 'down' && (
                          <TrendingDown className="h-3 w-3 text-red-500" />
                        )}
                        {performance.trend === 'stable' && (
                          <Minus className="h-3 w-3 text-gray-500" />
                        )}
                      </div>
                    </div>
                  </div>

                  <Progress value={performance.efficiency} className="h-2" />
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}