"""
Backlog API連携のテスト用エンドポイント
本番環境では削除すること
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus

router = APIRouter()


@router.post("/create-sample-tasks")
async def create_sample_tasks(
    project_id: int,
    count: int = 10,
    db: Session = Depends(get_db_session)
):
    """
    テスト用のサンプルタスクを作成
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # サンプルユーザーを取得
    users = db.query(User).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    
    tasks_created = []
    
    for i in range(count):
        # ランダムなステータス
        status = random.choice(list(TaskStatus))
        
        # ランダムな日付
        start_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        due_date = start_date + timedelta(days=random.randint(1, 14))
        completed_date = None
        
        if status == TaskStatus.CLOSED:
            completed_date = due_date - timedelta(days=random.randint(0, 3))
        
        task = Task(
            backlog_id=10000 + i,
            backlog_key=f"{project.project_key}-{i+1}",
            project_id=project_id,
            assignee_id=random.choice(users).id,
            reporter_id=random.choice(users).id,
            title=f"タスク {i+1}: {random.choice(['機能実装', 'バグ修正', 'ドキュメント作成', 'テスト', 'レビュー'])}",
            description=f"これはテスト用のタスク {i+1} です。",
            status=status,
            priority=random.choice([2, 3, 4]),  # 高、中、低
            issue_type_id=random.choice([1, 2, 3, 4]),  # タスク、バグ、改善、その他
            issue_type_name=random.choice(["タスク", "バグ", "改善", "その他"]),
            estimated_hours=random.choice([None, 1, 2, 4, 8, 16]),
            actual_hours=random.choice([None, 0.5, 1, 2, 4, 8]) if status in [TaskStatus.RESOLVED, TaskStatus.CLOSED] else None,
            start_date=start_date,
            due_date=due_date,
            completed_date=completed_date,
            milestone_name=f"Sprint {random.randint(1, 5)}" if random.random() > 0.5 else None,
            category_names=random.choice([None, "Backend", "Frontend", "Infrastructure"])
        )
        
        db.add(task)
        tasks_created.append({
            "backlog_key": task.backlog_key,
            "title": task.title,
            "status": task.status.value
        })
    
    db.commit()
    
    return {
        "message": f"Created {count} sample tasks",
        "project_id": project_id,
        "tasks": tasks_created
    }


@router.get("/sample-sync-status")
async def get_sample_sync_status(
    db: Session = Depends(get_db_session)
):
    """
    サンプルデータの同期状況を取得
    """
    total_tasks = db.query(Task).count()
    
    status_breakdown = {}
    for status in TaskStatus:
        count = db.query(Task).filter(Task.status == status).count()
        status_breakdown[status.value] = count
    
    projects_with_tasks = db.query(Project).join(Task).distinct().count()
    
    return {
        "total_tasks": total_tasks,
        "status_breakdown": status_breakdown,
        "projects_with_tasks": projects_with_tasks,
        "sample_data": True,
        "message": "This is sample data for testing. For real Backlog sync, use /api/v1/sync endpoints"
    }