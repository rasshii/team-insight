"use client";

import React, { useEffect, useState } from "react";
import { healthService, HealthStatus, HealthCheckError } from "@/services/health.service";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle2, RefreshCw, Server, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

/**
 * ヘルスチェックコンポーネント
 *
 * バックエンドAPIの健全性を表示し、定期的に更新します。
 * APIとRedisの状態をリアルタイムで監視できます。
 */
export const HealthCheck: React.FC = () => {
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<HealthCheckError | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  // ヘルスチェックを実行
  const checkHealth = async () => {
    setLoading(true);
    setError(null);

    try {
      const healthStatus = await healthService.checkHealth();
      setStatus(healthStatus);
      setLastChecked(new Date());
    } catch (err) {
      setError(err as HealthCheckError);
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  // 初回実行と定期的な更新
  useEffect(() => {
    checkHealth();

    // 30秒ごとに自動更新
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  // ステータスに応じたアイコンを取得
  const getStatusIcon = (isHealthy: boolean) => {
    return isHealthy ? (
      <CheckCircle2 className="h-5 w-5 text-green-500" />
    ) : (
      <AlertCircle className="h-5 w-5 text-red-500" />
    );
  };

  // ステータスに応じたバッジの色を取得
  const getBadgeVariant = (isHealthy: boolean): "default" | "destructive" | "secondary" => {
    return isHealthy ? "default" : "destructive";
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">システム状態</CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={checkHealth}
            disabled={loading}
            className="h-8 w-8"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
        <CardDescription>
          {lastChecked && (
            <span className="text-xs">
              最終確認: {lastChecked.toLocaleTimeString("ja-JP")}
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{healthService.getErrorMessage(error)}</AlertDescription>
          </Alert>
        )}

        {status && (
          <>
            {/* 全体ステータス */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">全体</span>
              <div className="flex items-center gap-2">
                {getStatusIcon(healthService.isHealthy(status))}
                <Badge variant={getBadgeVariant(healthService.isHealthy(status))}>
                  {healthService.getStatusMessage(status.status)}
                </Badge>
              </div>
            </div>

            {/* サービス別ステータス */}
            <div className="space-y-3 border-t pt-3">
              {/* API */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 text-gray-500" />
                  <span className="text-sm">API サーバー</span>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(status.services.api === "healthy")}
                  <Badge
                    variant={getBadgeVariant(status.services.api === "healthy")}
                    className="text-xs"
                  >
                    {healthService.getStatusMessage(status.services.api)}
                  </Badge>
                </div>
              </div>

              {/* Redis */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-gray-500" />
                  <span className="text-sm">Redis キャッシュ</span>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(status.services.redis === "healthy")}
                  <Badge
                    variant={getBadgeVariant(status.services.redis === "healthy")}
                    className="text-xs"
                  >
                    {healthService.getStatusMessage(status.services.redis)}
                  </Badge>
                </div>
              </div>
            </div>

            {/* メッセージ */}
            {status.message && (
              <div className="border-t pt-3">
                <p className="text-xs text-gray-500">{status.message}</p>
              </div>
            )}
          </>
        )}

        {loading && !status && !error && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        )}
      </CardContent>
    </Card>
  );
};