"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Layout } from "@/components/Layout";
import { PrivateRoute } from "@/components/PrivateRoute";
import { Skeleton } from "@/components/ui/skeleton";

export default function ProjectDashboardRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // プロジェクト一覧ページにリダイレクト
    router.replace("/projects");
  }, [router]);

  return (
    <PrivateRoute>
      <Layout>
        <div className="container mx-auto p-6 space-y-6">
          <div className="space-y-3">
            <Skeleton className="h-9 w-64" />
            <p className="text-muted-foreground">プロジェクト一覧にリダイレクトしています...</p>
          </div>
        </div>
      </Layout>
    </PrivateRoute>
  );
}