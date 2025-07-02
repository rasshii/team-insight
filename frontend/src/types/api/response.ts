/**
 * API レスポンスの統一的な型定義
 * 
 * バックエンドのPydanticスキーマと対応する
 * TypeScriptの型定義を提供します。
 */

/**
 * 成功レスポンスの基本型
 */
export interface SuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
  timestamp: string;
}

/**
 * エラーの詳細情報
 */
export interface ErrorDetail {
  field?: string;
  reason: string;
  value?: any;
}

/**
 * エラー情報
 */
export interface ErrorInfo {
  code: string;
  message: string;
  timestamp: string;
  details?: ErrorDetail[];
  request_id?: string;
  trace_id?: string;
}

/**
 * エラーレスポンス
 */
export interface ErrorResponse {
  error: ErrorInfo;
  status_code: number;
}

/**
 * ページネーション情報
 */
export interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * ページネーション付きレスポンス
 */
export interface PaginatedResponse<T> {
  success: true;
  data: T[];
  meta: PaginationMeta;
  message?: string;
  timestamp: string;
}

/**
 * 一括操作の結果
 */
export interface BulkOperationResult {
  succeeded: number;
  failed: number;
  errors: ErrorDetail[];
}

/**
 * 一括操作レスポンス
 */
export interface BulkOperationResponse {
  success: boolean;
  result: BulkOperationResult;
  message: string;
  timestamp: string;
}

/**
 * ヘルスチェックレスポンス
 */
export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  version?: string;
  services?: Record<string, any>;
}

/**
 * メッセージレスポンス
 */
export interface MessageResponse {
  success: boolean;
  message: string;
  timestamp: string;
}

/**
 * ステータスレスポンス
 */
export interface StatusResponse {
  status: string;
  details?: Record<string, any>;
  timestamp: string;
}

/**
 * APIレスポンスの共用型
 */
export type ApiResponse<T> = SuccessResponse<T> | ErrorResponse;

/**
 * ページネーション付きAPIレスポンスの共用型
 */
export type PaginatedApiResponse<T> = PaginatedResponse<T> | ErrorResponse;

/**
 * 型ガード: 成功レスポンスかどうかを判定
 */
export function isSuccessResponse<T>(
  response: ApiResponse<T>
): response is SuccessResponse<T> {
  return 'success' in response && response.success === true;
}

/**
 * 型ガード: エラーレスポンスかどうかを判定
 */
export function isErrorResponse(
  response: ApiResponse<any>
): response is ErrorResponse {
  return 'error' in response && 'status_code' in response;
}

/**
 * 型ガード: ページネーション付きレスポンスかどうかを判定
 */
export function isPaginatedResponse<T>(
  response: any
): response is PaginatedResponse<T> {
  return (
    'success' in response &&
    response.success === true &&
    'meta' in response &&
    Array.isArray(response.data)
  );
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
 * APIリクエストのオプション
 */
export interface ApiRequestOptions {
  timeout?: number;
  retry?: {
    count: number;
    delay: number;
  };
  signal?: AbortSignal;
}

/**
 * フィルター条件の基本型
 */
export interface BaseFilters {
  [key: string]: any;
}

/**
 * ソート条件の基本型
 */
export interface SortOptions {
  field: string;
  order: 'asc' | 'desc';
}

/**
 * リスト取得のパラメータ
 */
export interface ListParams<TFilters extends BaseFilters = BaseFilters> {
  page?: number;
  per_page?: number;
  filters?: TFilters;
  sort?: SortOptions;
}

/**
 * 検索パラメータ
 */
export interface SearchParams extends ListParams {
  query: string;
}

/**
 * 日付範囲フィルター
 */
export interface DateRangeFilter {
  start?: string;
  end?: string;
}

/**
 * 数値範囲フィルター
 */
export interface NumberRangeFilter {
  min?: number;
  max?: number;
}

/**
 * APIクライアントの基本インターフェース
 */
export interface ApiClient {
  get<T>(url: string, options?: ApiRequestOptions): Promise<T>;
  post<T>(url: string, data?: any, options?: ApiRequestOptions): Promise<T>;
  put<T>(url: string, data?: any, options?: ApiRequestOptions): Promise<T>;
  patch<T>(url: string, data?: any, options?: ApiRequestOptions): Promise<T>;
  delete<T>(url: string, options?: ApiRequestOptions): Promise<T>;
}