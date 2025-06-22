// frontend/src/lib/errors.ts

/**
 * アプリケーション固有のエラークラス
 */
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = "AppError";
  }
}

/**
 * API関連のエラー
 */
export class ApiError extends AppError {
  constructor(message: string, statusCode: number, details?: any) {
    super(message, `API_ERROR_${statusCode}`, statusCode, details);
    this.name = "ApiError";
  }
}

/**
 * 認証関連のエラー
 */
export class AuthError extends AppError {
  constructor(message: string, details?: any) {
    super(message, "AUTH_ERROR", 401, details);
    this.name = "AuthError";
  }
}

/**
 * 権限関連のエラー
 */
export class PermissionError extends AppError {
  constructor(message: string, details?: any) {
    super(message, "PERMISSION_ERROR", 403, details);
    this.name = "PermissionError";
  }
}

/**
 * バリデーションエラー
 */
export class ValidationError extends AppError {
  constructor(
    message: string,
    public validationErrors: Record<string, string[]>
  ) {
    super(message, "VALIDATION_ERROR", 422, validationErrors);
    this.name = "ValidationError";
  }
}
