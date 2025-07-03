/**
 * タスク関連のユーティリティ関数
 */

export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';

/**
 * タスクステータスを日本語ラベルに変換
 */
export const getTaskStatusLabel = (status: TaskStatus | string): string => {
  const statusMap: Record<string, string> = {
    'TODO': '未着手',
    'IN_PROGRESS': '進行中',
    'RESOLVED': '処理済み',
    'CLOSED': '完了',
    'DONE': '完了待ち', // 互換性のため
  };
  
  return statusMap[status] || status;
};

/**
 * タスクステータスの色を取得
 */
export const getTaskStatusColor = (status: TaskStatus | string): string => {
  const colorMap: Record<string, string> = {
    'TODO': 'text-gray-600',
    'IN_PROGRESS': 'text-blue-600',
    'RESOLVED': 'text-green-600',
    'CLOSED': 'text-gray-500',
    'DONE': 'text-yellow-600', // 互換性のため
  };
  
  return colorMap[status] || 'text-gray-600';
};

/**
 * タスクステータスのバッジバリアントを取得
 */
export const getTaskStatusBadgeVariant = (status: TaskStatus | string): 'default' | 'secondary' | 'destructive' | 'outline' => {
  const variantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    'TODO': 'outline',
    'IN_PROGRESS': 'default',
    'RESOLVED': 'secondary',
    'CLOSED': 'outline',
    'DONE': 'secondary', // 互換性のため
  };
  
  return variantMap[status] || 'outline';
};