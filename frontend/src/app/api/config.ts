// APIのベースURL
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// APIエンドポイント
export const API_ENDPOINTS = {
  // 認証関連
  AUTH: {
    LOGIN: `${API_BASE_URL}/api/auth/login`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
    REFRESH: `${API_BASE_URL}/api/auth/refresh`,
    ME: `${API_BASE_URL}/api/auth/me`,
  },
  // ユーザー関連
  USERS: {
    BASE: `${API_BASE_URL}/api/users`,
    PROFILE: `${API_BASE_URL}/api/users/profile`,
  },
  // チーム関連
  TEAMS: {
    BASE: `${API_BASE_URL}/api/teams`,
    MEMBERS: (teamId: number) => `${API_BASE_URL}/api/teams/${teamId}/members`,
  },
  // プロジェクト関連
  PROJECTS: {
    BASE: `${API_BASE_URL}/api/projects`,
    TASKS: (projectId: number) =>
      `${API_BASE_URL}/api/projects/${projectId}/tasks`,
  },
  // ダッシュボード関連
  DASHBOARD: {
    BASE: `${API_BASE_URL}/api/dashboard`,
    STATS: `${API_BASE_URL}/api/dashboard/stats`,
  },
};

// APIリクエストのデフォルト設定
export const API_CONFIG = {
  headers: {
    "Content-Type": "application/json",
  },
  credentials: "include" as const,
};

// エラーメッセージ
export const API_ERROR_MESSAGES = {
  NETWORK_ERROR: "ネットワークエラーが発生しました。",
  UNAUTHORIZED: "認証が必要です。",
  FORBIDDEN: "アクセス権限がありません。",
  NOT_FOUND: "リソースが見つかりません。",
  SERVER_ERROR: "サーバーエラーが発生しました。",
};
