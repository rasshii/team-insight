import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

// 期間の型定義
type Period = "今月" | "先月" | "過去3ヶ月";

// 期間から日付範囲を計算する関数
function getDateRange(period: Period): { start: Date; end: Date } {
  const now = new Date();
  const start = new Date(now);
  const end = new Date(now);

  switch (period) {
    case "今月":
      start.setDate(1);
      break;
    case "先月":
      start.setMonth(now.getMonth() - 1);
      start.setDate(1);
      end.setDate(0);
      break;
    case "過去3ヶ月":
      start.setMonth(now.getMonth() - 3);
      break;
  }

  return { start, end };
}

// メトリクスデータを取得する関数
async function getMetrics(period: Period) {
  // TODO: 実際のデータベースからデータを取得
  // 仮のデータを返す
  return {
    leadTime: {
      value: 5.2,
      change: -0.8,
    },
    throughput: {
      value: 12,
      change: 2,
    },
    quality: {
      value: 98.5,
      change: 0.5,
    },
  };
}

// ボトルネックデータを取得する関数
async function getBottleneckData(period: Period) {
  // TODO: 実際のデータベースからデータを取得
  // 仮のデータを返す
  return [
    { status: "レビュー待ち", averageDays: 3.5, ticketCount: 8 },
    { status: "実装中", averageDays: 2.8, ticketCount: 12 },
    { status: "テスト中", averageDays: 1.5, ticketCount: 5 },
  ];
}

// スループットデータを取得する関数
async function getThroughputData(period: Period) {
  // TODO: 実際のデータベースからデータを取得
  // 仮のデータを返す
  return [
    { date: "2024-03-01", completed: 5 },
    { date: "2024-03-08", completed: 8 },
    { date: "2024-03-15", completed: 6 },
    { date: "2024-03-22", completed: 10 },
    { date: "2024-03-29", completed: 7 },
  ];
}

export async function GET(request: NextRequest) {
  try {
    // 認証チェック
    const cookieStore = cookies();
    const authToken = cookieStore.get("auth_token");
    if (!authToken) {
      return NextResponse.json({ error: "認証が必要です" }, { status: 401 });
    }

    // クエリパラメータから期間を取得
    const searchParams = request.nextUrl.searchParams;
    const period = searchParams.get("period") as Period;
    if (!period || !["今月", "先月", "過去3ヶ月"].includes(period)) {
      return NextResponse.json({ error: "無効な期間です" }, { status: 400 });
    }

    // データを取得
    const [metrics, bottleneckData, throughputData] = await Promise.all([
      getMetrics(period),
      getBottleneckData(period),
      getThroughputData(period),
    ]);

    return NextResponse.json({
      metrics,
      bottleneckData,
      throughputData,
    });
  } catch (error) {
    console.error("Error in dashboard API:", error);
    return NextResponse.json(
      { error: "データの取得に失敗しました" },
      { status: 500 }
    );
  }
}
