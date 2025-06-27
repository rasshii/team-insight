"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import { Provider } from "react-redux";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { store } from "../store";
import { queryClient } from "../lib/react-query";

// プロバイダーコンポーネント
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <AuthInitializer>{children}</AuthInitializer>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </Provider>
  );
}

// 認証の初期化を管理するコンポーネント
function AuthInitializer({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  
  // React Queryで現在のユーザー情報を取得
  const { data: user, isLoading } = useCurrentUser();
  
  // 認証状態に応じたリダイレクト
  useEffect(() => {
    if (isLoading) return;
    
    const isAuthPage = pathname === "/auth/login" || pathname === "/auth/callback";
    const isRootPage = pathname === "/";
    const isAuthenticated = !!user;
    
    console.log('[AuthInitializer] Redirect check:', {
      pathname,
      isLoading,
      isAuthenticated,
      isAuthPage,
      isRootPage
    });
    
    if (!isAuthenticated && !isAuthPage && !isRootPage) {
      console.log('[AuthInitializer] Redirecting to login...');
      router.replace("/auth/login");
    } else if (isAuthenticated && isRootPage) {
      console.log('[AuthInitializer] Redirecting to dashboard...');
      router.replace("/dashboard/personal");
    }
  }, [isLoading, user, pathname, router]);

  // ローディング表示のメモ化
  const loadingSpinner = useMemo(
    () => (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    ),
    []
  );

  if (isLoading) {
    return loadingSpinner;
  }

  return <>{children}</>;
}

// useCurrentUserフックをインポート（循環参照を避けるため、ここでインライン実装）
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../lib/react-query";
import { authService } from "../services/auth.service";
import { useAppDispatch } from "../store/hooks";
import { setUser, initializeAuth } from "../store/slices/authSlice";

function useCurrentUser() {
  const dispatch = useAppDispatch();

  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: async () => {
      try {
        console.log('[AuthInitializer] Fetching current user...');
        const user = await authService.getCurrentUser();
        console.log('[AuthInitializer] User fetched successfully:', user);
        dispatch(setUser(user));
        return user;
      } catch (error) {
        console.error('[AuthInitializer] Error fetching user:', error);
        // 401エラーの場合は正常な未認証状態として扱う
        dispatch(initializeAuth());
        return null;
      }
    },
    staleTime: 10 * 60 * 1000, // 10分
    retry: false,
  });
}