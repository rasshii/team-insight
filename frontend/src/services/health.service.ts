/**
 * ヘルスチェックサービス
 *
 * このモジュールは、バックエンドAPIの健全性チェックを行います。
 * APIとRedisの状態を監視し、システム全体の健全性を確認します。
 */

import axios from "axios";
import { env } from "@/config/env";
import type { components } from "@/types/api";

// APIのベースURL
const API_BASE_URL = env.get("NEXT_PUBLIC_API_URL");

// 自動生成された型を使用
export type HealthStatus = components["schemas"]["HealthResponse"];
export type ServiceStatus = components["schemas"]["ServiceStatus"];

export interface HealthCheckError {
  error: string;
  message: string;
}

/**
 * ヘルスチェックサービスクラス
 *
 * バックエンドAPIの健全性を定期的にチェックし、
 * システムの状態を監視します。
 */
class HealthService {
  /**
   * ヘルスチェックを実行
   *
   * バックエンドの/healthエンドポイントを呼び出し、
   * APIとRedisの状態を取得します。
   *
   * @returns ヘルスステータス
   * @throws ヘルスチェックに失敗した場合
   */
  async checkHealth(): Promise<HealthStatus> {
    try {
      const response = await axios.get<HealthStatus>(
        `${API_BASE_URL}/health`,
        {
          timeout: 5000, // 5秒でタイムアウト
        }
      );
      return response.data;
    } catch (error) {
      // エラーをHealthCheckError型に変換
      if (axios.isAxiosError(error)) {
        throw {
          error: "API_ERROR",
          message: error.message || "APIへの接続に失敗しました",
        } as HealthCheckError;
      }
      throw {
        error: "UNKNOWN_ERROR",
        message: "予期しないエラーが発生しました",
      } as HealthCheckError;
    }
  }

  /**
   * サービス全体が健全かどうかを判定
   *
   * 全てのサービスが健全な場合のみtrueを返します。
   *
   * @param status ヘルスステータス
   * @returns 全体が健全な場合true
   */
  isHealthy(status: HealthStatus): boolean {
    return (
      status.status === "healthy" &&
      status.services.api === "healthy" &&
      status.services.database === "healthy" &&
      status.services.redis === "healthy"
    );
  }

  /**
   * サービスの状態を日本語メッセージに変換
   *
   * @param status サービスの状態
   * @returns 日本語の状態メッセージ
   */
  getStatusMessage(status: "healthy" | "unhealthy"): string {
    return status === "healthy" ? "正常" : "異常";
  }

  /**
   * エラーメッセージを取得
   *
   * @param error ヘルスチェックエラー
   * @returns ユーザー向けのエラーメッセージ
   */
  getErrorMessage(error: HealthCheckError): string {
    switch (error.error) {
      case "API_ERROR":
        return "APIサーバーに接続できません";
      case "UNKNOWN_ERROR":
        return "システムエラーが発生しました";
      default:
        return error.message;
    }
  }
}

// シングルトンインスタンスをエクスポート
export const healthService = new HealthService();