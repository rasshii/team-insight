"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Provider } from "react-redux";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { store } from "../store";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import { initializeAuth } from "../store/slices/authSlice";

// クライアントサイドの初期化を管理するコンポーネント
const AuthInitializer = ({ children }: { children: React.ReactNode }) => {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const pathname = usePathname();
  const { isInitialized, isAuthenticated } = useAppSelector(
    (state) => state.auth
  );
  const [isClient, setIsClient] = useState(false);
  const initRef = useRef({ client: false, auth: false });
  const renderCountRef = useRef(0);

  // クライアントサイドの初期化
  useEffect(() => {
    if (!initRef.current.client) {
      initRef.current.client = true;
      console.log("クライアントサイドの初期化を開始");
      setIsClient(true);
    }
  }, []);

  // 認証の初期化
  useEffect(() => {
    if (isClient && !initRef.current.auth) {
      initRef.current.auth = true;
      console.log("認証の初期化を開始");
      dispatch(initializeAuth());
    }
  }, [isClient, dispatch]);

  // 認証状態に応じたリダイレクト
  useEffect(() => {
    if (!isInitialized) return; // 初期化が終わるまで何もしない
    const isAuthPage = pathname === "/auth/login";
    const isRootPage = pathname === "/";
    if (!isAuthenticated && !isAuthPage) {
      console.log("未認証状態: ログインページにリダイレクト");
      router.replace("/auth/login");
    } else if (isAuthenticated && (isAuthPage || isRootPage)) {
      console.log("認証済み状態: ダッシュボードにリダイレクト");
      router.replace("/dashboard");
      console.log("リダイレクト実行");
    }
  }, [isInitialized, isAuthenticated, pathname, router]);

  // デバッグ用のログ
  useEffect(() => {
    renderCountRef.current += 1;
    if (renderCountRef.current <= 3) {
      console.log("AuthInitializer - 状態:", {
        isClient,
        isInitialized,
        isAuthenticated,
        pathname,
        renderCount: renderCountRef.current,
      });
    }
  }, [isClient, isInitialized, isAuthenticated, pathname]);

  // ローディング表示のメモ化
  const loadingSpinner = useMemo(
    () => (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    ),
    []
  );

  // クライアントサイドの初期化待ち
  if (!isClient) {
    return loadingSpinner;
  }

  // 認証の初期化待ち
  if (!isInitialized) {
    return loadingSpinner;
  }

  // 認証の初期化完了
  if (renderCountRef.current <= 3) {
    console.log("認証の初期化完了 - 子コンポーネントをレンダリング");
  }
  return <>{children}</>;
};

// プロバイダーコンポーネント
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <AuthInitializer>{children}</AuthInitializer>
    </Provider>
  );
}
