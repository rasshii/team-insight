'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useState } from 'react'

interface TeamProductivityChartProps {
  teamId: number
}

// ダミーデータ（実際のAPIから取得するまでの仮データ）
const getProductivityData = (teamId: number, period: string) => {
  const weeklyData = [
    { week: '第1週', 完了タスク: 12, 新規タスク: 15, 効率性: 85 },
    { week: '第2週', 完了タスク: 18, 新規タスク: 16, 効率性: 92 },
    { week: '第3週', 完了タスク: 15, 新規タスク: 20, 効率性: 78 },
    { week: '第4週', 完了タスク: 22, 新規タスク: 18, 効率性: 95 },
  ]

  const monthlyData = [
    { month: '1月', 完了タスク: 45, 新規タスク: 50, 効率性: 82 },
    { month: '2月', 完了タスク: 52, 新規タスク: 48, 効率性: 88 },
    { month: '3月', 完了タスク: 58, 新規タスク: 55, 効率性: 90 },
    { month: '4月', 完了タスク: 65, 新規タスク: 60, 効率性: 93 },
    { month: '5月', 完了タスク: 70, 新規タスク: 68, 効率性: 95 },
    { month: '6月', 完了タスク: 68, 新規タスク: 70, 効率性: 91 },
  ]

  return period === 'weekly' ? weeklyData : monthlyData
}

const getVelocityData = (teamId: number) => {
  return [
    { スプリント: 'Sprint 1', 計画: 20, 実績: 18 },
    { スプリント: 'Sprint 2', 計画: 22, 実績: 25 },
    { スプリント: 'Sprint 3', 計画: 25, 実績: 23 },
    { スプリント: 'Sprint 4', 計画: 28, 実績: 30 },
    { スプリント: 'Sprint 5', 計画: 30, 実績: 32 },
    { スプリント: 'Sprint 6', 計画: 32, 実績: 35 },
  ]
}

export function TeamProductivityChart({ teamId }: TeamProductivityChartProps) {
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly')
  const productivityData = getProductivityData(teamId, period)
  const velocityData = getVelocityData(teamId)

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>生産性推移</CardTitle>
              <CardDescription>
                タスクの完了数と新規作成数の推移
              </CardDescription>
            </div>
            <Select value={period} onValueChange={(value) => setPeriod(value as 'weekly' | 'monthly')}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="weekly">週次</SelectItem>
                <SelectItem value="monthly">月次</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={productivityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey={period === 'weekly' ? 'week' : 'month'} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="完了タスク"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981' }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="新規タスク"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="効率性"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ fill: '#f59e0b' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>ベロシティチャート</CardTitle>
          <CardDescription>
            スプリントごとの計画と実績の比較
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={velocityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="スプリント" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="計画" fill="#94a3b8" />
                <Bar dataKey="実績" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}