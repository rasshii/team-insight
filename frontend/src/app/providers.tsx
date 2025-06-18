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

  // クライアントサイドの初期化
  useEffect(() => {
    if (!initRef.current.client) {
      initRef.current.client = true;
      setIsClient(true);
    }
  }, []);

  // 認証の初期化
  useEffect(() => {
    if (isClient && !initRef.current.auth) {
      initRef.current.auth = true;
      dispatch(initializeAuth());
    }
  }, [isClient, dispatch]);

  // 認証状態に応じたリダイレクト
  useEffect(() => {
    if (!isInitialized) return;
    const isAuthPage = pathname === "/auth/login";
    const isRootPage = pathname === "/";
    if (!isAuthenticated && !isAuthPage) {
      router.replace("/");
    } else if (isAuthenticated && (isAuthPage || isRootPage)) {
      router.replace("/dashboard");
    }
  }, [isInitialized, isAuthenticated, pathname, router]);

  // ローディング表示のメモ化
  const loadingSpinner = useMemo(
    () => (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    ),
    []
  );

  if (!isClient || !isInitialized) {
    return loadingSpinner;
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
