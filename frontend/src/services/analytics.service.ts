import { apiClient } from '@/lib/api-client'

export interface ProjectHealth {
  project_id: number;
  project_name: string;
  health_score: number;
  total_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  overdue_tasks: number;
  overdue_rate: number;
  status_distribution: {
    [key: string]: number;
  };
}

export interface Bottleneck {
  type: "stalled_tasks" | "task_concentration" | "overdue_tasks";
  severity: "high" | "medium" | "low";
  status?: string;
  assignee?: string;
  count?: number;
  task_count?: number;
  overdue_count?: number;
  avg_days_stalled?: number;
  avg_task_count?: number;
}

export interface VelocityData {
  date: string;
  completed_count: number;
}

export interface CycleTimeData {
  project_id: number;
  project_name: string;
  cycle_times: {
    [status: string]: number;
  };
  unit: string;
}

export interface PersonalDashboard {
  user_id: number;
  user_name: string;
  statistics: {
    total_tasks: number;
    completed_tasks: number;
    in_progress_tasks: number;
    overdue_tasks: number;
    completion_rate: number;
  };
  recent_completed_tasks: Array<{
    id: number;
    title: string;
    completed_date: string | null;
  }>;
}

/**
 * 分析関連のAPIサービス
 * 
 * React Queryと組み合わせて使用するためのシンプルな関数群
 */
export const analyticsService = {
  /**
   * プロジェクトの健全性情報を取得
   */
  async getProjectHealth(projectId: number): Promise<ProjectHealth> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/health/`)
  },

  /**
   * プロジェクトのボトルネックを取得
   */
  async getProjectBottlenecks(projectId: number): Promise<Bottleneck[]> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/bottlenecks/`)
  },

  /**
   * プロジェクトのベロシティを取得
   */
  async getProjectVelocity(projectId: number, periodDays: number = 30): Promise<VelocityData[]> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/velocity/`, {
      params: { period_days: periodDays }
    })
  },

  /**
   * プロジェクトのサイクルタイムを取得
   */
  async getProjectCycleTime(projectId: number): Promise<CycleTimeData> {
    return await apiClient.get(`/api/v1/analytics/project/${projectId}/cycle-time/`)
  },

  /**
   * 個人ダッシュボード情報を取得
   */
  async getPersonalDashboard(): Promise<PersonalDashboard> {
    return await apiClient.get('/api/v1/analytics/personal/dashboard/')
  },
}