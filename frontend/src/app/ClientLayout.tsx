"use client";

import { useEffect } from "react";
import { Provider } from "react-redux";
import { store } from "../store";
import { useAppDispatch } from "../store/hooks";
import { initializeAuth } from "../store/slices/authSlice";

/**
 * アプリケーションの初期化を行うコンポーネント
 */
function AppInitializer({ children }: { children: React.ReactNode }) {
  const dispatch = useAppDispatch();

  useEffect(() => {
    // 認証状態を初期化
    dispatch(initializeAuth());
  }, [dispatch]);

  return <>{children}</>;
}

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Provider store={store}>
      <AppInitializer>{children}</AppInitializer>
    </Provider>
  );
}
