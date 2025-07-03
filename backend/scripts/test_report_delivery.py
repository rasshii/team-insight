#!/usr/bin/env python3
"""
レポート配信機能のテストスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.services.report_generator import ReportGenerator
from app.services.report_email import ReportEmailService
from datetime import datetime, timedelta
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_report_delivery():
    """レポート配信のテスト"""
    db = SessionLocal()
    try:
        # 最初のアクティブユーザーを取得
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            logger.error("アクティブなユーザーが見つかりません")
            return
        
        logger.info(f"テストユーザー: {user.email} (ID: {user.id})")
        
        # レポート生成サービスのインスタンス化
        report_generator = ReportGenerator()
        email_service = ReportEmailService()
        
        # 個人週次レポートを生成
        logger.info("個人週次レポートを生成中...")
        report_data = report_generator.generate_personal_report(
            user=user,
            db=db,
            report_type="weekly"
        )
        
        # レポートデータの確認
        logger.info(f"レポートデータ: {report_data}")
        
        # メール送信
        logger.info("メールを送信中...")
        
        # メール送信
        result = email_service.send_report(
            to_email=user.email or "test@example.com",  # emailがNoneの場合のフォールバック
            report_type="weekly",
            report_data=report_data
        )
        
        if result:
            logger.info("✅ レポートメールが正常に送信されました！")
            logger.info("MailHog UI (http://localhost:8025) でメールを確認してください。")
        else:
            logger.error("❌ メール送信に失敗しました")
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    test_report_delivery()