import { AxiosError } from 'axios'

/**
 * APIエラーレスポンスの型定義
 */
export interface ApiErrorResponse {
  error: {
    code: string
    message: string
    timestamp: string
    details?: Record<string, any>
    request_id?: string
  }
  status_code: number
}

/**
 * バリデーションエラーの詳細
 */
export interface ValidationError {
  field: string
  message: string
  type: string
}

/**
 * Axiosエラーかどうかを判定
 */
export function isApiError(error: unknown): error is AxiosError<ApiErrorResponse> {
  return !!(
    error &&
    typeof error === 'object' &&
    'isAxiosError' in error &&
    error.isAxiosError === true
  )
}

/**
 * エラーからメッセージを抽出
 * 
 * @param error - エラーオブジェクト
 * @param fallbackMessage - フォールバックメッセージ
 * @returns エラーメッセージ
 */
export function getErrorMessage(error: unknown, fallbackMessage = 'エラーが発生しました'): string {
  if (isApiError(error)) {
    // 新しい統一フォーマット
    if (error.response?.data?.error?.message) {
      return error.response.data.error.message
    }
    
    // 旧フォーマット（後方互換性）
    if (error.response?.data && typeof error.response.data === 'object' && 'detail' in error.response.data) {
      return (error.response.data as any).detail
    }
    
    // HTTPステータスコードに基づくメッセージ
    if (error.response?.status) {
      return getHttpErrorMessage(error.response.status)
    }
  }
  
  // 通常のErrorオブジェクト
  if (error instanceof Error) {
    return error.message
  }
  
  // 文字列エラー
  if (typeof error === 'string') {
    return error
  }
  
  return fallbackMessage
}

/**
 * HTTPステータスコードに基づくエラーメッセージを取得
 */
export function getHttpErrorMessage(statusCode: number): string {
  switch (statusCode) {
    case 400:
      return '不正なリクエストです'
    case 401:
      return '認証が必要です'
    case 403:
      return 'アクセス権限がありません'
    case 404:
      return 'リソースが見つかりません'
    case 409:
      return 'リソースが既に存在します'
    case 422:
      return '入力データが正しくありません'
    case 429:
      return 'リクエストが多すぎます。しばらくしてから再試行してください'
    case 500:
      return 'サーバーエラーが発生しました'
    case 502:
      return 'ゲートウェイエラーが発生しました'
    case 503:
      return 'サービスが一時的に利用できません'
    default:
      return `エラーが発生しました (${statusCode})`
  }
}

/**
 * バリデーションエラーを取得
 */
export function getValidationErrors(error: unknown): ValidationError[] | null {
  if (!isApiError(error)) {
    return null
  }
  
  // 新しい統一フォーマット
  if (error.response?.data?.error?.details?.validation_errors) {
    return error.response.data.error.details.validation_errors
  }
  
  // 旧フォーマット（後方互換性）
  if (error.response?.data && 'detail' in error.response.data) {
    const detail = (error.response.data as any).detail
    if (Array.isArray(detail) && detail.length > 0 && 'loc' in detail[0]) {
      return detail.map((err: any) => ({
        field: err.loc.join('.'),
        message: err.msg,
        type: err.type,
      }))
    }
  }
  
  return null
}

/**
 * エラーコードを取得
 */
export function getErrorCode(error: unknown): string | null {
  if (!isApiError(error)) {
    return null
  }
  
  return error.response?.data?.error?.code || null
}

/**
 * リクエストIDを取得
 */
export function getRequestId(error: unknown): string | null {
  if (!isApiError(error)) {
    return null
  }
  
  return error.response?.data?.error?.request_id || null
}

/**
 * エラーログ用の詳細情報を生成
 */
export function getErrorLogDetails(error: unknown): Record<string, any> {
  const details: Record<string, any> = {
    message: getErrorMessage(error),
    timestamp: new Date().toISOString(),
  }
  
  if (isApiError(error)) {
    details.statusCode = error.response?.status
    details.errorCode = getErrorCode(error)
    details.requestId = getRequestId(error)
    details.url = error.config?.url
    details.method = error.config?.method
    
    const validationErrors = getValidationErrors(error)
    if (validationErrors) {
      details.validationErrors = validationErrors
    }
  }
  
  return details
}

/**
 * エラーハンドリングのベストプラクティス例
 * 
 * @example
 * ```tsx
 * try {
 *   await apiCall()
 * } catch (error) {
 *   // ユーザー向けメッセージ
 *   const message = getErrorMessage(error, 'データの取得に失敗しました')
 *   toast({ title: 'エラー', description: message, variant: 'destructive' })
 *   
 *   // 開発者向けログ
 *   console.error('API Error:', getErrorLogDetails(error))
 *   
 *   // バリデーションエラーの処理
 *   const validationErrors = getValidationErrors(error)
 *   if (validationErrors) {
 *     validationErrors.forEach(err => {
 *       form.setError(err.field, { message: err.message })
 *     })
 *   }
 * }
 * ```
 */