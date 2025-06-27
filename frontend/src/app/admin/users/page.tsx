import { ComingSoon } from '@/components/ComingSoon'

export default function AdminUsersPage() {
  return (
    <ComingSoon
      title="ユーザー管理"
      description="ユーザーアカウントとアクセス権限を一元管理します"
      features={[
        'ユーザー一覧の表示と検索',
        '新規ユーザーの招待と登録',
        'ユーザープロファイルの編集',
        'ロールベースアクセス制御（RBAC）の割り当て',
        'チームとプロジェクトへのメンバー割り当て',
        'アクセス履歴とセッション管理',
        'ユーザーの有効化/無効化',
        '一括インポート/エクスポート機能',
        'Backlogユーザーとの同期管理'
      ]}
      backLink={{
        href: '/dashboard/personal',
        label: '個人ダッシュボードに戻る'
      }}
    />
  )
}