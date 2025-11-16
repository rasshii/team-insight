/**
 * @fileoverview プライベートルートコンポーネント
 *
 * 認証が必要なページを保護し、未認証ユーザーをログインページにリダイレクトする
 * 認証ガードコンポーネントです。
 *
 * @module PrivateRoute
 */

"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * プライベートルートのプロパティ型定義
 */
interface PrivateRouteProps {
  /** 認証保護するコンテンツ */
  children: React.ReactNode;
}

/**
 * プライベートルートコンポーネント
 *
 * 認証が必要なページを保護する高階コンポーネント（HOC）です。
 * ユーザーの認証状態を確認し、未認証の場合はログインページにリダイレクトします。
 *
 * ## 動作フロー
 * 1. 初期化待機: 認証状態の初期化が完了するまで待機
 * 2. 認証チェック: ユーザーが認証済みかどうかを確認
 * 3. リダイレクト: 未認証の場合は/auth/loginにリダイレクト
 * 4. コンテンツ表示: 認証済みの場合は子要素を表示
 *
 * @param {PrivateRouteProps} props - コンポーネントのプロパティ
 * @returns {JSX.Element | null} 認証済みの場合は子要素、未認証の場合はnull
 *
 * @example
 * ```tsx
 * // ページコンポーネントでの使用
 * export default function DashboardPage() {
 *   return (
 *     <PrivateRoute>
 *       <Dashboard />
 *     </PrivateRoute>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Layoutコンポーネントと組み合わせて使用
 * export default function ProfilePage() {
 *   return (
 *     <PrivateRoute>
 *       <Layout>
 *         <Profile />
 *       </Layout>
 *     </PrivateRoute>
 *   );
 * }
 * ```
 *
 * @remarks
 * - 初期化中は「認証情報を確認中...」というテキストを表示します
 * - リダイレクトにはrouter.replace()を使用（履歴に残さない）
 * - Next.js App Routerのクライアントコンポーネントとして動作
 *
 * @see {@link useAuth} - 認証状態管理フック
 * @see {@link Layout} - 共通レイアウトコンポーネント（通常PrivateRouteでラップ）
 */
export function PrivateRoute({ children }: PrivateRouteProps) {
  const { isAuthenticated, isInitialized, user } = useAuth();
  const router = useRouter();

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
