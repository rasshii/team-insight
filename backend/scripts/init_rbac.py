#!/usr/bin/env python3
"""
RBAC初期データ投入スクリプト

このスクリプトは、システムの基本的なロールとパーミッションを
データベースに投入します。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.rbac import Role, Permission
from app.core.permissions import RoleType


def init_roles():
    """システムロールの初期化"""
    db = SessionLocal()
    
    roles_data = [
        {
            "name": RoleType.ADMIN.value,
            "description": "システム管理者",
            "is_system": True
        },
        {
            "name": RoleType.PROJECT_LEADER.value,
            "description": "プロジェクトリーダー",
            "is_system": True
        },
        {
            "name": RoleType.MEMBER.value,
            "description": "プロジェクトメンバー",
            "is_system": True
        }
    ]
    
    for role_data in roles_data:
        # 既存のロールをチェック
        existing_role = db.query(Role).filter(
            Role.name == role_data["name"]
        ).first()
        
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            print(f"ロール '{role_data['name']}' を作成しました")
        else:
            print(f"ロール '{role_data['name']}' は既に存在します")
    
    db.commit()
    db.close()


def init_permissions():
    """システムパーミッションの初期化"""
    db = SessionLocal()
    
    permissions_data = [
        # ユーザー管理
        {"name": "users.read", "resource": "users", "action": "read", 
         "description": "ユーザー情報の参照"},
        {"name": "users.write", "resource": "users", "action": "write",
         "description": "ユーザー情報の編集"},
        {"name": "users.delete", "resource": "users", "action": "delete",
         "description": "ユーザーの削除"},
        
        # プロジェクト管理
        {"name": "projects.read", "resource": "projects", "action": "read",
         "description": "プロジェクト情報の参照"},
        {"name": "projects.write", "resource": "projects", "action": "write",
         "description": "プロジェクト情報の編集"},
        {"name": "projects.delete", "resource": "projects", "action": "delete",
         "description": "プロジェクトの削除"},
        {"name": "projects.manage", "resource": "projects", "action": "manage",
         "description": "プロジェクトの管理（メンバー追加等）"},
        
        # メトリクス
        {"name": "metrics.read", "resource": "metrics", "action": "read",
         "description": "メトリクスの参照"},
        {"name": "metrics.export", "resource": "metrics", "action": "export",
         "description": "メトリクスのエクスポート"},
        
        # システム管理
        {"name": "system.admin", "resource": "system", "action": "admin",
         "description": "システム管理機能へのアクセス"},
    ]
    
    for perm_data in permissions_data:
        # 既存のパーミッションをチェック
        existing_perm = db.query(Permission).filter(
            Permission.name == perm_data["name"]
        ).first()
        
        if not existing_perm:
            permission = Permission(**perm_data)
            db.add(permission)
            print(f"パーミッション '{perm_data['name']}' を作成しました")
        else:
            print(f"パーミッション '{perm_data['name']}' は既に存在します")
    
    db.commit()
    db.close()


def assign_permissions_to_roles():
    """ロールへのパーミッション割り当て"""
    db = SessionLocal()
    
    # 各ロールに割り当てるパーミッション
    role_permissions = {
        RoleType.ADMIN.value: [
            "users.read", "users.write", "users.delete",
            "projects.read", "projects.write", "projects.delete", "projects.manage",
            "metrics.read", "metrics.export",
            "system.admin"
        ],
        RoleType.PROJECT_LEADER.value: [
            "projects.read", "projects.write", "projects.manage",
            "metrics.read", "metrics.export"
        ],
        RoleType.MEMBER.value: [
            "projects.read",
            "metrics.read"
        ]
    }
    
    for role_name, permission_names in role_permissions.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            print(f"ロール '{role_name}' が見つかりません")
            continue
        
        for perm_name in permission_names:
            permission = db.query(Permission).filter(
                Permission.name == perm_name
            ).first()
            
            if not permission:
                print(f"パーミッション '{perm_name}' が見つかりません")
                continue
            
            # 既に割り当てられているかチェック
            if permission not in role.permissions:
                role.permissions.append(permission)
                print(f"ロール '{role_name}' にパーミッション '{perm_name}' を割り当てました")
            else:
                print(f"ロール '{role_name}' には既にパーミッション '{perm_name}' が割り当てられています")
    
    db.commit()
    db.close()


def main():
    """メイン処理"""
    print("RBAC初期データの投入を開始します...")
    
    print("\n1. ロールの作成")
    init_roles()
    
    print("\n2. パーミッションの作成")
    init_permissions()
    
    print("\n3. ロールへのパーミッション割り当て")
    assign_permissions_to_roles()
    
    print("\nRBAC初期データの投入が完了しました！")


if __name__ == "__main__":
    main()