"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import {
  ArrowRight,
  GitBranch,
  LineChart,
  Shield,
  Target,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
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

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* ヘッダー */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Team Insight</h1>
          <Button onClick={() => router.push("/auth/login")} variant="default">
            ログイン
          </Button>
        </div>
      </header>

      {/* ヒーローセクション */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Backlogのデータから
            <br />
            チームの可能性を最大化
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Team Insightは、Backlogと連携してプロジェクトデータを分析し、
            チームのパフォーマンスを向上させる統合分析プラットフォームです。
          </p>
          <div className="flex gap-4 justify-center">
            <Button
              size="lg"
              onClick={() => router.push("/auth/login")}
              className="group"
            >
              今すぐ始める
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() =>
                document
                  .getElementById("features")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              詳しく見る
            </Button>
          </div>
        </div>
      </section>

      {/* 機能セクション */}
      <section id="features" className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold text-gray-900 mb-4">
            Backlogのデータを最大限に活用
          </h3>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            既存のBacklog環境をそのまま使いながら、
            高度な分析機能でチームの生産性を向上させます。
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card
                key={index}
                className="border-gray-200 hover:shadow-lg transition-all hover:-translate-y-1"
              >
                <CardHeader>
                  <Icon className="h-12 w-12 text-blue-600 mb-3" />
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* 導入効果セクション */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">導入効果</h3>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Team Insightを導入したチームの実績
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {benefits.map((benefit, index) => {
              const Icon = benefit.icon;
              return (
                <div key={index} className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                    <Icon className="h-8 w-8 text-blue-600" />
                  </div>
                  <h4 className="text-xl font-semibold mb-2">
                    {benefit.title}
                  </h4>
                  <p className="text-gray-600">{benefit.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTAセクション */}
      <section className="container mx-auto px-4 py-20">
        <Card className="max-w-4xl mx-auto bg-gradient-to-r from-blue-600 to-blue-700 text-white border-0">
          <CardContent className="p-12 text-center">
            <h3 className="text-3xl font-bold mb-4">
              チームの可能性を解き放つ
            </h3>
            <p className="text-xl mb-8 text-blue-100">
              Backlogアカウントでログインして、今すぐ分析を開始しましょう
            </p>
            <Button
              size="lg"
              onClick={() => router.push("/auth/login")}
              className="bg-white text-blue-600 hover:bg-gray-100"
            >
              無料で始める
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </section>

      {/* フッター */}
      <footer className="border-t bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-sm text-gray-600">
            <p>
              © 2024 Team Insight. Backlogと連携した統合分析プラットフォーム
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
