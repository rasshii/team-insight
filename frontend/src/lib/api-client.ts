import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { env } from '@/config/env'
import { store } from '@/store'
import { logout } from '@/store/slices/authSlice'

/**
 * 統一されたAPIクライアント
 * 
 * 全てのAPI通信で使用する共通のaxiosインスタンス
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
      timeout: 30000,
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
        }
        
        return response
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
        
        // エラーログ
        if (process.env.NODE_ENV === 'development') {
          console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url} - ${error.response?.status}`)
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
          
          // リフレッシュエンドポイント自体の401エラーの場合は、リトライしない
          if (originalRequest.url?.includes('/auth/backlog/refresh')) {
            // ログアウト処理
            store.dispatch(logout())
            
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
            // トークンリフレッシュを試行
            this.axiosInstance.post('/api/v1/auth/backlog/refresh')
              .then(() => {
                this.processQueue(null)
                resolve(this.axiosInstance(originalRequest))
              })
              .catch((refreshError) => {
                this.processQueue(refreshError, null)
                // リフレッシュ失敗時はログアウト
                store.dispatch(logout())
                
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

        return Promise.reject(error)
      }
    )
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

// シングルトンインスタンス
export const apiClient = new ApiClient()

/**
 * APIエラーかどうかを判定するタイプガード
 */
export const isApiError = (error: unknown): error is AxiosError => {
  return axios.isAxiosError(error)
}

/**
 * APIエラーの詳細を取得
 */
export const getApiErrorMessage = (error: unknown): string => {
  if (!isApiError(error)) {
    return 'エラーが発生しました'
  }

  // バックエンドからのエラーメッセージ
  if (error.response?.data) {
    const data = error.response.data as any
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