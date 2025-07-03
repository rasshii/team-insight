"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Layout } from "@/components/Layout";
import { UserCircle, Settings, Shield, Link2 } from "lucide-react";

const settingsNavigation = [
  { name: "プロフィール", href: "/settings/profile", icon: UserCircle },
  { name: "アカウント設定", href: "/settings/account", icon: Settings },
  { name: "Backlog連携", href: "/settings/backlog", icon: Link2 },
  { name: "セキュリティ", href: "/settings/security", icon: Shield },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <Layout>
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-3xl font-bold mb-8">設定</h1>
          
          <div className="flex gap-8">
            {/* サイドバーナビゲーション */}
            <nav className="w-64 space-y-1">
              {settingsNavigation.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 px-4 py-2 text-sm font-medium rounded-md transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-gray-700 hover:bg-gray-100"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
            
            {/* メインコンテンツ */}
            <div className="flex-1">
              {children}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}