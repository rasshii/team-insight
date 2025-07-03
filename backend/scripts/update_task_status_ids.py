#!/usr/bin/env python3
"""
既存のタスクにstatus_idを設定するスクリプト

タスクのステータス（enum）に基づいて、適切なstatus_idを設定します。
これは一時的なスクリプトで、既存のデータを修正するために使用されます。
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.task import Task, TaskStatus
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backlogの標準的なステータスIDマッピング
# 注: これらのIDは一般的な値ですが、実際のBacklogスペースでは異なる可能性があります
DEFAULT_STATUS_ID_MAPPING = {
    TaskStatus.TODO: 1,        # 未対応
    TaskStatus.IN_PROGRESS: 2, # 処理中
    TaskStatus.RESOLVED: 3,    # 処理済み
    TaskStatus.CLOSED: 4       # 完了
}


def update_task_status_ids(db: Session) -> dict:
    """既存のタスクにstatus_idを設定"""
    
    updated_count = 0
    skipped_count = 0
    
    try:
        # status_idがNULLのタスクを取得
        tasks = db.query(Task).filter(Task.status_id.is_(None)).all()
        
        logger.info(f"Found {len(tasks)} tasks without status_id")
        
        for task in tasks:
            if task.status in DEFAULT_STATUS_ID_MAPPING:
                task.status_id = DEFAULT_STATUS_ID_MAPPING[task.status]
                updated_count += 1
                
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} tasks...")
                    db.commit()  # バッチコミット
            else:
                logger.warning(f"Unknown status for task {task.id}: {task.status}")
                skipped_count += 1
        
        db.commit()  # 最終コミット
        
        logger.info(f"Update completed: {updated_count} tasks updated, {skipped_count} skipped")
        
        # 更新後の統計を表示
        status_counts = {}
        for status in TaskStatus:
            count = db.query(Task).filter(
                Task.status == status,
                Task.status_id.isnot(None)
            ).count()
            status_counts[status.value] = count
        
        logger.info("Status distribution after update:")
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count}")
        
        return {
            "updated": updated_count,
            "skipped": skipped_count,
            "total": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Error updating task status IDs: {str(e)}")
        db.rollback()
        raise


def main():
    """メイン処理"""
    logger.info("Starting task status ID update...")
    
    db = SessionLocal()
    try:
        result = update_task_status_ids(db)
        logger.info(f"Update completed successfully: {result}")
    finally:
        db.close()


if __name__ == "__main__":
    main()