import { ComingSoon } from '@/components/ComingSoon'

export default function AdminSettingsPage() {
  return (
    <ComingSoon
      title="管理設定"
      description="システム全体の設定とカスタマイズを管理します"
      features={[
        '組織情報の管理（会社名、ロゴ、連絡先）',
        'Backlog API連携の詳細設定',
        'データ同期スケジュールの設定',
        'システム全体の権限ポリシー管理',
        'カスタムロールと権限の作成',
        '通知設定とアラートルールの定義',
        'データ保持ポリシーとアーカイブ設定',
        'システムログとセキュリティ監査',
        'バックアップとリストア機能'
      ]}
      backLink={{
        href: '/dashboard/personal',
        label: '個人ダッシュボードに戻る'
      }}
    />
  )
}