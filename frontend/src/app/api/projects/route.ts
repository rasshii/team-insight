import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

interface Project {
  id: string;
  name: string;
  description: string;
  status: "active" | "completed" | "archived";
  startDate: string;
  endDate: string | null;
  teamSize: number;
  progress: number;
}

// プロジェクト一覧を取得する関数
async function getProjects(): Promise<Project[]> {
  // TODO: 実際のデータベースからデータを取得
  // 仮のデータを返す
  return [
    {
      id: "1",
      name: "新規Webアプリケーション開発",
      description: "モダンなWebアプリケーションの開発プロジェクト",
      status: "active",
      startDate: "2024-01-01",
      endDate: "2024-06-30",
      teamSize: 8,
      progress: 45,
    },
    {
      id: "2",
      name: "既存システムのリファクタリング",
      description: "レガシーシステムの改善と最適化",
      status: "active",
      startDate: "2024-02-01",
      endDate: "2024-05-31",
      teamSize: 5,
      progress: 30,
    },
    {
      id: "3",
      name: "モバイルアプリ開発",
      description: "iOS/Android向けネイティブアプリの開発",
      status: "completed",
      startDate: "2023-10-01",
      endDate: "2024-01-31",
      teamSize: 6,
      progress: 100,
    },
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

    // プロジェクト一覧を取得
    const projects = await getProjects();

    return NextResponse.json({ projects });
  } catch (error) {
    console.error("Error in projects API:", error);
    return NextResponse.json(
      { error: "プロジェクト一覧の取得に失敗しました" },
      { status: 500 }
    );
  }
}
