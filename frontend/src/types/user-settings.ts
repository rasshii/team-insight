/**
 * ユーザー設定関連の型定義
 */

export interface UserSettings {
  // 基本情報
  id: number
  email?: string
  name?: string
  backlog_id?: number
  is_active: boolean
  
  // 設定
  timezone: string
  locale: string
  date_format: string
  
  // 通知設定
  preferences?: UserPreferences
}

export interface UserPreferences {
  id: number
  user_id: number
  email_notifications: boolean
  report_frequency: string
  notification_email?: string
  created_at: string
  updated_at: string
}

export interface UserSettingsUpdate {
  name?: string
  timezone?: string
  locale?: string
  date_format?: string
  email_notifications?: boolean
  report_frequency?: string
  notification_email?: string
}

export interface LoginHistory {
  id: number
  user_id: number
  ip_address?: string
  user_agent?: string
  login_at: string
  logout_at?: string
  session_id?: string
}

export interface ActivityLog {
  id: number
  user_id: number
  action: string
  resource_type?: string
  resource_id?: number
  details?: any
  ip_address?: string
  created_at: string
}

export interface SessionInfo {
  session_id: string
  ip_address?: string
  user_agent?: string
  login_at: string
  is_current: boolean
}

// 定数
export const TIMEZONES = [
  { value: 'Asia/Tokyo', label: '東京 (GMT+9)' },
  { value: 'Asia/Seoul', label: 'ソウル (GMT+9)' },
  { value: 'Asia/Shanghai', label: '上海 (GMT+8)' },
  { value: 'Asia/Singapore', label: 'シンガポール (GMT+8)' },
  { value: 'UTC', label: 'UTC (GMT+0)' },
  { value: 'America/New_York', label: 'ニューヨーク (GMT-5)' },
  { value: 'America/Los_Angeles', label: 'ロサンゼルス (GMT-8)' },
  { value: 'Europe/London', label: 'ロンドン (GMT+0)' },
  { value: 'Europe/Paris', label: 'パリ (GMT+1)' },
]

export const LOCALES = [
  { value: 'ja', label: '日本語' },
  { value: 'en', label: 'English' },
]

export const DATE_FORMATS = [
  { value: 'YYYY-MM-DD', label: '2024-12-31' },
  { value: 'DD/MM/YYYY', label: '31/12/2024' },
  { value: 'MM/DD/YYYY', label: '12/31/2024' },
  { value: 'YYYY年MM月DD日', label: '2024年12月31日' },
]

export const REPORT_FREQUENCIES = [
  { value: 'daily', label: '毎日' },
  { value: 'weekly', label: '毎週' },
  { value: 'monthly', label: '毎月' },
  { value: 'disabled', label: '無効' },
]