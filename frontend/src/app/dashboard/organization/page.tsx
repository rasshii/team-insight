import { ComingSoon } from '@/components/ComingSoon'

export default function OrganizationDashboardPage() {
  return (
    <ComingSoon
      title="組織ダッシュボード"
      description="組織全体のパフォーマンスを俯瞰的に把握し、戦略的な意思決定を支援します"
      features={[
        '組織全体のKPIダッシュボード（生産性、品質、効率性）',
        '部門・チーム間の比較分析とベンチマーク',
        'プロジェクトポートフォリオの健全性評価',
        'リソース配分の最適化提案',
        '組織レベルのボトルネック検出と改善提案',
        'トレンド分析と将来予測',
        '経営層向けのエグゼクティブサマリー',
        'カスタマイズ可能なレポート生成機能'
      ]}
      backLink={{
        href: '/dashboard/personal',
        label: '個人ダッシュボードに戻る'
      }}
    />
  )
}