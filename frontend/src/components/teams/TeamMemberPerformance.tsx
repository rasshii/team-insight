'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Shield, User, TrendingUp, TrendingDown, Minus, Loader2 } from 'lucide-react'
import { TeamMember, TeamRole } from '@/types/team'
import { useTeamMembersPerformance } from '@/hooks/queries/useTeams'
import { Skeleton } from '@/components/ui/skeleton'

interface TeamMemberPerformanceProps {
  teamId: number
  members: TeamMember[]
}

export function TeamMemberPerformance({ teamId, members }: TeamMemberPerformanceProps) {
  const { data: performanceData, isLoading } = useTeamMembersPerformance(teamId)

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
          {isLoading ? (
            // ローディング中のスケルトン
            Array.from({ length: members.length }).map((_, index) => (
              <div key={index} className="flex items-center gap-4 p-4 rounded-lg border">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <div className="grid grid-cols-3 gap-4">
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-4 w-16" />
                  </div>
                  <Skeleton className="h-2 w-full" />
                </div>
              </div>
            ))
          ) : (
            members.map((member) => {
              const performance = performanceData?.find((p: any) => p.user_id === member.user_id) || {
                completed_tasks: 0,
                active_tasks: 0,
                efficiency: 0,
                trend: 'stable'
              }
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
                      <p className="font-medium">{performance.completed_tasks}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">進行中</p>
                      <p className="font-medium">{performance.active_tasks}</p>
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
          })
          )}
        </div>
      </CardContent>
    </Card>
  )
}