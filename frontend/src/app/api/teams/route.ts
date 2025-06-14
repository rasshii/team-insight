import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

interface TeamMember {
  id: string;
  name: string;
  role: string;
  avatar: string;
  status: "active" | "away" | "offline";
}

interface Team {
  id: string;
  name: string;
  description: string;
  members: TeamMember[];
  projectCount: number;
  averageVelocity: number;
  lastActivity: string;
}

// チーム一覧を取得する関数
async function getTeams(): Promise<Team[]> {
  // TODO: 実際のデータベースからデータを取得
  // 仮のデータを返す
  return [
    {
      id: "1",
      name: "フロントエンドチーム",
      description: "Webアプリケーションのフロントエンド開発を担当",
      members: [
        {
          id: "1",
          name: "山田太郎",
          role: "チームリーダー",
          avatar: "/avatars/yamada.png",
          status: "active",
        },
        {
          id: "2",
          name: "鈴木花子",
          role: "シニアエンジニア",
          avatar: "/avatars/suzuki.png",
          status: "active",
        },
        {
          id: "3",
          name: "佐藤次郎",
          role: "エンジニア",
          avatar: "/avatars/sato.png",
          status: "away",
        },
      ],
      projectCount: 3,
      averageVelocity: 15,
      lastActivity: "2024-03-20T10:30:00Z",
    },
    {
      id: "2",
      name: "バックエンドチーム",
      description: "サーバーサイドの開発とインフラを担当",
      members: [
        {
          id: "4",
          name: "田中一郎",
          role: "チームリーダー",
          avatar: "/avatars/tanaka.png",
          status: "active",
        },
        {
          id: "5",
          name: "中村美咲",
          role: "シニアエンジニア",
          avatar: "/avatars/nakamura.png",
          status: "offline",
        },
      ],
      projectCount: 2,
      averageVelocity: 12,
      lastActivity: "2024-03-19T15:45:00Z",
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

    // チーム一覧を取得
    const teams = await getTeams();

    return NextResponse.json({ teams });
  } catch (error) {
    console.error("Error in teams API:", error);
    return NextResponse.json(
      { error: "チーム一覧の取得に失敗しました" },
      { status: 500 }
    );
  }
}
