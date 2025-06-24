// frontend/src/config/env.ts
/**
 * 環境変数の型定義と検証
 *
 * 実行時に環境変数の存在と型を検証します
 */

interface EnvConfig {
  // 公開可能な環境変数
  NEXT_PUBLIC_API_URL: string;
  NEXT_PUBLIC_APP_URL: string;
  NEXT_PUBLIC_ENABLE_ANALYTICS: boolean;
  NEXT_PUBLIC_ENABLE_DEBUG_PANEL: boolean;

  // ビルド時のみの環境変数
  NODE_ENV: "development" | "production" | "test";
}

class EnvironmentConfig {
  private config: EnvConfig;

  constructor() {
    this.config = this.validateConfig();
  }

  private validateConfig(): EnvConfig {
    const errors: string[] = [];

    // 必須の環境変数チェック
    const requiredVars = ["NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_APP_URL"];

    for (const varName of requiredVars) {
      if (!process.env[varName]) {
        errors.push(`Missing required environment variable: ${varName}`);
      }
    }

    if (errors.length > 0) {
      throw new Error(`Environment validation failed:\n${errors.join("\n")}`);
    }

    return {
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL!,
      NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL!,
      NEXT_PUBLIC_ENABLE_ANALYTICS:
        process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === "true",
      NEXT_PUBLIC_ENABLE_DEBUG_PANEL:
        process.env.NEXT_PUBLIC_ENABLE_DEBUG_PANEL === "true",
      NODE_ENV:
        (process.env.NODE_ENV as EnvConfig["NODE_ENV"]) || "development",
    };
  }

  get<K extends keyof EnvConfig>(key: K): EnvConfig[K] {
    return this.config[key];
  }

  isProduction(): boolean {
    return this.config.NODE_ENV === "production";
  }

  isDevelopment(): boolean {
    return this.config.NODE_ENV === "development";
  }

  isTest(): boolean {
    return this.config.NODE_ENV === "test";
  }
}

// シングルトンインスタンス
export const env = new EnvironmentConfig();

// 使用例
// import { env } from '@/config/env';
// const apiUrl = env.get('NEXT_PUBLIC_API_URL');
