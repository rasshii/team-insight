"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ExternalLink, Info } from "lucide-react";

interface BacklogLogoutInfoProps {
  spaceKey?: string;
}

export function BacklogLogoutInfo({ spaceKey = "nulab-exam" }: BacklogLogoutInfoProps) {
  const backlogUrl = `https://${spaceKey}.backlog.jp`;
  
  return (
    <Alert className="mb-4">
      <Info className="h-4 w-4" />
      <AlertTitle>別のBacklogアカウントでログインする方法</AlertTitle>
      <AlertDescription className="space-y-2">
        <p>
          現在のBacklogアカウントからログアウトしてから、
          別のアカウントでログインしてください。
        </p>
        <div className="flex gap-2 mt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(`${backlogUrl}/Logout.action`, '_blank')}
          >
            <ExternalLink className="mr-2 h-3 w-3" />
            Backlogからログアウト
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );
}