#!/usr/bin/env python
"""
メール検証機能のテストスクリプト

このスクリプトは、メール検証機能が正しく動作するかテストします。
注意：実際のメール送信を行うため、SMTPサーバーの設定が必要です。
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.email import email_service
from app.core.config import settings

async def test_email_service():
    """メールサービスのテスト"""
    
    print("=== メール検証機能テスト ===")
    print(f"SMTP設定:")
    print(f"  ホスト: {settings.SMTP_HOST}")
    print(f"  ポート: {settings.SMTP_PORT}")
    print(f"  送信元: {settings.SMTP_FROM_EMAIL}")
    print()
    
    # SMTP設定が無い場合は警告
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print("⚠️  警告: SMTP設定が不完全です。.envファイルを確認してください。")
        print("テストを中止します。")
        return
    
    # テスト用のデータ
    test_email = input("テストメールを送信するメールアドレスを入力してください: ")
    test_user_name = "テストユーザー"
    test_verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token=test-token-12345"
    
    print(f"\n検証メールを {test_email} に送信します...")
    
    try:
        # 検証メールのテスト
        success = email_service.send_verification_email(
            to_email=test_email,
            user_name=test_user_name,
            verification_url=test_verification_url
        )
        
        if success:
            print("✅ 検証メールの送信に成功しました！")
            print(f"   メールボックスを確認してください: {test_email}")
        else:
            print("❌ 検証メールの送信に失敗しました。")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return
    
    # 検証成功メールのテストも行うか確認
    send_success = input("\n検証成功通知メールもテストしますか？ (y/n): ")
    if send_success.lower() == 'y':
        print(f"\n検証成功メールを {test_email} に送信します...")
        
        try:
            success = email_service.send_verification_success_email(
                to_email=test_email,
                user_name=test_user_name
            )
            
            if success:
                print("✅ 検証成功メールの送信に成功しました！")
            else:
                print("❌ 検証成功メールの送信に失敗しました。")
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    asyncio.run(test_email_service())