import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    // ダミーデータを返す
    const dashboardData = {
      projects: [
        {
          id: 1,
          name: "プロジェクトA",
          key: "PROJ-A",
          status: "active",
          issueCount: 15,
        },
        {
          id: 2,
          name: "プロジェクトB",
          key: "PROJ-B",
          status: "active",
          issueCount: 8,
        },
      ],
      teams: [
        {
          id: 1,
          name: "開発チーム",
          memberCount: 5,
        },
        {
          id: 2,
          name: "デザインチーム",
          memberCount: 3,
        },
      ],
      stats: {
        totalProjects: 2,
        totalTeams: 2,
        totalIssues: 23,
        activeIssues: 18,
      },
    };

    return NextResponse.json(dashboardData);
  } catch (error) {
    console.error("Dashboard API Error:", error);
    return NextResponse.json(
      { error: "サーバーエラーが発生しました" },
      { status: 500 }
    );
  }
}
