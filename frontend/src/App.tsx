import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Layout from "./components/Layout";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<div>ホームページ</div>} />
          <Route path="/dashboard" element={<div>ダッシュボード</div>} />
          <Route path="/projects" element={<div>プロジェクト一覧</div>} />
          <Route path="/team" element={<div>チーム管理</div>} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
