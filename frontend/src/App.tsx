import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import PrivateRoute from "./components/PrivateRoute";
import { AuthProvider } from "./contexts/AuthContext";
import AuthCallback from "./pages/AuthCallback";
import Login from "./pages/Login";

function App() {
  return (
    <Router>
      <AuthProvider>
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
      </AuthProvider>
    </Router>
  );
}

export default App;
