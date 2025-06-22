// frontend/src/components/project/ProjectSelector.tsx

import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/hooks/useProjects";
import { AlertCircle, Folder, Users } from "lucide-react";

export function ProjectSelector() {
  const { projects, selectedProject, loading, error, selectProject } =
    useProjects();

  // プロジェクト切り替え時の処理
  const handleProjectChange = (projectId: string) => {
    const id = parseInt(projectId, 10);
    console.log(`📁 プロジェクトを切り替え: ${id}`);
    selectProject(id);
  };

  if (loading) {
    return <Skeleton className="w-[300px] h-10" />;
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600">
        <AlertCircle className="w-4 h-4" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (!projects || projects.length === 0) {
    return (
      <div className="text-gray-500 text-sm">プロジェクトがありません</div>
    );
  }

  return (
    <Select
      value={selectedProject?.id.toString()}
      onValueChange={handleProjectChange}
    >
      <SelectTrigger className="w-[300px]">
        <SelectValue placeholder="プロジェクトを選択してください" />
      </SelectTrigger>
      <SelectContent>
        {projects.map((project) => (
          <SelectItem
            key={project.id}
            value={project.id.toString()}
            className="cursor-pointer"
          >
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <Folder className="w-4 h-4 text-gray-500" />
                <span className="font-medium">{project.name}</span>
                <span className="text-gray-500">({project.key})</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  <Users className="w-3 h-3 mr-1" />
                  {project.memberCount}
                </Badge>
                {project.isActive ? (
                  <Badge variant="default" className="text-xs">
                    アクティブ
                  </Badge>
                ) : (
                  <Badge variant="default" className="text-xs">
                    非アクティブ
                  </Badge>
                )}
              </div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
