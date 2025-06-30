// frontend/src/config/env-client.ts
/**
 * クライアントサイド用の環境変数設定
 * Next.jsのビルド時に環境変数が静的に置換される
 */

interface ClientEnvConfig {
  NEXT_PUBLIC_API_URL: string;
  NEXT_PUBLIC_APP_URL: string;
  NEXT_PUBLIC_ENABLE_ANALYTICS?: boolean;
  NEXT_PUBLIC_ENABLE_DEBUG_PANEL?: boolean;
}

// 環境変数をオブジェクトとして定義
// Next.jsはビルド時にこれらの値を文字列リテラルに置換する
const clientEnv: ClientEnvConfig = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost",
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost",
  NEXT_PUBLIC_ENABLE_ANALYTICS: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === "true",
  NEXT_PUBLIC_ENABLE_DEBUG_PANEL: process.env.NEXT_PUBLIC_ENABLE_DEBUG_PANEL === "true",
};

// 環境変数の検証
function validateEnv(): void {
  const required: (keyof ClientEnvConfig)[] = ["NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_APP_URL"];
  const missing = required.filter(key => !clientEnv[key]);
  
  if (missing.length > 0) {
    console.error("Missing required environment variables:", missing);
    // 開発環境ではデフォルト値を使用して続行
    if (process.env.NODE_ENV !== "production") {
      console.warn("Using default values for missing environment variables");
    } else {
      throw new Error(`Missing required environment variables: ${missing.join(", ")}`);
    }
  }
}

// 初期化時に検証を実行
if (typeof window !== "undefined") {
  validateEnv();
}

export default clientEnv;