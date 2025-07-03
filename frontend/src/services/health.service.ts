/**
 * ヘルスチェックサービス
 *
 * このモジュールは、バックエンドAPIの健全性チェックを行います。
 * APIとRedisの状態を監視し、システム全体の健全性を確認します。
 */

import { apiClient } from '@/lib/api-client'
import type { components } from "@/types/api";

// 自動生成された型を使用
export type HealthStatus = components["schemas"]["HealthResponse"];
export type ServiceStatus = components["schemas"]["ServiceStatus"];

export interface HealthCheckError {
  error: string;
  message: string;
}

/**
 * ヘルスチェック関連のAPIサービス
 * 
 * React Queryと組み合わせて使用するためのシンプルな関数群
 */
export const healthService = {
  /**
   * ヘルスチェックを実行
   */
  async checkHealth(): Promise<HealthStatus> {
    return await apiClient.get('/health/', {
      timeout: 5000, // 5秒でタイムアウト
    })
  },

}

/**
 * ヘルスチェックユーティリティ
 */
export const healthUtils = {
  /**
   * サービス全体が健全かどうかを判定
   */
  isHealthy(status: HealthStatus): boolean {
    return (
      status.status === "healthy" &&
      status.services.api === "healthy" &&
      status.services.database === "healthy" &&
      status.services.redis === "healthy"
    );
  },

  /**
   * サービスの状態を日本語メッセージに変換
   */
  getStatusMessage(status: "healthy" | "unhealthy"): string {
    return status === "healthy" ? "正常" : "異常";
  },

  /**
   * エラーメッセージを取得
   */
  getErrorMessage(error: any): string {
    if (error?.response?.status === 503) {
      return "APIサーバーに接続できません";
    }
    return error?.message || "システムエラーが発生しました";
  },
}