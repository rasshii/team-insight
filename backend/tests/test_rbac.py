"""
RBAC（Role-Based Access Control）機能のテスト

このモジュールは、権限管理システムの動作を検証します。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.project import Project
from app.models.rbac import Role, Permission, UserRole
from app.core.permissions import PermissionChecker, RoleType
from app.core.security import create_access_token
from app.db.session import SessionLocal

client = TestClient(app)


class TestPermissionChecker:
    """PermissionCheckerクラスのテスト"""
    
    def test_admin_has_all_permissions(self, test_superuser: User):
        """管理者は全ての権限を持つことを確認"""
        # 任意のロールに対してTrueを返すはず
        assert PermissionChecker.has_role(test_superuser, RoleType.ADMIN)
        assert PermissionChecker.has_role(test_superuser, RoleType.PROJECT_LEADER)
        assert PermissionChecker.has_role(test_superuser, RoleType.MEMBER)
    
    def test_has_role_with_global_role(self, db_session: Session):
        """グローバルロールの確認"""
        # テストユーザーとロールを作成
        import uuid
        unique_email = f"role_test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=unique_email,
            full_name="Role Test User",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # 既存のロールをチェック、なければ作成
        role = db_session.query(Role).filter(
            Role.name == RoleType.PROJECT_LEADER.value
        ).first()
        if not role:
            role = Role(name=RoleType.PROJECT_LEADER.value, description="Project Leader")
            db_session.add(role)
            db_session.commit()
        
        user_role = UserRole(user_id=user.id, role_id=role.id, project_id=None)
        db_session.add(user_role)
        db_session.commit()
        
        # ユーザーをリフレッシュしてリレーションを読み込む
        db_session.refresh(user)
        
        # グローバルロールを持っていることを確認
        assert PermissionChecker.has_role(user, RoleType.PROJECT_LEADER)
        assert not PermissionChecker.has_role(user, RoleType.ADMIN)
        
        # クリーンアップ
        db_session.delete(user_role)
        db_session.delete(role)
        db_session.delete(user)
        db_session.commit()
    
    def test_has_role_with_project_role(self, db_session: Session):
        """プロジェクト固有のロールの確認"""
        # テストユーザーとプロジェクトを作成
        import uuid
        unique_email = f"project_role_test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=unique_email,
            full_name="Project Role Test User",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            backlog_id=9999,
            name="Test Project for RBAC",
            project_key="RBAC-TEST"
        )
        db_session.add(project)
        db_session.commit()
        
        # 既存のロールをチェック、なければ作成
        role = db_session.query(Role).filter(
            Role.name == RoleType.MEMBER.value
        ).first()
        if not role:
            role = Role(name=RoleType.MEMBER.value, description="Member")
            db_session.add(role)
            db_session.commit()
        
        # プロジェクト固有のロールを付与
        user_role = UserRole(
            user_id=user.id, 
            role_id=role.id, 
            project_id=project.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        # ユーザーをリフレッシュ
        db_session.refresh(user)
        
        # プロジェクト固有のロールを確認
        assert PermissionChecker.has_role(user, RoleType.MEMBER, project.id)
        assert not PermissionChecker.has_role(user, RoleType.MEMBER)  # グローバルではない
        assert not PermissionChecker.has_role(user, RoleType.PROJECT_LEADER, project.id)
        
        # クリーンアップ
        db_session.delete(user_role)
        db_session.delete(role)
        db_session.delete(project)
        db_session.delete(user)
        db_session.commit()
    
    def test_check_project_access(self, test_user: User, test_project: Project, db_session: Session):
        """プロジェクトアクセス権限のチェック"""
        # セッションを共通化
        test_user = db_session.merge(test_user)
        test_project = db_session.merge(test_project)
        
        # test_userはtest_projectのメンバー
        assert PermissionChecker.check_project_access(test_user, test_project.id, db_session)
        
        # 存在しないプロジェクトへのアクセスはFalse
        assert not PermissionChecker.check_project_access(test_user, 99999, db_session)
        
        # メンバーでないユーザーのアクセスはFalse
        import uuid
        unique_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
        other_user = User(
            email=unique_email,
            full_name="Other User",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        assert not PermissionChecker.check_project_access(other_user, test_project.id, db_session)
        
        # クリーンアップ
        db_session.delete(other_user)
        db_session.commit()


class TestProjectAccessControl:
    """プロジェクトAPIのアクセス制御テスト"""
    
    def test_project_detail_requires_membership(
        self, test_user: User, test_project: Project, auth_headers: dict
    ):
        """プロジェクト詳細はメンバーのみアクセス可能"""
        # メンバーはアクセス可能
        response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == test_project.id
    
    def test_project_detail_forbidden_for_non_member(
        self, test_project: Project, db_session: Session
    ):
        """非メンバーはプロジェクト詳細にアクセス不可"""
        # 別のユーザーを作成
        import uuid
        unique_email = f"nonmember_{uuid.uuid4().hex[:8]}@example.com"
        other_user = User(
            email=unique_email,
            full_name="Non Member",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        # 認証ヘッダーを作成
        access_token = create_access_token(data={"sub": str(other_user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # アクセス拒否されることを確認
        response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=headers
        )
        assert response.status_code == 403
        assert "アクセス権限がありません" in response.json()["detail"]
        
        # クリーンアップ
        db_session.delete(other_user)
        db_session.commit()
    
    def test_project_update_requires_leader_role(
        self, test_user: User, test_project: Project, auth_headers: dict, db_session: Session
    ):
        """プロジェクト更新はリーダー権限が必要"""
        # 通常のメンバーとして更新を試みる（失敗するはず）
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"description": "Updated description"},
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "PROJECT_LEADER権限が必要" in response.json()["detail"]
        
        # リーダー権限を付与
        leader_role = db_session.query(Role).filter(
            Role.name == RoleType.PROJECT_LEADER.value
        ).first()
        
        if not leader_role:
            leader_role = Role(
                name=RoleType.PROJECT_LEADER.value,
                description="Project Leader"
            )
            db_session.add(leader_role)
            db_session.commit()
        
        user_role = UserRole(
            user_id=test_user.id,
            role_id=leader_role.id,
            project_id=test_project.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        # リーダー権限で再度試みる（成功するはず）
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"description": "Updated description"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"
        
        # クリーンアップ
        db_session.delete(user_role)
        db_session.commit()
    
    def test_project_delete_requires_admin_role(
        self, test_user: User, test_project: Project, auth_headers: dict, admin_headers: dict
    ):
        """プロジェクト削除は管理者権限が必要"""
        # 通常のユーザーとして削除を試みる（失敗するはず）
        response = client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "ADMIN権限が必要" in response.json()["detail"]
        
        # 管理者として削除を試みる（成功するはず）
        response = client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "削除しました" in response.json()["message"]


class TestRoleInheritance:
    """ロールの階層性のテスト"""
    
    def test_admin_inherits_all_permissions(self, test_superuser: User, db_session: Session):
        """管理者は全てのプロジェクト権限を継承する"""
        # プロジェクトを作成（管理者はメンバーでなくても可）
        project = Project(
            backlog_id=8888,
            name="Admin Test Project",
            project_key="ADMIN-TEST"
        )
        db_session.add(project)
        db_session.commit()
        
        # 管理者は全プロジェクトにアクセス可能
        assert PermissionChecker.check_project_access(test_superuser, project.id, db_session)
        assert PermissionChecker.check_project_permission(
            test_superuser, project.id, RoleType.PROJECT_LEADER, db_session
        )
        
        # クリーンアップ
        db_session.delete(project)
        db_session.commit()