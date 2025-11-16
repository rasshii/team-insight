/**
 * @fileoverview API通信クライアント
 *
 * 全てのバックエンドAPI通信で使用する統一されたaxiosクライアントです。
 * 認証、エラーハンドリング、トークンリフレッシュ、ログ出力などの共通処理を提供します。
 *
 * @module apiClient
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { env } from '@/config/env'
import { ApiError, ErrorResponse } from '@/types/error'
import { authEventEmitter } from './auth-event-emitter'
import { TIMING_CONSTANTS } from './constants/timing'

/**
 * 統一されたAPIクライアント
 *
 * アプリケーション全体で使用する共通のaxiosインスタンスを管理するクラスです。
 *
 * ## 主要機能
 * - HTTPリクエストのインターセプター（認証トークンの自動付与）
 * - HTTPレスポンスのインターセプター（エラーハンドリング、自動リフレッシュ）
 * - トークン自動リフレッシュ機能（401エラー時）
 * - リクエスト/レスポンスのデバッグログ出力
 * - Cookie経由のJWT認証サポート
 *
 * ## 認証フロー
 * 1. リクエスト送信
 * 2. 401エラー受信 → トークンリフレッシュ試行
 * 3. リフレッシュ成功 → 元のリクエストを再実行
 * 4. リフレッシュ失敗 → ログアウトイベント発火、ログインページへリダイレクト
 *
 * ## エラーハンドリング
 * - 401エラー: 自動リフレッシュ → 失敗時はログアウト
 * - その他のエラー: ApiErrorクラスに変換して返却
 *
 * @remarks
 * - シングルトンパターンで実装されています
 * - withCredentials: true でCookieベースの認証をサポート
 * - タイムアウト: 30秒（デフォルト）
 *
 * @see {@link authEventEmitter} - 認証イベント通知
 */
