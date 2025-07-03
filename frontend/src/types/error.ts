/**
 * APIエラーレスポンスの型定義
 */

/**
 * エラーコード定義
 */
export enum ErrorCode {
  // 認証関連
  AUTH_INVALID_CREDENTIALS = 'AUTH_INVALID_CREDENTIALS',
  AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED',
  AUTH_TOKEN_NOT_FOUND = 'AUTH_TOKEN_NOT_FOUND',
  AUTH_PERMISSION_DENIED = 'AUTH_PERMISSION_DENIED',
  
  // データ関連
  DATA_NOT_FOUND = 'DATA_NOT_FOUND',
  DATA_ALREADY_EXISTS = 'DATA_ALREADY_EXISTS',
  DATA_VALIDATION_ERROR = 'DATA_VALIDATION_ERROR',
  
  // システム関連
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  DATABASE_ERROR = 'DATABASE_ERROR',
  EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR',
}

/**
 * 検証エラーの詳細
 */
export interface ValidationError {
  field: string
  message: string
  type: string
}

/**
 * エラーレスポンスの基本構造
 */
export interface ErrorResponse {
  error: {
    code: ErrorCode
    message: string
    timestamp: string
    request_id?: string
    details?: {
      validation_errors?: ValidationError[]
      [key: string]: any
    }
  }
  status_code: number
}

/**
 * APIエラークラス
 */
export class ApiError extends Error {
  public readonly code: ErrorCode
  public readonly statusCode: number
  public readonly requestId?: string
  public readonly details?: any
  public readonly timestamp: string

  constructor(response: ErrorResponse) {
    super(response.error.message)
    this.name = 'ApiError'
    this.code = response.error.code
    this.statusCode = response.status_code
    this.requestId = response.error.request_id
    this.details = response.error.details
    this.timestamp = response.error.timestamp
  }

  /**
   * 検証エラーかどうかを判定
   */
  isValidationError(): boolean {
    return this.code === ErrorCode.DATA_VALIDATION_ERROR
  }

  /**
   * 認証エラーかどうかを判定
   */
  isAuthError(): boolean {
    return [
      ErrorCode.AUTH_INVALID_CREDENTIALS,
      ErrorCode.AUTH_TOKEN_EXPIRED,
      ErrorCode.AUTH_TOKEN_NOT_FOUND,
      ErrorCode.AUTH_PERMISSION_DENIED
    ].includes(this.code)
  }

  /**
   * 検証エラーの詳細を取得
   */
  getValidationErrors(): ValidationError[] {
    if (this.isValidationError() && this.details?.validation_errors) {
      return this.details.validation_errors
    }
    return []
  }
}