"use client";

import React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface BottleneckData {
  task_id: number;
  task_key: string;
  task_title: string;
  blocked_days: number;
  blocking_reason: string;
  assignee_name: string;
  status: string;
}

interface BottleneckChartProps {
  data?: BottleneckData[];
  isLoading?: boolean;
  error?: Error | null;
}

export const BottleneckChart: React.FC<BottleneckChartProps> = ({
  data = [],
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return <Skeleton className="h-[300px] w-full" />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          データの読み込みに失敗しました: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[300px] text-center">
        <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">
          現在ボトルネックとなっているタスクはありません
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data.map((item, index) => (
        <div
          key={item.task_id || `bottleneck-${index}`}
          className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-sm text-muted-foreground">
                  {item.task_key}
                </span>
                <span className="font-medium">{item.task_title}</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div key={`${item.task_id}-blocked-days`}>
                  <span className="text-muted-foreground">停滞日数: </span>
                  <span className="font-medium text-destructive">
                    {item.blocked_days}日
                  </span>
                </div>
                <div key={`${item.task_id}-assignee`}>
                  <span className="text-muted-foreground">担当者: </span>
                  <span>{item.assignee_name || "未割当"}</span>
                </div>
                <div key={`${item.task_id}-status`}>
                  <span className="text-muted-foreground">ステータス: </span>
                  <span>{item.status}</span>
                </div>
                <div key={`${item.task_id}-reason`}>
                  <span className="text-muted-foreground">原因: </span>
                  <span>{item.blocking_reason}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};