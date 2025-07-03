'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useState } from 'react'
import { useTeamProductivityTrend } from '@/hooks/queries/useTeams'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle } from 'lucide-react'

interface TeamProductivityChartProps {
  teamId: number
}

export function TeamProductivityChart({ teamId }: TeamProductivityChartProps) {
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('monthly')
  const { data: trendData, isLoading, error } = useTeamProductivityTrend(teamId, period)

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>生産性推移</CardTitle>
          <CardDescription>
            タスクの完了数と平均完了時間の推移
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[350px] w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error || !trendData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>生産性推移</CardTitle>
          <CardDescription>
            タスクの完了数と平均完了時間の推移
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-[350px] text-muted-foreground">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p>データの取得に失敗しました</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // データがない場合
  if (!trendData || trendData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>生産性推移</CardTitle>
          <CardDescription>
            タスクの完了数と平均完了時間の推移
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-[350px] text-muted-foreground">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p>データがありません</p>
            <p className="text-sm mt-2">タスクを作成・完了すると、ここに推移が表示されます</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>生産性推移</CardTitle>
            <CardDescription>
              タスクの完了数と平均完了時間の推移
            </CardDescription>
          </div>
          <Select value={period} onValueChange={(value) => setPeriod(value as 'daily' | 'weekly' | 'monthly')}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="daily">日次</SelectItem>
              <SelectItem value="weekly">週次</SelectItem>
              <SelectItem value="monthly">月次</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="period" 
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-background border rounded-lg shadow-lg p-3">
                        <p className="font-semibold">{label}</p>
                        {payload.map((entry: any, index: number) => (
                          <p key={index} className="text-sm" style={{ color: entry.color }}>
                            {entry.name}: {entry.value}
                            {entry.name === '平均完了時間' ? '日' : ''}
                            {entry.name === '効率性スコア' ? '%' : ''}
                          </p>
                        ))}
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="completed_tasks"
                name="完了タスク"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: '#10b981' }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avg_completion_time"
                name="平均完了時間"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6' }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="efficiency_score"
                name="効率性スコア"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ fill: '#f59e0b' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}