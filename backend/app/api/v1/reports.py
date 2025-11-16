"""
レポート配信API

分析レポートの配信設定と管理を行うAPIエンドポイントです。
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import status as http_status
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.schemas.report import (
    ReportType,
    ReportRecipientType,
    ReportScheduleRequest,
    ReportScheduleResponse,
    TestReportRequest,
    ReportScheduleListResponse,
)
from app.services.report_generator import report_generator
from app.services.report_email import report_email_service
from app.core.permissions import PermissionChecker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/test", status_code=http_status.HTTP_202_ACCEPTED)
async def send_test_report(
    request: TestReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
) -> dict:
    """
    テストレポートを送信

    指定された設定でテストレポートを即座に送信します。
    """
    try:
        # プロジェクトレポートの場合、権限チェック
        if request.recipient_type == ReportRecipientType.PROJECT:
            if not request.project_id:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST, detail="プロジェクトレポートにはproject_idが必要です"
                )

            project = db.query(Project).options(joinedload(Project.members)).filter(Project.id == request.project_id).first()

            if not project:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="プロジェクトが見つかりません")

            # プロジェクトメンバーかチェック
            if not any(member.id == current_user.id for member in project.members):
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN, detail="このプロジェクトのレポートを送信する権限がありません"
                )

        # 送信先メールアドレス
        to_email = request.email or current_user.email
        if not to_email:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="送信先メールアドレスが設定されていません"
            )

        # バックグラウンドでレポート送信
        background_tasks.add_task(
            _send_report_task,
            user=current_user,
            report_type=request.report_type,
            recipient_type=request.recipient_type,
            project_id=request.project_id,
            to_email=to_email,
            db=db,
        )

        return {"message": "テストレポートの送信を開始しました", "email": to_email}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test report: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="テストレポートの送信に失敗しました"
        )


@router.get("/schedules", response_model=ReportScheduleListResponse)
async def get_report_schedules(
    current_user: User = Depends(deps.get_current_active_user), db: Session = Depends(deps.get_db_session)
) -> ReportScheduleListResponse:
    """
    レポート配信スケジュール一覧を取得

    現在のユーザーのレポート配信スケジュール設定を取得します。
    """
    from app.models.report_schedule import ReportSchedule

    schedules = db.query(ReportSchedule).filter(ReportSchedule.user_id == current_user.id).all()

    return ReportScheduleListResponse(
        schedules=[ReportScheduleResponse.model_validate(s) for s in schedules], total=len(schedules)
    )


@router.post("/schedules", response_model=ReportScheduleResponse)
async def create_report_schedule(
    request: ReportScheduleRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
) -> ReportScheduleResponse:
    """
    レポート配信スケジュールを作成

    新しいレポート配信スケジュールを設定します。
    """
    from app.models.report_schedule import ReportSchedule
    from app.services.report_scheduler import report_scheduler
    from datetime import time as datetime_time

    # プロジェクトレポートの場合、権限チェック
    if request.recipient_type == ReportRecipientType.PROJECT:
        if not request.project_id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="プロジェクトレポートにはproject_idが必要です"
            )

        project = db.query(Project).filter(Project.id == request.project_id).first()

        if not project:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="プロジェクトが見つかりません")

        # プロジェクトメンバーかチェック
        if not any(member.id == current_user.id for member in project.members):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="このプロジェクトのレポートスケジュールを作成する権限がありません",
            )

    # 既存のスケジュールをチェック（同じタイプ・受信者の重複を防ぐ）
    existing = (
        db.query(ReportSchedule)
        .filter(
            ReportSchedule.user_id == current_user.id,
            ReportSchedule.report_type == request.report_type,
            ReportSchedule.recipient_type == request.recipient_type,
            ReportSchedule.project_id == request.project_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="同じタイプのスケジュールが既に存在します")

    # 送信時刻の変換
    send_time = None
    if request.send_time:
        hour, minute = map(int, request.send_time.split(":"))
        send_time = datetime_time(hour=hour, minute=minute)

    # スケジュールを作成
    schedule = ReportSchedule(
        user_id=current_user.id,
        report_type=request.report_type,
        recipient_type=request.recipient_type,
        project_id=request.project_id,
        enabled=request.enabled,
        send_time=send_time,
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # スケジューラーに登録
    if schedule.enabled:
        report_scheduler.add_schedule(schedule)

    return ReportScheduleResponse.model_validate(schedule)


@router.put("/schedules/{schedule_id}", response_model=ReportScheduleResponse)
async def update_report_schedule(
    schedule_id: int,
    request: ReportScheduleRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
) -> ReportScheduleResponse:
    """
    レポート配信スケジュールを更新

    既存のレポート配信スケジュールを更新します。
    """
    from app.models.report_schedule import ReportSchedule
    from app.services.report_scheduler import report_scheduler
    from datetime import time as datetime_time

    # スケジュールを取得
    schedule = (
        db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id, ReportSchedule.user_id == current_user.id).first()
    )

    if not schedule:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="スケジュールが見つかりません")

    # プロジェクトレポートの場合、権限チェック
    if request.recipient_type == ReportRecipientType.PROJECT:
        if not request.project_id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="プロジェクトレポートにはproject_idが必要です"
            )

        project = db.query(Project).filter(Project.id == request.project_id).first()

        if not project:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="プロジェクトが見つかりません")

        # プロジェクトメンバーかチェック
        if not any(member.id == current_user.id for member in project.members):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="このプロジェクトのレポートスケジュールを更新する権限がありません",
            )

    # 送信時刻の変換
    send_time = None
    if request.send_time:
        hour, minute = map(int, request.send_time.split(":"))
        send_time = datetime_time(hour=hour, minute=minute)

    # スケジュールを更新
    schedule.report_type = request.report_type
    schedule.recipient_type = request.recipient_type
    schedule.project_id = request.project_id
    schedule.enabled = request.enabled
    schedule.send_time = send_time

    db.commit()
    db.refresh(schedule)

    # スケジューラーを更新
    report_scheduler.update_schedule(schedule)

    return ReportScheduleResponse.model_validate(schedule)


@router.delete("/schedules/{schedule_id}")
async def delete_report_schedule(
    schedule_id: int, current_user: User = Depends(deps.get_current_active_user), db: Session = Depends(deps.get_db_session)
) -> dict:
    """
    レポート配信スケジュールを削除

    指定されたレポート配信スケジュールを削除します。
    """
    from app.models.report_schedule import ReportSchedule
    from app.services.report_scheduler import report_scheduler

    # スケジュールを取得
    schedule = (
        db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id, ReportSchedule.user_id == current_user.id).first()
    )

    if not schedule:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="スケジュールが見つかりません")

    # スケジューラーから削除
    report_scheduler.remove_schedule(schedule_id)

    # データベースから削除
    db.delete(schedule)
    db.commit()

    return {"message": "スケジュールが削除されました"}


async def _send_report_task(
    user: User, report_type: str, recipient_type: str, project_id: Optional[int], to_email: str, db: Session
):
    """
    バックグラウンドでレポートを生成・送信するタスク
    """
    try:
        # レポートデータを生成
        report_data = None

        if recipient_type == ReportRecipientType.PERSONAL:
            report_data = report_generator.generate_personal_report(user=user, db=db, report_type=report_type)
        elif recipient_type == ReportRecipientType.PROJECT and project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                report_data = report_generator.generate_project_report(project=project, db=db, report_type=report_type)
        elif recipient_type == ReportRecipientType.TEAM:
            report_data = report_generator.generate_team_report(db=db, report_type=report_type)

        if not report_data:
            logger.error("Failed to generate report data")
            return

        # レポートを送信
        success = report_email_service.send_report(to_email=to_email, report_type=report_type, report_data=report_data)

        if success:
            logger.info(f"Report sent successfully to {to_email}")
        else:
            logger.error(f"Failed to send report to {to_email}")

    except Exception as e:
        logger.error(f"Error in report task: {str(e)}", exc_info=True)
