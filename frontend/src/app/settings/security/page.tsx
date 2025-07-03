"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  useLoginHistory, 
  useActivityLogs, 
  useSessions,
  useTerminateSession 
} from "@/hooks/queries/useUserSettings";
import { useState } from "react";
import { 
  Shield, 
  Activity, 
  LogIn, 
  AlertCircle,
  Monitor,
  Smartphone,
  Globe,
  LogOut,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

export default function SecuritySettingsPage() {
  const [loginHistoryPage, setLoginHistoryPage] = useState(1);
  const [activityLogsPage, setActivityLogsPage] = useState(1);
  
  const { data: loginHistory, isLoading: loginHistoryLoading } = useLoginHistory(loginHistoryPage);
  const { data: activityLogs, isLoading: activityLogsLoading } = useActivityLogs(activityLogsPage);
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions();
  const terminateSessionMutation = useTerminateSession();

  const getDeviceIcon = (userAgent?: string) => {
    if (!userAgent) return <Globe className="h-4 w-4" />;
    if (userAgent.includes("Mobile")) return <Smartphone className="h-4 w-4" />;
    return <Monitor className="h-4 w-4" />;
  };

  const getActivityDescription = (action: string, details?: any) => {
    switch (action) {
      case "login":
        return "ログイン";
      case "logout":
        return "ログアウト";
      case "update_settings":
        return "設定を更新";
      case "update_profile":
        return "プロフィールを更新";
      case "terminate_session":
        return "セッションを終了";
      default:
        return action;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">セキュリティ設定</h2>
        <p className="text-muted-foreground">
          アカウントのセキュリティとアクティビティを管理します
        </p>
      </div>

      {/* アクティブセッション */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            アクティブセッション
          </CardTitle>
          <CardDescription>
            現在ログイン中のデバイスとセッション
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : sessionsData?.sessions && sessionsData.sessions.length > 0 ? (
            <div className="space-y-4">
              {sessionsData.sessions.map((session) => (
                <div
                  key={session.session_id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    {getDeviceIcon(session.user_agent)}
                    <div>
                      <div className="font-medium">
                        {session.user_agent?.split(" ")[0] || "Unknown Device"}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {session.ip_address || "Unknown IP"}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        ログイン時刻: {format(new Date(session.login_at), "yyyy/MM/dd HH:mm", { locale: ja })}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {session.is_current && (
                      <Badge variant="secondary">現在のセッション</Badge>
                    )}
                    {!session.is_current && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => terminateSessionMutation.mutate(session.session_id)}
                        disabled={terminateSessionMutation.isPending}
                      >
                        <LogOut className="h-4 w-4 mr-1" />
                        終了
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                アクティブなセッションがありません
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* ログイン履歴 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LogIn className="h-5 w-5" />
            ログイン履歴
          </CardTitle>
          <CardDescription>
            最近のログイン活動
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loginHistoryLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : loginHistory?.items && loginHistory.items.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>デバイス</TableHead>
                    <TableHead>IPアドレス</TableHead>
                    <TableHead>ログイン時刻</TableHead>
                    <TableHead>ログアウト時刻</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loginHistory.items.map((history) => (
                    <TableRow key={history.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getDeviceIcon(history.user_agent)}
                          <span className="text-sm">
                            {history.user_agent?.split(" ")[0] || "Unknown"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {history.ip_address || "-"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {format(new Date(history.login_at), "yyyy/MM/dd HH:mm", { locale: ja })}
                      </TableCell>
                      <TableCell className="text-sm">
                        {history.logout_at
                          ? format(new Date(history.logout_at), "yyyy/MM/dd HH:mm", { locale: ja })
                          : "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* ページネーション */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  全 {loginHistory.total} 件中 {((loginHistoryPage - 1) * 20) + 1} - {Math.min(loginHistoryPage * 20, loginHistory.total)} 件
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setLoginHistoryPage(loginHistoryPage - 1)}
                    disabled={loginHistoryPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setLoginHistoryPage(loginHistoryPage + 1)}
                    disabled={loginHistoryPage * 20 >= loginHistory.total}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                ログイン履歴がありません
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* アクティビティログ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            アクティビティログ
          </CardTitle>
          <CardDescription>
            アカウントの最近の活動
          </CardDescription>
        </CardHeader>
        <CardContent>
          {activityLogsLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : activityLogs?.items && activityLogs.items.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>アクション</TableHead>
                    <TableHead>詳細</TableHead>
                    <TableHead>IPアドレス</TableHead>
                    <TableHead>日時</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {activityLogs.items.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-medium">
                        {getActivityDescription(log.action, log.details)}
                      </TableCell>
                      <TableCell className="text-sm">
                        {log.resource_type && log.resource_id
                          ? `${log.resource_type} #${log.resource_id}`
                          : "-"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {log.ip_address || "-"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {format(new Date(log.created_at), "yyyy/MM/dd HH:mm", { locale: ja })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* ページネーション */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  全 {activityLogs.total} 件中 {((activityLogsPage - 1) * 50) + 1} - {Math.min(activityLogsPage * 50, activityLogs.total)} 件
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActivityLogsPage(activityLogsPage - 1)}
                    disabled={activityLogsPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActivityLogsPage(activityLogsPage + 1)}
                    disabled={activityLogsPage * 50 >= activityLogs.total}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                アクティビティログがありません
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}