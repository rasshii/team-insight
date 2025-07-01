"use client";

import { ReactNode } from 'react';
import { ProtectedComponent } from './ProtectedComponent';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ShieldX } from "lucide-react";

interface AdminOnlyProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function AdminOnly({ children, fallback }: AdminOnlyProps) {
  const defaultFallback = (
    <div className="container mx-auto p-6">
      <Alert variant="destructive">
        <ShieldX className="h-4 w-4" />
        <AlertTitle>アクセス拒否</AlertTitle>
        <AlertDescription>
          このページにアクセスするには管理者権限が必要です。
        </AlertDescription>
      </Alert>
    </div>
  );

  return (
    <ProtectedComponent
      requiredRoles={['ADMIN']}
      fallback={fallback || defaultFallback}
    >
      {children}
    </ProtectedComponent>
  );
}