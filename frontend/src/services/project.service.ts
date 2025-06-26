import { env } from "@/config/env";

interface Project {
  id: number;
  name: string;
  key: string;
  status: string;
  issueCount: number;
}

class ProjectService {
  async getProjects(): Promise<Project[]> {
    const response = await fetch(`http://localhost/api/v1/projects`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // HttpOnlyクッキーを含める
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("認証が必要です");
      }
      throw new Error("プロジェクトデータの取得に失敗しました");
    }

    return response.json();
  }

  async getProject(projectId: string): Promise<Project> {
    const response = await fetch(`http://localhost/api/v1/projects/${projectId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("認証が必要です");
      }
      if (response.status === 404) {
        throw new Error("プロジェクトが見つかりません");
      }
      throw new Error("プロジェクトデータの取得に失敗しました");
    }

    return response.json();
  }
}

export const projectService = new ProjectService();