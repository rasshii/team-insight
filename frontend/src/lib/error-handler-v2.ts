/**
 * 統一的なエラーハンドリングユーティリティ V2
 * 
 * 既存のerror-handler.tsを拡張し、より統一的で再利用可能な
 * エラーハンドリング機能を提供します。
 */

import { toast } from 'react-toastify';
import { AxiosError } from 'axios';

/**
 * エラーの詳細情報
 */
export interface ErrorDetail {
  field?: string;
  reason?: string;
  value?: any;
}

/**
 * 統一的なAPIエラーレスポンス構造
 */
export interface UnifiedErrorResponse {
  error: {
    code: string;
    message: string;
    timestamp: string;
    details?: ErrorDetail[];
    request_id?: string;
    trace_id?: string;
  };
  status_code: number;
}

/**
 * エラーコードの定数
 */
export const ERROR_CODES = {
  // クライアントエラー
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  CONFLICT: 'CONFLICT',
  TOO_MANY_REQUESTS: 'TOO_MANY_REQUESTS',
  
  // サーバーエラー
  INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
  BAD_GATEWAY: 'BAD_GATEWAY',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  
  // ネットワーク・その他
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

/**
 * エラーハンドリングオプション
 */
export interface ErrorHandlingOptions {
  showToast?: boolean;
  toastDuration?: number;
  logToConsole?: boolean;
  context?: string;
  onAuthError?: () => void;
  onNetworkError?: () => void;
  customHandlers?: Record<ErrorCode, (error: any) => void>;
}

/**
 * 統一的なエラーハンドラー
 */
export class UnifiedErrorHandler {
  private static defaultOptions: ErrorHandlingOptions = {
    showToast: true,
    toastDuration: 5000,
    logToConsole: true,
  };

  /**
   * デフォルトオプションを設定
   */
  static setDefaultOptions(options: Partial<ErrorHandlingOptions>): void {
    this.defaultOptions = { ...this.defaultOptions, ...options };
  }

  /**
   * エラーを処理
   */
  static handle(error: any, options: ErrorHandlingOptions = {}): void {
    const opts = { ...this.defaultOptions, ...options };
    const errorCode = this.getErrorCode(error);
    
    // ログ出力
    if (opts.logToConsole) {
      this.logError(error, opts.context);
    }

    // カスタムハンドラーの実行
    if (opts.customHandlers?.[errorCode]) {
      opts.customHandlers[errorCode](error);
      return;
    }

    // エラータイプ別の処理
    switch (errorCode) {
      case ERROR_CODES.UNAUTHORIZED:
        this.handleAuthError(error, opts);
        break;
      
      case ERROR_CODES.NETWORK_ERROR:
      case ERROR_CODES.TIMEOUT:
        this.handleNetworkError(error, opts);
        break;
      
      case ERROR_CODES.VALIDATION_ERROR:
        this.handleValidationError(error, opts);
        break;
      
      default:
        this.handleGenericError(error, opts);
    }

    // トースト表示
    if (opts.showToast) {
      this.showToast(error, opts);
    }
  }

  /**
   * エラーコードを取得
   */
  static getErrorCode(error: any): ErrorCode {
    // Axiosエラーの場合
    if (this.isAxiosError(error)) {
      const responseData = error.response?.data;
      
      // 統一フォーマットのエラーコード
      if (responseData?.error?.code) {
        return responseData.error.code as ErrorCode;
      }

      // HTTPステータスコードから推測
      const status = error.response?.status;
      if (status === 401) return ERROR_CODES.UNAUTHORIZED;
      if (status === 403) return ERROR_CODES.FORBIDDEN;
      if (status === 404) return ERROR_CODES.NOT_FOUND;
      if (status === 409) return ERROR_CODES.CONFLICT;
      if (status === 422) return ERROR_CODES.VALIDATION_ERROR;
      if (status === 429) return ERROR_CODES.TOO_MANY_REQUESTS;
      if (status === 502) return ERROR_CODES.BAD_GATEWAY;
      if (status === 503) return ERROR_CODES.SERVICE_UNAVAILABLE;
      if (status && status >= 500) return ERROR_CODES.INTERNAL_SERVER_ERROR;
    }

    // ネットワークエラー
    if (error.code === 'ECONNABORTED') return ERROR_CODES.TIMEOUT;
    if (error.message === 'Network Error') return ERROR_CODES.NETWORK_ERROR;

    return ERROR_CODES.UNKNOWN_ERROR;
  }

  /**
   * ユーザー向けメッセージを取得
   */
  static getUserMessage(error: any): string {
    // Axiosエラーの場合
    if (this.isAxiosError(error)) {
      const responseData = error.response?.data;
      
      // 統一フォーマットのメッセージ
      if (responseData?.error?.message) {
        return responseData.error.message;
      }

      // 旧フォーマット（後方互換性）
      if (responseData?.detail) {
        return responseData.detail;
      }
    }

    // 通常のErrorオブジェクト
    if (error instanceof Error) {
      return error.message;
    }

    // デフォルトメッセージ
    return 'エラーが発生しました';
  }

  /**
   * エラーの詳細情報を取得
   */
  static getErrorDetails(error: any): ErrorDetail[] | undefined {
    if (!this.isAxiosError(error)) return undefined;
    
    const responseData = error.response?.data;
    return responseData?.error?.details;
  }

  /**
   * リクエストIDを取得
   */
  static getRequestId(error: any): string | undefined {
    if (!this.isAxiosError(error)) return undefined;
    
    const responseData = error.response?.data;
    return responseData?.error?.request_id;
  }

  /**
   * Axiosエラーかどうかを判定
   */
  private static isAxiosError(error: any): error is AxiosError<UnifiedErrorResponse> {
    return !!(error?.isAxiosError);
  }

  /**
   * 認証エラーの処理
   */
  private static handleAuthError(error: any, options: ErrorHandlingOptions): void {
    if (options.onAuthError) {
      options.onAuthError();
    }
  }

  /**
   * ネットワークエラーの処理
   */
  private static handleNetworkError(error: any, options: ErrorHandlingOptions): void {
    if (options.onNetworkError) {
      options.onNetworkError();
    }
  }

  /**
   * バリデーションエラーの処理
   */
  private static handleValidationError(error: any, options: ErrorHandlingOptions): void {
    const details = this.getErrorDetails(error);
    if (details && details.length > 0) {
      console.group('Validation Errors');
      details.forEach(detail => {
        console.error(`${detail.field}: ${detail.reason}`);
      });
      console.groupEnd();
    }
  }

  /**
   * 一般的なエラーの処理
   */
  private static handleGenericError(error: any, options: ErrorHandlingOptions): void {
    // 必要に応じて追加の処理を実装
  }

  /**
   * トースト通知を表示
   */
  private static showToast(error: any, options: ErrorHandlingOptions): void {
    const message = this.getUserMessage(error);
    const errorCode = this.getErrorCode(error);
    
    const toastOptions = {
      autoClose: options.toastDuration,
    };

    switch (errorCode) {
      case ERROR_CODES.VALIDATION_ERROR:
        const details = this.getErrorDetails(error);
        if (details && details.length > 0) {
          const detailMessage = details
            .map(d => `${d.field}: ${d.reason}`)
            .join('\n');
          toast.error(`${message}\n${detailMessage}`, toastOptions);
        } else {
          toast.error(message, toastOptions);
        }
        break;

      case ERROR_CODES.UNAUTHORIZED:
        toast.warning(message, toastOptions);
        break;

      case ERROR_CODES.NETWORK_ERROR:
      case ERROR_CODES.TIMEOUT:
        toast.info(message, toastOptions);
        break;

      default:
        toast.error(message, toastOptions);
    }
  }

  /**
   * エラーをコンソールにログ出力
   */
  private static logError(error: any, context?: string): void {
    const errorInfo = {
      code: this.getErrorCode(error),
      message: this.getUserMessage(error),
      details: this.getErrorDetails(error),
      requestId: this.getRequestId(error),
      context,
      timestamp: new Date().toISOString(),
    };

    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 Error: ${errorInfo.code}`);
      console.error('Error Info:', errorInfo);
      console.error('Full Error:', error);
      console.groupEnd();
    } else {
      console.error(`Error: ${errorInfo.message} (${errorInfo.code})`);
    }
  }

  /**
   * リトライ可能なエラーかどうかを判定
   */
  static isRetryable(error: any): boolean {
    const errorCode = this.getErrorCode(error);
    
    return [
      ERROR_CODES.NETWORK_ERROR,
      ERROR_CODES.TIMEOUT,
      ERROR_CODES.INTERNAL_SERVER_ERROR,
      ERROR_CODES.BAD_GATEWAY,
      ERROR_CODES.SERVICE_UNAVAILABLE
    ].includes(errorCode);
  }

  /**
   * 致命的なエラーかどうかを判定
   */
  static isFatal(error: any): boolean {
    const errorCode = this.getErrorCode(error);
    
    return [
      ERROR_CODES.UNAUTHORIZED,
      ERROR_CODES.FORBIDDEN
    ].includes(errorCode);
  }
}

/**
 * React Query用のエラーハンドラー
 */
export function createReactQueryErrorHandler(options?: ErrorHandlingOptions) {
  return (error: any) => {
    UnifiedErrorHandler.handle(error, {
      ...options,
      context: 'React Query',
    });
  };
}

/**
 * グローバルエラーハンドラーの設定
 */
export function setupGlobalErrorHandlers(options?: ErrorHandlingOptions): void {
  // unhandledrejectionイベント
  window.addEventListener('unhandledrejection', (event) => {
    UnifiedErrorHandler.handle(event.reason, {
      ...options,
      context: 'Unhandled Promise Rejection',
    });
  });

  // errorイベント
  window.addEventListener('error', (event) => {
    UnifiedErrorHandler.handle(event.error || event, {
      ...options,
      context: 'Global Error',
    });
  });
}

// エクスポート
export { UnifiedErrorHandler as ErrorHandler };