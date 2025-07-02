'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface TaskDistributionChartProps {
  teamId: number
}

// ダミーデータ（実際のAPIから取得するまでの仮データ）
const getTaskDistribution = (teamId: number) => {
  const distributions = [
    [
      { name: '未着手', value: 15, color: '#94a3b8' },
      { name: '進行中', value: 25, color: '#3b82f6' },
      { name: 'レビュー中', value: 10, color: '#f59e0b' },
      { name: '完了', value: 50, color: '#10b981' },
    ],
    [
      { name: '未着手', value: 20, color: '#94a3b8' },
      { name: '進行中', value: 30, color: '#3b82f6' },
      { name: 'レビュー中', value: 15, color: '#f59e0b' },
      { name: '完了', value: 35, color: '#10b981' },
    ],
  ]
  return distributions[teamId % distributions.length]
}

const getMemberDistribution = (teamId: number) => {
  const distributions = [
    [
      { name: '田中太郎', value: 30, color: '#3b82f6' },
      { name: '山田花子', value: 25, color: '#8b5cf6' },
      { name: '佐藤次郎', value: 20, color: '#ec4899' },
      { name: '鈴木三郎', value: 15, color: '#f59e0b' },
      { name: 'その他', value: 10, color: '#94a3b8' },
    ],
    [
      { name: '高橋一郎', value: 35, color: '#3b82f6' },
      { name: '伊藤美咲', value: 28, color: '#8b5cf6' },
      { name: '渡辺健', value: 22, color: '#ec4899' },
      { name: 'その他', value: 15, color: '#94a3b8' },
    ],
  ]
  return distributions[teamId % distributions.length]
}

export function TaskDistributionChart({ teamId }: TaskDistributionChartProps) {
  const taskStatusData = getTaskDistribution(teamId)
  const memberData = getMemberDistribution(teamId)

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg shadow-lg p-3">
          <p className="font-semibold">{payload[0].name}</p>
          <p className="text-sm">
            {payload[0].value} タスク ({payload[0].payload.percentage}%)
          </p>
        </div>
      )
    }
    return null
  }

  // パーセンテージを計算
  const totalTasks = taskStatusData.reduce((sum, item) => sum + item.value, 0)
  const dataWithPercentage = taskStatusData.map((item) => ({
    ...item,
    percentage: Math.round((item.value / totalTasks) * 100),
  }))

  const totalMemberTasks = memberData.reduce((sum, item) => sum + item.value, 0)
  const memberDataWithPercentage = memberData.map((item) => ({
    ...item,
    percentage: Math.round((item.value / totalMemberTasks) * 100),
  }))

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>タスクステータス分布</CardTitle>
          <CardDescription>
            タスクの現在の状態別分布
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={dataWithPercentage}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name}: ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {dataWithPercentage.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {dataWithPercentage.map((item) => (
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

      <Card>
        <CardHeader>
          <CardTitle>メンバー別タスク分配</CardTitle>
          <CardDescription>
            各メンバーが担当しているタスクの割合
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={memberDataWithPercentage}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ percentage }) => `${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {memberDataWithPercentage.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {memberDataWithPercentage.map((item) => (
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
    </div>
  )
}