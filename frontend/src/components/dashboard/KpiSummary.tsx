"use client";

interface KpiCardProps {
  title: string;
  value: string | number;
  change: number;
  unit?: string;
}

function KpiCard({ title, value, change, unit = "" }: KpiCardProps) {
  const isPositive = change > 0;
  const changeColor = isPositive ? "text-green-600" : "text-red-600";
  const changeIcon = isPositive ? "↑" : "↓";

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <div className="mt-2 flex items-baseline">
        <p className="text-2xl font-semibold text-gray-900">
          {value}
          {unit}
        </p>
        <p
          className={`ml-2 flex items-baseline text-sm font-semibold ${changeColor}`}
        >
          <span className="sr-only">{isPositive ? "増加" : "減少"}</span>
          {changeIcon}
          {Math.abs(change)}%
        </p>
      </div>
    </div>
  );
}

interface KpiSummaryProps {
  metrics: {
    leadTime: { value: number; change: number };
    throughput: { value: number; change: number };
    quality: { value: number; change: number };
  };
}

export function KpiSummary({ metrics }: KpiSummaryProps) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
      <KpiCard
        title="平均リードタイム"
        value={metrics.leadTime.value}
        change={metrics.leadTime.change}
        unit="日"
      />
      <KpiCard
        title="スループット"
        value={metrics.throughput.value}
        change={metrics.throughput.change}
        unit="件/週"
      />
      <KpiCard
        title="品質指標"
        value={metrics.quality.value}
        change={metrics.quality.change}
        unit="%"
      />
    </div>
  );
}
