/**
 * RBAC機能の使用例を示すコンポーネント
 */

import { usePermissions } from '@/hooks/usePermissions';
import { ProtectedComponent, AdminOnly, ProjectLeaderOnly } from '@/components/auth/ProtectedComponent';
import { withAdminOnly, withProjectLeaderAccess } from '@/components/auth/withPermission';
import { RoleType, PERMISSIONS } from '@/types/rbac';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAppSelector } from '@/store/hooks';
import { selectCurrentUser } from '@/store/slices/authSlice';

/**
 * 管理者専用パネル（HOCを使用）
 */
const AdminPanelComponent = () => (
  <Card>
    <CardHeader>
      <CardTitle>管理者パネル</CardTitle>
    </CardHeader>
    <CardContent>
      <p>このパネルは管理者のみが表示できます。</p>
      <Button variant="destructive">システム設定</Button>
    </CardContent>
  </Card>
);

// HOCでラップ
const AdminPanel = withAdminOnly(AdminPanelComponent, 
  <Card>
    <CardContent>
      <p className="text-muted-foreground">管理者権限が必要です</p>
    </CardContent>
  </Card>
);

/**
 * プロジェクト設定（HOCを使用）
 */
const ProjectSettingsComponent = ({ projectId }: { projectId?: number }) => (
  <Card>
    <CardHeader>
      <CardTitle>プロジェクト設定</CardTitle>
    </CardHeader>
    <CardContent>
      <p>プロジェクトID: {projectId || 'グローバル'}</p>
      <p>プロジェクトリーダー以上の権限で表示されます。</p>
      <Button>設定を変更</Button>
    </CardContent>
  </Card>
);

// HOCでラップ
const ProjectSettings = withProjectLeaderAccess(ProjectSettingsComponent);

/**
 * RBAC機能の使用例
 */
export const RBACExample = () => {
  const permissions = usePermissions();
  const currentUser = useAppSelector(selectCurrentUser);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">RBAC機能デモ</h2>
        
        {/* 現在のユーザー情報 */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>現在のユーザー情報</CardTitle>
          </CardHeader>
          <CardContent>
            {currentUser ? (
              <div className="space-y-2">
                <p><strong>ユーザー名:</strong> {currentUser.name}</p>
                <p><strong>メール:</strong> {currentUser.email || 'なし'}</p>
                <div>
                  <strong>ロール:</strong>
                  <div className="mt-2 space-x-2">
                    {currentUser.user_roles.map((userRole) => (
                      <Badge key={userRole.id} variant="secondary">
                        {userRole.role.name}
                        {userRole.project_id && ` (プロジェクト: ${userRole.project_id})`}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p>ログインしていません</p>
            )}
          </CardContent>
        </Card>

        {/* 権限チェックの例 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* usePermissionsフックの使用例 */}
          <Card>
            <CardHeader>
              <CardTitle>usePermissionsフックの例</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p>管理者権限: {permissions.isAdmin() ? '✅ あり' : '❌ なし'}</p>
              <p>プロジェクト1へのアクセス: {permissions.canAccessProject(1) ? '✅ あり' : '❌ なし'}</p>
              <p>プロジェクト1の管理権限: {permissions.canManageProject(1) ? '✅ あり' : '❌ なし'}</p>
              <p>プロジェクト読み取り権限: {permissions.hasPermission(PERMISSIONS.PROJECTS_READ) ? '✅ あり' : '❌ なし'}</p>
            </CardContent>
          </Card>

          {/* 条件付き表示の例 */}
          <Card>
            <CardHeader>
              <CardTitle>条件付きレンダリング</CardTitle>
            </CardHeader>
            <CardContent>
              {permissions.isAdmin() && (
                <Button variant="destructive" className="mb-2 w-full">
                  管理者専用ボタン
                </Button>
              )}
              
              {permissions.hasRole(RoleType.PROJECT_LEADER) && (
                <Button variant="default" className="mb-2 w-full">
                  プロジェクトリーダー専用ボタン
                </Button>
              )}
              
              {permissions.hasPermission(PERMISSIONS.METRICS_EXPORT) && (
                <Button variant="outline" className="w-full">
                  メトリクスエクスポート
                </Button>
              )}
            </CardContent>
          </Card>
        </div>

        {/* ProtectedComponentの使用例 */}
        <div className="space-y-4 mt-6">
          <h3 className="text-xl font-semibold">ProtectedComponentの例</h3>
          
          {/* 管理者のみ */}
          <AdminOnly fallback={<p className="text-muted-foreground">管理者権限が必要です</p>}>
            <Card>
              <CardContent className="pt-6">
                <p className="text-green-600">✅ このコンテンツは管理者のみ表示されます</p>
              </CardContent>
            </Card>
          </AdminOnly>

          {/* プロジェクトリーダー以上 */}
          <ProjectLeaderOnly projectId={1}>
            <Card>
              <CardContent className="pt-6">
                <p className="text-blue-600">✅ プロジェクト1のリーダー権限で表示されます</p>
              </CardContent>
            </Card>
          </ProjectLeaderOnly>

          {/* 複数条件 */}
          <ProtectedComponent
            roles={[RoleType.ADMIN, RoleType.PROJECT_LEADER]}
            permissions={[PERMISSIONS.PROJECTS_MANAGE]}
            requireAll={false}
            fallback={<p className="text-muted-foreground">権限が不足しています</p>}
          >
            <Card>
              <CardContent className="pt-6">
                <p className="text-purple-600">✅ 管理者またはプロジェクトリーダーで、プロジェクト管理権限を持つユーザーのみ表示</p>
              </CardContent>
            </Card>
          </ProtectedComponent>
        </div>

        {/* HOCの使用例 */}
        <div className="space-y-4 mt-6">
          <h3 className="text-xl font-semibold">withPermission HOCの例</h3>
          
          {/* 管理者専用パネル */}
          <AdminPanel />
          
          {/* プロジェクト設定（プロジェクトID付き） */}
          <ProjectSettings projectId={1} />
          
          {/* プロジェクト設定（グローバル） */}
          <ProjectSettings />
        </div>
      </div>
    </div>
  );
};