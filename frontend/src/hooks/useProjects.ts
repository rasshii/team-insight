import { useEffect, useState } from "react";

export interface Project {
  id: number;
  name: string;
  key: string;
  memberCount: number;
  isActive: boolean;
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // プロジェクト一覧を取得
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true);
        // TODO: APIからプロジェクト一覧を取得
        const mockProjects: Project[] = [
          {
            id: 1,
            name: "Team Insight",
            key: "TI",
            memberCount: 5,
            isActive: true,
          },
          {
            id: 2,
            name: "Backlog Integration",
            key: "BI",
            memberCount: 3,
            isActive: true,
          },
        ];
        setProjects(mockProjects);
        setSelectedProject(mockProjects[0]);
      } catch (err) {
        setError("プロジェクトの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  const selectProject = (projectId: number) => {
    const project = projects.find((p) => p.id === projectId);
    setSelectedProject(project || null);
  };

  return {
    projects,
    selectedProject,
    loading,
    error,
    selectProject,
  };
}
