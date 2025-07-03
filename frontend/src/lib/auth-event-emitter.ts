/**
 * 認証関連のイベントを管理するイベントエミッター
 * 
 * api-clientとReduxストアの疎結合化のために使用
 */
export type AuthEventType = 'logout' | 'token-refresh-failed' | 'unauthorized'

export interface AuthEventHandler {
  (event: AuthEventType, data?: any): void
}

class AuthEventEmitter {
  private handlers: Map<AuthEventType, Set<AuthEventHandler>> = new Map()

  /**
   * イベントハンドラーを登録
   */
  on(event: AuthEventType, handler: AuthEventHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)
  }

  /**
   * イベントハンドラーを解除
   */
  off(event: AuthEventType, handler: AuthEventHandler): void {
    const handlers = this.handlers.get(event)
    if (handlers) {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.handlers.delete(event)
      }
    }
  }

  /**
   * イベントを発火
   */
  emit(event: AuthEventType, data?: any): void {
    const handlers = this.handlers.get(event)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(event, data)
        } catch (error) {
          console.error(`Error in auth event handler for ${event}:`, error)
        }
      })
    }
  }

  /**
   * 全てのハンドラーをクリア
   */
  clear(): void {
    this.handlers.clear()
  }
}

// シングルトンインスタンス
export const authEventEmitter = new AuthEventEmitter()