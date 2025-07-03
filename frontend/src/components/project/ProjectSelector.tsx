// frontend/src/components/project/ProjectSelector.tsx

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/hooks/queries/useProjects";
import { AlertCircle, Folder } from "lucide-react";

export function ProjectSelector() {
  const { data, isLoading, error } = useProjects();
  const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>();
  
  const projects = data?.projects || [];
  const selectedProject = projects.find((p) => p.id.toString() === selectedProjectId);

  // プロジェクト切り替え時の処理
  const handleProjectChange = (projectId: string) => {
    console.log(`📁 プロジェクトを切り替え: ${projectId}`);
    setSelectedProjectId(projectId);
  };

  if (isLoading) {
    return <Skeleton className="w-[300px] h-10" />;
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600">
        <AlertCircle className="w-4 h-4" />
        <span className="text-sm">{error instanceof Error ? error.message : 'エラーが発生しました'}</span>
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
                <span className="text-gray-500">({project.project_key})</span>
              </div>
              <div className="flex items-center gap-2">
                {project.status === 'active' ? (
                  <Badge variant="default" className="text-xs">
                    アクティブ
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-xs">
                    アーカイブ
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
