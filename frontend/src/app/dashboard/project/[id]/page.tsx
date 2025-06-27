import { ComingSoon } from '@/components/ComingSoon'

interface ProjectDashboardPageProps {
  params: {
    id: string
  }
}

export default function ProjectDashboardPage({ params }: ProjectDashboardPageProps) {
  return (
    <ComingSoon
      title="プロジェクトダッシュボード"
      description="プロジェクトの健全性を多角的に分析し、成功への道筋を可視化します"
      features={[
        'プロジェクトの進捗状況とバーンダウンチャート',
        'スプリントベロシティの推移と予測',
        'タスクのフロー効率とサイクルタイム分析',
        'チームメンバーの貢献度と負荷状況',
        'プロジェクト固有のボトルネック検出',
        'リスク要因の早期発見と対策提案',
        'ステークホルダー向けの進捗レポート',
        'プロジェクト完了予測と必要リソース試算'
      ]}
      backLink={{
        href: '/projects',
        label: 'プロジェクト一覧に戻る'
      }}
    />
  )
}