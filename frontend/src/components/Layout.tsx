import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "./ui/button";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <nav className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-xl font-bold">
                Team Insight
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" asChild>
                <Link to="/">ホーム</Link>
              </Button>
              <Button variant="ghost" asChild>
                <Link to="/dashboard">ダッシュボード</Link>
              </Button>
              <Button variant="ghost" asChild>
                <Link to="/projects">プロジェクト</Link>
              </Button>
              <Button variant="ghost" asChild>
                <Link to="/team">チーム</Link>
              </Button>
            </div>
            <div className="flex items-center space-x-4">
              {/* ユーザー情報 */}
              {user && (
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-700">{user.name}</span>
                  <Button variant="outline" size="sm" onClick={logout}>
                    ログアウト
                  </Button>
                </div>
              )}
            </div>
          </nav>
        </div>
      </header>
      <main className="flex-1 container mx-auto px-4 py-8">{children}</main>
      <footer className="border-t">
        <div className="container mx-auto px-4 py-6">
          <p className="text-center text-sm text-muted-foreground">
            © 2024 Team Insight. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
