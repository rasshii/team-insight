import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Tailwind CSSクラス名を結合
 * 
 * clsxとtailwind-mergeを組み合わせて、
 * 条件付きクラス名と重複するTailwindクラスを適切に処理
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 日付をフォーマット
 * 
 * @param date - 日付
 * @param format - フォーマット（'short', 'medium', 'long', 'relative'）
 * @returns フォーマットされた日付文字列
 */
export function formatDate(
  date: Date | string | number,
  format: 'short' | 'medium' | 'long' | 'relative' = 'medium'
): string {
  const d = new Date(date)
  
  if (format === 'relative') {
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      if (diffHours === 0) {
        const diffMinutes = Math.floor(diffMs / (1000 * 60))
        if (diffMinutes === 0) {
          return '今'
        }
        return `${diffMinutes}分前`
      }
      return `${diffHours}時間前`
    } else if (diffDays === 1) {
      return '昨日'
    } else if (diffDays < 7) {
      return `${diffDays}日前`
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7)
      return `${weeks}週間前`
    } else if (diffDays < 365) {
      const months = Math.floor(diffDays / 30)
      return `${months}ヶ月前`
    } else {
      const years = Math.floor(diffDays / 365)
      return `${years}年前`
    }
  }
  
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: format === 'short' ? '2-digit' : 'long',
    day: 'numeric',
  }
  
  if (format === 'long') {
    options.hour = '2-digit'
    options.minute = '2-digit'
  }
  
  return d.toLocaleDateString('ja-JP', options)
}

/**
 * 数値を通貨形式でフォーマット
 * 
 * @param amount - 金額
 * @param currency - 通貨コード（デフォルト: 'JPY'）
 * @returns フォーマットされた通貨文字列
 */
export function formatCurrency(amount: number, currency = 'JPY'): string {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

/**
 * 数値を短縮形式でフォーマット
 * 
 * @param num - 数値
 * @param decimals - 小数点以下の桁数
 * @returns フォーマットされた文字列（例: 1.2K, 3.4M）
 */
export function formatCompactNumber(num: number, decimals = 1): string {
  if (num < 1000) return num.toString()
  
  const units = ['K', 'M', 'B', 'T']
  const unitIndex = Math.floor(Math.log10(num) / 3) - 1
  const unitValue = 1000 ** (unitIndex + 1)
  
  const value = (num / unitValue).toFixed(decimals)
  return `${value}${units[unitIndex]}`
}

/**
 * パーセンテージを計算
 * 
 * @param current - 現在値
 * @param total - 総数
 * @param decimals - 小数点以下の桁数
 * @returns パーセンテージ
 */
export function calculatePercentage(
  current: number,
  total: number,
  decimals = 0
): number {
  if (total === 0) return 0
  return Math.round((current / total) * 100 * 10 ** decimals) / 10 ** decimals
}

/**
 * 文字列を指定長で切り詰め
 * 
 * @param text - 対象文字列
 * @param maxLength - 最大長
 * @param suffix - 末尾に付ける文字列
 * @returns 切り詰められた文字列
 */
export function truncate(
  text: string,
  maxLength: number,
  suffix = '...'
): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - suffix.length) + suffix
}

/**
 * デバウンス関数
 * 
 * @param func - デバウンスする関数
 * @param wait - 待機時間（ミリ秒）
 * @returns デバウンスされた関数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  
  return function (...args: Parameters<T>) {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * スロットル関数
 * 
 * @param func - スロットルする関数
 * @param limit - 実行間隔（ミリ秒）
 * @returns スロットルされた関数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  
  return function (...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * オブジェクトから指定したキーを除外
 * 
 * @param obj - 対象オブジェクト
 * @param keys - 除外するキー
 * @returns 新しいオブジェクト
 */
export function omit<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj }
  keys.forEach(key => delete result[key])
  return result
}

/**
 * オブジェクトから指定したキーのみを抽出
 * 
 * @param obj - 対象オブジェクト
 * @param keys - 抽出するキー
 * @returns 新しいオブジェクト
 */
export function pick<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  const result = {} as Pick<T, K>
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key]
    }
  })
  return result
}

/**
 * 配列をグループ化
 * 
 * @param array - 対象配列
 * @param key - グループ化のキー
 * @returns グループ化されたオブジェクト
 */
export function groupBy<T>(
  array: T[],
  key: keyof T | ((item: T) => string)
): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const groupKey = typeof key === 'function' ? key(item) : String(item[key])
    if (!groups[groupKey]) {
      groups[groupKey] = []
    }
    groups[groupKey].push(item)
    return groups
  }, {} as Record<string, T[]>)
}

/**
 * 配列から重複を除去
 * 
 * @param array - 対象配列
 * @param key - 重複判定のキー（オプション）
 * @returns 重複を除去した配列
 */
export function uniqBy<T>(
  array: T[],
  key?: keyof T | ((item: T) => any)
): T[] {
  if (!key) {
    return [...new Set(array)]
  }
  
  const seen = new Set()
  return array.filter(item => {
    const k = typeof key === 'function' ? key(item) : item[key]
    if (seen.has(k)) {
      return false
    }
    seen.add(k)
    return true
  })
}

/**
 * 深いオブジェクトのマージ
 * 
 * @param target - ターゲットオブジェクト
 * @param sources - マージするオブジェクト
 * @returns マージされたオブジェクト
 */
export function deepMerge<T extends Record<string, any>>(
  target: T,
  ...sources: Partial<T>[]
): T {
  if (!sources.length) return target
  
  const source = sources.shift()
  
  if (isObject(target) && isObject(source)) {
    for (const key in source) {
      if (isObject(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} })
        deepMerge(target[key], source[key])
      } else {
        Object.assign(target, { [key]: source[key] })
      }
    }
  }
  
  return deepMerge(target, ...sources)
}

/**
 * オブジェクトかどうかを判定
 */
function isObject(item: any): item is Record<string, any> {
  return item && typeof item === 'object' && !Array.isArray(item)
}

/**
 * URLクエリパラメータを構築
 * 
 * @param params - パラメータオブジェクト
 * @returns クエリ文字列
 */
export function buildQueryString(
  params: Record<string, any>
): string {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, String(v)))
      } else {
        searchParams.append(key, String(value))
      }
    }
  })
  
  return searchParams.toString()
}

/**
 * ローカルストレージの型安全なラッパー
 */
export const storage = {
  get<T>(key: string, defaultValue?: T): T | undefined {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch {
      return defaultValue
    }
  },
  
  set<T>(key: string, value: T): void {
    try {
      window.localStorage.setItem(key, JSON.stringify(value))
    } catch {
      console.error(`Failed to save ${key} to localStorage`)
    }
  },
  
  remove(key: string): void {
    try {
      window.localStorage.removeItem(key)
    } catch {
      console.error(`Failed to remove ${key} from localStorage`)
    }
  },
  
  clear(): void {
    try {
      window.localStorage.clear()
    } catch {
      console.error('Failed to clear localStorage')
    }
  },
}
