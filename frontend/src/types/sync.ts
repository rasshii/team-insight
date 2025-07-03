/**
 * 同期関連の型定義
 */

export interface ConnectionStatus {
  connected: boolean;
  status: 'active' | 'expired' | 'no_token';
  message: string;
  expires_at?: string;
  last_project_sync?: string;
  last_task_sync?: string;
}

export interface SyncStatus {
  project_id: number;
  project_name: string;
  total_tasks: number;
  status_counts: {
    todo: number;
    in_progress: number;
    resolved: number;
    closed: number;
  };
  last_sync: string | null;
}

export interface SyncResult {
  message: string;
  status: 'started' | 'completed' | 'failed';
  project_id?: number;
  created?: number;
  updated?: number;
  total?: number;
}