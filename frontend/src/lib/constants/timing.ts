/**
 * @fileoverview タイミング定数定義
 *
 * API タイムアウト、React Query キャッシュ時間、同期間隔など、
 * アプリケーション全体で使用するタイミング関連の定数を集約しています。
 *
 * @module timing
 */

/**
 * タイミング関連の定数
 *
 * すべての時間はミリ秒単位で定義されています。
 */
export const TIMING_CONSTANTS = {
  /**
   * API リクエストのタイムアウト時間
   * @constant {number} 30秒 (30,000ミリ秒)
   */
  API_TIMEOUT_MS: 30_000,

  /**
   * API リトライ時の基本遅延時間
   * @constant {number} 1秒 (1,000ミリ秒)
   */
  API_RETRY_DELAY_BASE_MS: 1_000,

  /**
   * API リトライ時の最大遅延時間
   * @constant {number} 30秒 (30,000ミリ秒)
   */
  API_RETRY_DELAY_MAX_MS: 30_000,

  /**
   * React Query: データが新鮮とみなされる期間（デフォルト）
   * @constant {number} 5分 (300,000ミリ秒)
   */
  QUERY_STALE_TIME_MS: 5 * 60 * 1_000,

  /**
   * React Query: ガベージコレクション時間（キャッシュ保持期間）
   * @constant {number} 10分 (600,000ミリ秒)
   */
  QUERY_GC_TIME_MS: 10 * 60 * 1_000,

  /**
   * React Query: 頻繁に更新されるデータのstale time
   * @constant {number} 3分 (180,000ミリ秒)
   */
  QUERY_STALE_TIME_SHORT_MS: 3 * 60 * 1_000,

  /**
   * React Query: 滅多に更新されないデータのstale time
   * @constant {number} 10分 (600,000ミリ秒)
   */
  QUERY_STALE_TIME_LONG_MS: 10 * 60 * 1_000,

  /**
   * 同期ステータスのポーリング間隔
   * @constant {number} 1分 (60,000ミリ秒)
   */
  SYNC_POLL_INTERVAL_MS: 60 * 1_000,

  /**
   * 同期ステータスデータのstale time
   * @constant {number} 30秒 (30,000ミリ秒)
   */
  SYNC_STALE_TIME_MS: 30 * 1_000,

  /**
   * デバウンス用の遅延時間（検索入力など）
   * @constant {number} 300ミリ秒
   */
  DEBOUNCE_DELAY_MS: 300,

  /**
   * トースト通知の表示時間
   * @constant {number} 3秒 (3,000ミリ秒)
   */
  TOAST_DURATION_MS: 3_000,

  /**
   * トースト通知の表示時間（エラー）
   * @constant {number} 5秒 (5,000ミリ秒)
   */
  TOAST_DURATION_ERROR_MS: 5_000,

  // ============ 時間換算用定数 ============

  /**
   * 1分のミリ秒数
   * @constant {number} 60,000ミリ秒
   */
  MS_PER_MINUTE: 60 * 1_000,

  /**
   * 1時間のミリ秒数
   * @constant {number} 3,600,000ミリ秒
   */
  MS_PER_HOUR: 60 * 60 * 1_000,

  /**
   * 1日のミリ秒数
   * @constant {number} 86,400,000ミリ秒
   */
  MS_PER_DAY: 24 * 60 * 60 * 1_000,

  /**
   * 1週間のミリ秒数
   * @constant {number} 604,800,000ミリ秒
   */
  MS_PER_WEEK: 7 * 24 * 60 * 60 * 1_000,
} as const

/**
 * タイミング定数の型
 */
export type TimingConstants = typeof TIMING_CONSTANTS

/**
 * 指数バックオフによるリトライ遅延時間を計算
 *
 * @param {number} attemptIndex - リトライ回数（0から開始）
 * @returns {number} 遅延時間（ミリ秒）
 *
 * @example
 * ```typescript
 * calculateRetryDelay(0) // => 1000ms (1秒)
 * calculateRetryDelay(1) // => 2000ms (2秒)
 * calculateRetryDelay(5) // => 30000ms (30秒、上限)
 * ```
 */
export const calculateRetryDelay = (attemptIndex: number): number => {
  return Math.min(
    TIMING_CONSTANTS.API_RETRY_DELAY_BASE_MS * 2 ** attemptIndex,
    TIMING_CONSTANTS.API_RETRY_DELAY_MAX_MS
  )
}
