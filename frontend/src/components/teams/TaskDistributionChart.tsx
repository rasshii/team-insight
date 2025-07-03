'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { useTeamTaskDistribution } from '@/hooks/queries/useTeams'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle } from 'lucide-react'

interface TaskDistributionChartProps {
  teamId: number
}

export function TaskDistributionChart({ teamId }: TaskDistributionChartProps) {
  const { data: distributionData, isLoading, error } = useTeamTaskDistribution(teamId)

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg shadow-lg p-3">
          <p className="font-semibold">{payload[0].name}</p>
          <p className="text-sm">
            {payload[0].value} タスク
          </p>
        </div>
      )
    }
    return null
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>メンバー別タスク分配</CardTitle>
          <CardDescription>
            各メンバーが担当しているタスクの数
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error || !distributionData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>メンバー別タスク分配</CardTitle>
          <CardDescription>
            各メンバーが担当しているタスクの数
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

  // データがない場合
  if (!distributionData.data || distributionData.data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>メンバー別タスク分配</CardTitle>
          <CardDescription>
            各メンバーが担当しているタスクの数
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p>タスクデータがありません</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Rechartsで使用するデータ形式に変換
  const chartData = distributionData.labels.map((label: string, index: number) => ({
    name: label,
    value: distributionData.data[index],
    color: distributionData.backgroundColor[index % distributionData.backgroundColor.length]
  }))

  // 合計を計算
  const totalTasks = distributionData.data.reduce((sum: number, value: number) => sum + value, 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>メンバー別タスク分配</CardTitle>
        <CardDescription>
          各メンバーが担当しているタスクの数（合計: {totalTasks}件）
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 space-y-2">
          {chartData.map((item: any) => (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm">{item.name}</span>
              </div>
              <span className="text-sm font-medium">{item.value} タスク</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}