/**
 * 設定管理関連の型定義
 */

export interface EmailSettings {
  email_from: string
  email_from_name: string
}

export interface SecuritySettings {
  session_timeout: number
  password_min_length: number
  login_attempt_limit: number
  api_rate_limit: number
  token_expiry: number
}

export interface SyncSettings {
  backlog_sync_interval: number
  backlog_cache_timeout: number
  api_timeout: number
  max_retry_count: number
}

export interface SystemSettings {
  log_level: string
  debug_mode: boolean
  maintenance_mode: boolean
  data_retention_days: number
  backup_frequency: string
}

export interface AllSettings {
  email: EmailSettings
  security: SecuritySettings
  sync: SyncSettings
  system: SystemSettings
}

export interface SettingsUpdateRequest {
  email?: EmailSettings
  security?: SecuritySettings
  sync?: SyncSettings
  system?: SystemSettings
}

export interface Setting {
  id: number
  key: string
  value: string
  group: string
  value_type: string
  description?: string
  is_sensitive: boolean
  created_at: string
  updated_at: string
}