class ApiClient {
  private axiosInstance: AxiosInstance
  private isRefreshing = false
  private failedQueue: Array<{
    resolve: (value?: unknown) => void
    reject: (reason?: any) => void
  }> = []

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: env.get('NEXT_PUBLIC_API_URL'),
      timeout: TIMING_CONSTANTS.API_TIMEOUT_MS,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // CookieベースのJWT認証のため
    })

    this.setupInterceptors()
  }

  private processQueue(error: any, token: string | null = null) {
    this.failedQueue.forEach(prom => {
      if (error) {
        prom.reject(error)
      } else {
        prom.resolve(token)
      }
    })
    
    this.failedQueue = []
  }

  private setupInterceptors() {
    // リクエストインターセプター
    this.axiosInstance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // デバッグ用ログ（本番環境では無効化）
        if (process.env.NODE_ENV === 'development') {
          console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
          if (config.data) {
            console.log('[API Request Data]', config.data)
          }
        }
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // レスポンスインターセプター
    this.axiosInstance.interceptors.response.use(
      (response) => {
        // デバッグ用ログ
        if (process.env.NODE_ENV === 'development') {
          console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`)
          console.log('[API Response Data]', response.data)
        }
        
        return response
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
        
        // エラーログ（401エラーは特別扱い）
        if (process.env.NODE_ENV === 'development') {
          const isAuthEndpoint = error.config?.url?.includes('/auth/me')
          const is401Error = error.response?.status === 401
          
          if (is401Error && isAuthEndpoint) {
            // /auth/meの401エラーは正常な未認証状態なのでinfoレベル
            console.info(`[API Info] ${error.config?.method?.toUpperCase()} ${error.config?.url} - 401 (Not authenticated)`)
          } else {
            // その他のエラーは通常通りエラーログ
            console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url} - ${error.response?.status}`)
            if (error.response?.data) {
              console.error('[API Error Details]', error.response.data)
            }
          }
        }

        // 401エラー（認証エラー）の場合
        if (error.response?.status === 401 && !originalRequest._retry) {
          // 現在のパスを取得
          const currentPath = typeof window !== 'undefined' ? window.location.pathname : ''
          const isRootPage = currentPath === '/'
          const isAuthPage = currentPath.startsWith('/auth/')
          
          console.log('[API Client] 401 error handling:', {
            url: originalRequest.url,
            currentPath,
            isRootPage,
            isAuthPage
          })
          
          // 認証が不要なエンドポイントの場合は、リフレッシュを試みない
          const publicEndpoints = [
            '/auth/login',
            '/auth/backlog/authorize',
            '/auth/backlog/callback'
          ]
          if (publicEndpoints.some(endpoint => originalRequest.url?.includes(endpoint))) {
            console.log('[API Client] Public endpoint 401 error - no refresh attempt')
            return Promise.reject(error)
          }
          
          // リフレッシュエンドポイント自体の401エラーの場合は、リトライしない
          if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/auth/backlog/refresh')) {
            // ログアウトイベントを発火
            authEventEmitter.emit('logout')
            
            // ルートページや認証ページ以外の場合のみリダイレクト
            if (typeof window !== 'undefined' && !isRootPage && !isAuthPage) {
              console.log('[API Client] Redirecting to login page...')
              window.location.href = '/auth/login'
            }
            return Promise.reject(error)
          }

          // /auth/me エンドポイントの401エラーで、ルートページや認証ページからの場合は、
          // リダイレクトせずにエラーをそのまま返す（未認証状態として扱う）
          if (originalRequest.url?.includes('/auth/me') && (isRootPage || isAuthPage)) {
            console.log('[API Client] /auth/me 401 error on root/auth page - no redirect')
            return Promise.reject(error)
          }

          if (this.isRefreshing) {
            // 既にリフレッシュ中の場合は、キューに追加
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject })
            }).then(() => {
              // リフレッシュ成功後、元のリクエストを再実行
              return this.axiosInstance(originalRequest)
            }).catch(err => {
              return Promise.reject(err)
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          return new Promise((resolve, reject) => {
            // JWTトークンリフレッシュを試行
            this.axiosInstance.post('/api/v1/auth/refresh')
              .then(() => {
                this.processQueue(null)
                resolve(this.axiosInstance(originalRequest))
              })
              .catch((refreshError) => {
                this.processQueue(refreshError, null)
                // リフレッシュ失敗時はログアウトイベントを発火
                authEventEmitter.emit('token-refresh-failed')
                authEventEmitter.emit('logout')
                
                // 現在のパスを取得
                const currentPath = typeof window !== 'undefined' ? window.location.pathname : ''
                const isRootPage = currentPath === '/'
                const isAuthPage = currentPath.startsWith('/auth/')
                
                // ルートページや認証ページ以外の場合のみリダイレクト
                if (typeof window !== 'undefined' && !isRootPage && !isAuthPage) {
                  console.log('[API Client] Refresh failed, redirecting to login page...')
                  window.location.href = '/auth/login'
                }
                reject(refreshError)
              })
              .finally(() => {
                this.isRefreshing = false
              })
          })
        }

        // エラーレスポンスをApiErrorクラスに変換
        if (error.response?.data && this.isErrorResponse(error.response.data)) {
          return Promise.reject(new ApiError(error.response.data as ErrorResponse))
        }
        
        return Promise.reject(error)
      }
    )
  }

  /**
   * エラーレスポンスの判定
   */
  private isErrorResponse(data: any): data is ErrorResponse {
    return data && 
           typeof data === 'object' && 
           'error' in data && 
           typeof data.error === 'object' &&
           'code' in data.error &&
           'message' in data.error
  }

  // HTTPメソッドのラッパー
  async get<T = any>(url: string, config?: any) {
    const response = await this.axiosInstance.get<T>(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: any) {
    const response = await this.axiosInstance.post<T>(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: any) {
    const response = await this.axiosInstance.put<T>(url, data, config)
    return response.data
  }

  async patch<T = any>(url: string, data?: any, config?: any) {
    const response = await this.axiosInstance.patch<T>(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: any) {
    const response = await this.axiosInstance.delete<T>(url, config)
    return response.data
  }
}

/**
 * APIクライアントのシングルトンインスタンス
 *
 * アプリケーション全体でこのインスタンスを使用してAPIリクエストを行います。
 *
 * @example
 * ```typescript
 * // GET リクエスト
 * const users = await apiClient.get('/api/v1/users');
 *
 * // POST リクエスト
 * const newUser = await apiClient.post('/api/v1/users', { name: 'John' });
 *
 * // PUT リクエスト
 * const updated = await apiClient.put('/api/v1/users/1', { name: 'Jane' });
 *
 * // DELETE リクエスト
 * await apiClient.delete('/api/v1/users/1');
 * ```
 */
export const apiClient = new ApiClient()

/**
 * APIエラーかどうかを判定するタイプガード（AxiosError）
 *
 * @param {unknown} error - 判定対象のエラーオブジェクト
 * @returns {boolean} AxiosErrorの場合true
 *
 * @example
 * ```typescript
 * try {
 *   await apiClient.get('/api/users');
 * } catch (error) {
 *   if (isAxiosError(error)) {
 *     console.log('HTTPステータス:', error.response?.status);
 *   }
 * }
 * ```
 */
export const isAxiosError = (error: unknown): error is AxiosError => {
  return axios.isAxiosError(error)
}

/**
 * APIエラーかどうかを判定するタイプガード（ApiError）
 *
 * @param {unknown} error - 判定対象のエラーオブジェクト
 * @returns {boolean} ApiErrorの場合true
 *
 * @example
 * ```typescript
 * try {
 *   await apiClient.post('/api/users', data);
 * } catch (error) {
 *   if (isApiError(error)) {
 *     console.log('エラーコード:', error.code);
 *     console.log('エラーメッセージ:', error.message);
 *   }
 * }
 * ```
 */
export const isApiError = (error: unknown): error is ApiError => {
  return error instanceof ApiError
}

/**
 * APIエラーの詳細メッセージを取得
 *
 * 様々な形式のエラーオブジェクトから、ユーザーに表示するための
 * わかりやすいエラーメッセージを抽出します。
 *
 * ## エラーメッセージの優先順位
 * 1. ApiError のメッセージ
 * 2. AxiosError のレスポンスデータ（error.message, detail, message）
 * 3. HTTPステータスコードに基づくデフォルトメッセージ
 * 4. Error オブジェクトのメッセージ
 * 5. 汎用エラーメッセージ
 *
 * @param {unknown} error - エラーオブジェクト
 * @returns {string} ユーザーに表示するエラーメッセージ
 *
 * @example
 * ```typescript
 * try {
 *   await apiClient.post('/api/users', data);
 * } catch (error) {
 *   const message = getApiErrorMessage(error);
 *   toast.error(message); // 「入力内容に誤りがあります」など
 * }
 * ```
 *
 * @remarks
 * - 400: 不正なリクエストです
 * - 401: 認証が必要です
 * - 403: アクセス権限がありません
 * - 404: リソースが見つかりません
 * - 409: リソースが既に存在します
 * - 422: 入力内容に誤りがあります
 * - 500: サーバーエラーが発生しました
 * - 502/503/504: サーバーが一時的に利用できません
 */
export const getApiErrorMessage = (error: unknown): string => {
  // ApiErrorの場合
  if (isApiError(error)) {
    return error.message
  }
  
  // AxiosErrorの場合
  if (isAxiosError(error)) {
    // バックエンドからのエラーメッセージ
    if (error.response?.data) {
      const data = error.response.data as any
      if (data.error?.message) {
        return data.error.message
      }
      if (data.detail) {
        return data.detail
      }
      if (data.message) {
        return data.message
      }
    }

    // HTTPステータスコードに基づくメッセージ
    switch (error.response?.status) {
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
        return '入力内容に誤りがあります'
      case 500:
        return 'サーバーエラーが発生しました'
      case 502:
      case 503:
      case 504:
        return 'サーバーが一時的に利用できません'
      default:
        return error.message || 'エラーが発生しました'
    }
  }
  
  // その他のエラー
  if (error instanceof Error) {
    return error.message
  }
  
  return 'エラーが発生しました'
}