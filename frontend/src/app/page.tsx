"use client";

import { useAuth } from "@/hooks/useAuth";
import {
  GitBranch,
  LineChart,
  Shield,
  Target,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isInitialized } = useAuth();

  useEffect(() => {
    // 初期化が完了してから認証状態をチェック
    if (isInitialized && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isInitialized, router]);

  const features = [
    {
      icon: LineChart,
      title: "リアルタイム分析",
      description:
        "Backlogのデータをリアルタイムで分析し、チームの状況を即座に把握",
    },
    {
      icon: Target,
      title: "ボトルネック検出",
      description: "プロジェクトの遅延要因を自動検出し、改善ポイントを提案",
    },
    {
      icon: Users,
      title: "チーム最適化",
      description: "メンバーの負荷を可視化し、タスクの最適な配分を支援",
    },
    {
      icon: GitBranch,
      title: "プロセス改善",
      description: "開発フローの問題点を特定し、継続的な改善を実現",
    },
  ];

  const benefits = [
    {
      icon: Zap,
      title: "生産性が平均30%向上",
      description: "データに基づいた意思決定により、チームの生産性を大幅に改善",
    },
    {
      icon: Shield,
      title: "品質の向上",
      description: "問題の早期発見により、バグの発生を50%削減",
    },
    {
      icon: TrendingUp,
      title: "予測可能な開発",
      description: "過去のデータから精度の高い見積もりを実現",
    },
  ];

  // ローディング中は何も表示しない
  if (!isInitialized) {
    return null;
  }

  // 認証済みの場合はダッシュボードにリダイレクト
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* ヒーローセクション */}
      <div className="bg-white">
        <div className="relative isolate px-6 pt-14 lg:px-8">
          <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
            <div className="text-center">
              <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
                Team Insight
              </h1>
              <p className="mt-6 text-lg leading-8 text-gray-600">
                チームの生産性を可視化し、データドリブンな意思決定を支援するプラットフォーム
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-6">
                <Link
                  href="/auth/login"
                  className="rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                >
                  Backlogでログイン
                </Link>
                <Link
                  href="#features"
                  className="text-sm font-semibold leading-6 text-gray-900"
                >
                  詳細を見る <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 機能紹介セクション */}
      <div id="features" className="bg-gray-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-blue-600">
              より良い開発を
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              すべての機能があなたのチームをサポート
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Team
              Insightは、チームの生産性を最大化するための様々な機能を提供します
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-2">
              {features.map((feature) => (
                <div key={feature.title} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <feature.icon
                      className="h-5 w-5 flex-none text-blue-600"
                      aria-hidden="true"
                    />
                    {feature.title}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{feature.description}</p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* メリットセクション */}
      <div className="bg-white py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-blue-600">
              実績
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              導入企業の声
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Team Insightを導入した企業から、多くの成功事例が報告されています
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {benefits.map((benefit) => (
                <div key={benefit.title} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <benefit.icon
                      className="h-5 w-5 flex-none text-blue-600"
                      aria-hidden="true"
                    />
                    {benefit.title}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{benefit.description}</p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
