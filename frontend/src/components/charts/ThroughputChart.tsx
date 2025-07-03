"use client";

import React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ThroughputData {
  date: string;
  completed_tasks: number;
  story_points: number;
}

interface ThroughputChartProps {
  data?: ThroughputData[];
  isLoading?: boolean;
  error?: Error | null;
}

export const ThroughputChart: React.FC<ThroughputChartProps> = ({
  data = [],
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return <Skeleton className="h-full w-full" />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <TrendingUp className="h-4 w-4" />
        <AlertDescription>
          データの読み込みに失敗しました: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">
          スループットデータがありません
        </p>
      </div>
    );
  }

  // 簡易的なバーチャート表示
  const maxTasks = Math.max(...data.map(d => d.completed_tasks));
  const maxPoints = Math.max(...data.map(d => d.story_points));

  return (
    <div className="space-y-4 h-full">
      <div className="text-sm text-muted-foreground">
        過去のタスク完了数とストーリーポイントの推移
      </div>
      <div className="space-y-3 overflow-y-auto" style={{ maxHeight: 'calc(100% - 80px)' }}>
        {data.slice(-10).map((item, index) => (
          <div key={`throughput-${item.date}-${index}`} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {new Date(item.date).toLocaleDateString('ja-JP')}
              </span>
              <div className="flex gap-4">
                <span>タスク: {item.completed_tasks}</span>
                <span>ポイント: {item.story_points}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <div className="flex-1 bg-muted rounded-sm h-4 relative overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-primary/80"
                  style={{
                    width: `${(item.completed_tasks / maxTasks) * 100}%`
                  }}
                />
              </div>
              <div className="flex-1 bg-muted rounded-sm h-4 relative overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-blue-500/80"
                  style={{
                    width: `${(item.story_points / maxPoints) * 100}%`
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-4 text-sm text-muted-foreground pt-2">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-primary/80 rounded-sm" />
          <span>完了タスク数</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500/80 rounded-sm" />
          <span>ストーリーポイント</span>
        </div>
      </div>
    </div>
  );
};