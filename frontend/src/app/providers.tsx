"use client";

import { useEffect } from "react";
import { Provider } from "react-redux";
import { useAuth } from "../hooks/useAuth";
import { store } from "../store";
import { initializeAuth } from "../store/slices/authSlice";

function AuthInitializer({ children }: { children: React.ReactNode }) {
  const { isInitialized } = useAuth();

  useEffect(() => {
    if (!isInitialized) {
      store.dispatch(initializeAuth());
    }
  }, [isInitialized]);

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <AuthInitializer>{children}</AuthInitializer>
    </Provider>
  );
}
