"use client";

import { BottleneckChart } from "@/components/dashboard/BottleneckChart";
import { FilterBar } from "@/components/dashboard/FilterBar";
import { KpiSummary } from "@/components/dashboard/KpiSummary";
import { ThroughputChart } from "@/components/dashboard/ThroughputChart";
import { Loading } from "@/components/ui/loading";
import { useAuth } from "@/hooks/useAuth";
import { Period } from "@/types/period";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface Metrics {
  leadTime: {
    value: number;
    change: number;
  };
  throughput: {
    value: number;
    change: number;
  };
  quality: {
    value: number;
    change: number;
  };
}

interface BottleneckData {
  status: string;
  averageDays: number;
  ticketCount: number;
}

interface ThroughputData {
  date: string;
  completed: number;
}

interface DashboardData {
  metrics: Metrics;
  bottleneckData: BottleneckData[];
  throughputData: ThroughputData[];
}

export default function Dashboard() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [selectedPeriod, setSelectedPeriod] = useState<Period>("今月");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/api/dashboard?period=${selectedPeriod}`);
        if (!response.ok) {
          throw new Error("データの取得に失敗しました");
        }

        const data = await response.json();
        setDashboardData(data);
      } catch (err) {
        setError("データの取得に失敗しました");
        console.error("Error fetching dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [selectedPeriod]);

  if (!isAuthenticated) {
    return null;
  }

  if (loading) {
    return <Loading text="ダッシュボードデータを読み込み中..." />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  const handlePeriodChange = (period: Period) => {
    setSelectedPeriod(period);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
        <p className="mt-2 text-gray-600">
          プロジェクトの進捗状況とパフォーマンス指標
        </p>
      </div>

      <div className="mb-6">
        <FilterBar
          selectedPeriod={selectedPeriod}
          onPeriodChange={handlePeriodChange}
        />
      </div>

      {dashboardData?.metrics && (
        <div className="mb-8">
          <KpiSummary metrics={dashboardData.metrics} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BottleneckChart data={dashboardData?.bottleneckData || []} />
        <ThroughputChart data={dashboardData?.throughputData || []} />
      </div>
    </div>
  );
}
