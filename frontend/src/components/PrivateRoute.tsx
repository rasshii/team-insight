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
  const { isAuthenticated, isInitialized, user } = useAuth();
  const router = useRouter();

  // 認証状態のログ出力
  console.log("PrivateRoute useAuth:", {
    isAuthenticated,
    isInitialized,
    user,
  });

  useEffect(() => {
    if (!isInitialized) return; // 初期化が終わるまで何もしない
    if (!isAuthenticated) {
      router.replace("/auth/login");
    }
  }, [isInitialized, isAuthenticated, router]);

  if (!isInitialized) {
    return <div>認証情報を確認中...</div>; // 必要に応じてスピナーに変更可
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
