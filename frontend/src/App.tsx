import React, { useEffect } from "react";
import { Provider } from "react-redux";
import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import PrivateRoute from "./components/PrivateRoute";
import AuthCallback from "./pages/AuthCallback";
import Login from "./pages/Login";
import { store } from "./store";
import { useAppDispatch } from "./store/hooks";
import { initializeAuth } from "./store/slices/authSlice";

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

function App() {
  return (
    <Provider store={store}>
      <Router>
        <AppInitializer>
          <Routes>
            {/* 公開ルート */}
            <Route path="/login" element={<Login />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            {/* 認証が必要なルート */}
            <Route
              path="/*"
              element={
                <PrivateRoute>
                  <Layout>
                    <Routes>
                      <Route path="/" element={<div>ホームページ</div>} />
                      <Route
                        path="/dashboard"
                        element={<div>ダッシュボード</div>}
                      />
                      <Route
                        path="/projects"
                        element={<div>プロジェクト一覧</div>}
                      />
                      <Route path="/team" element={<div>チーム管理</div>} />
                    </Routes>
                  </Layout>
                </PrivateRoute>
              }
            />
          </Routes>
        </AppInitializer>
      </Router>
    </Provider>
  );
}

export default App;
