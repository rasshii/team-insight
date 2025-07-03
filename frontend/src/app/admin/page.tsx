"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, Settings, Shield, Database } from "lucide-react";
import Link from "next/link";
import { ProtectedComponent } from "@/components/auth/ProtectedComponent";

export default function AdminDashboard() {
  return (
    <ProtectedComponent requiredRoles={["ADMIN"]}>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-8">管理者ダッシュボード</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link href="/admin/users">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center space-x-4">
                <Users className="h-10 w-10 text-blue-500" />
                <div>
                  <h2 className="text-xl font-semibold">ユーザー管理</h2>
                  <p className="text-gray-600">ユーザーの一覧とロール管理</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link href="/admin/settings">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center space-x-4">
                <Settings className="h-10 w-10 text-green-500" />
                <div>
                  <h2 className="text-xl font-semibold">システム設定</h2>
                  <p className="text-gray-600">アプリケーションの設定管理</p>
                </div>
              </div>
            </Card>
          </Link>

          <Card className="p-6 opacity-50 cursor-not-allowed">
            <div className="flex items-center space-x-4">
              <Shield className="h-10 w-10 text-purple-500" />
              <div>
                <h2 className="text-xl font-semibold">権限管理</h2>
                <p className="text-gray-600">ロールと権限の設定（準備中）</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 opacity-50 cursor-not-allowed">
            <div className="flex items-center space-x-4">
              <Database className="h-10 w-10 text-orange-500" />
              <div>
                <h2 className="text-xl font-semibold">データ管理</h2>
                <p className="text-gray-600">バックアップとリストア（準備中）</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </ProtectedComponent>
  );
}