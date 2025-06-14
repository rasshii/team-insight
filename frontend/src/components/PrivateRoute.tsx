/**
 * プライベートルートコンポーネント
 *
 * 認証が必要なルートを保護し、
 * 未認証ユーザーをログインページにリダイレクトします。
 */

"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * プライベートルートのプロパティ
 */
interface PrivateRouteProps {
  children: React.ReactNode;
}

/**
 * プライベートルートコンポーネント
 *
 * 認証状態を確認し、未認証の場合はログインページにリダイレクトします。
 * ローディング中は、ローディング表示を行います。
 */
export function PrivateRoute({ children }: PrivateRouteProps) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
