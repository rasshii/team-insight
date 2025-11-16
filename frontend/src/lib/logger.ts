/**
 * アプリケーション全体で使用する統一ロガー
 *
 * 環境に応じてログレベルを制御し、本番環境では
 * 不要なログを出力しないようにします。
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: unknown;
}

class Logger {
  private isDevelopment: boolean;
  private isTest: boolean;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
    this.isTest = process.env.NODE_ENV === 'test';
  }

  /**
   * デバッグレベルのログ（開発環境のみ）
   */
  debug(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.debug(`[DEBUG] ${message}`, context || '');
    }
  }

  /**
   * 情報レベルのログ（開発環境のみ）
   */
  info(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.info(`[INFO] ${message}`, context || '');
    }
  }

  /**
   * 警告レベルのログ（開発・本番共通）
   */
  warn(message: string, context?: LogContext): void {
    if (!this.isTest) {
      console.warn(`[WARN] ${message}`, context || '');
    }
  }

  /**
   * エラーレベルのログ（開発・本番共通）
   */
  error(message: string, error?: Error | unknown, context?: LogContext): void {
    if (!this.isTest) {
      console.error(`[ERROR] ${message}`, {
        error: error instanceof Error ? {
          name: error.name,
          message: error.message,
          stack: this.isDevelopment ? error.stack : undefined,
        } : error,
        ...context,
      });
    }
  }

  /**
   * 汎用ログメソッド
   */
  log(level: LogLevel, message: string, context?: LogContext): void {
    switch (level) {
      case 'debug':
        this.debug(message, context);
        break;
      case 'info':
        this.info(message, context);
        break;
      case 'warn':
        this.warn(message, context);
        break;
      case 'error':
        this.error(message, context);
        break;
    }
  }
}

// シングルトンインスタンスをエクスポート
export const logger = new Logger();

// 型エクスポート
export type { LogLevel, LogContext };
