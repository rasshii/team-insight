"""
レポートスケジューラーサービス

APSchedulerを使用して定期的にレポート配信を実行します。
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.report_schedule import ReportSchedule, ReportDeliveryHistory
from app.services.report_generator import report_generator
from app.services.report_email import report_email_service

logger = logging.getLogger(__name__)


class ReportSchedulerService:
    """レポートスケジューラーサービス"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_prefix = "report_schedule_"

    def start(self):
        """スケジューラーを開始"""
        try:
            # 既存のスケジュールをロード
            self._load_schedules()

            # 毎時0分にスケジュールをチェック
            self.scheduler.add_job(self._check_schedules, CronTrigger(minute=0), id="check_schedules", replace_existing=True)

            self.scheduler.start()
            logger.info("Report scheduler started")
        except Exception as e:
            logger.error(f"Failed to start report scheduler: {str(e)}")

    def stop(self):
        """スケジューラーを停止"""
        try:
            self.scheduler.shutdown()
            logger.info("Report scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop report scheduler: {str(e)}")

    def add_schedule(self, schedule: ReportSchedule):
        """スケジュールを追加"""
        if not schedule.enabled or not schedule.send_time:
            return

        job_id = f"{self.job_prefix}{schedule.id}"

        # CRONトリガーを作成
        trigger = CronTrigger(hour=schedule.send_time.hour, minute=schedule.send_time.minute)

        # ジョブを追加
        self.scheduler.add_job(self._send_scheduled_report, trigger, args=[schedule.id], id=job_id, replace_existing=True)

        logger.info(f"Added schedule job: {job_id}")

    def remove_schedule(self, schedule_id: int):
        """スケジュールを削除"""
        job_id = f"{self.job_prefix}{schedule_id}"

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed schedule job: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {str(e)}")

    def update_schedule(self, schedule: ReportSchedule):
        """スケジュールを更新"""
        self.remove_schedule(schedule.id)

        if schedule.enabled:
            self.add_schedule(schedule)

    def _load_schedules(self):
        """データベースから全スケジュールをロード"""
        db = SessionLocal()
        try:
            schedules = (
                db.query(ReportSchedule).filter(ReportSchedule.enabled == True, ReportSchedule.send_time.isnot(None)).all()
            )

            for schedule in schedules:
                self.add_schedule(schedule)

            logger.info(f"Loaded {len(schedules)} report schedules")

        except Exception as e:
            logger.error(f"Failed to load schedules: {str(e)}")
        finally:
            db.close()

    def _check_schedules(self):
        """定期的にスケジュールをチェック（毎時実行）"""
        db = SessionLocal()
        try:
            now = datetime.now()
            current_hour = now.hour

            # 今の時間に実行すべきスケジュールを検索
            schedules = (
                db.query(ReportSchedule).filter(ReportSchedule.enabled == True, ReportSchedule.send_time.isnot(None)).all()
            )

            for schedule in schedules:
                # 実行時刻をチェック
                if schedule.send_time.hour == current_hour and schedule.send_time.minute == 0:
                    # 今日既に送信済みかチェック
                    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    if not schedule.last_sent_at or schedule.last_sent_at < today_start:
                        self._send_scheduled_report(schedule.id)

        except Exception as e:
            logger.error(f"Failed to check schedules: {str(e)}")
        finally:
            db.close()

    def _send_scheduled_report(self, schedule_id: int):
        """スケジュールされたレポートを送信"""
        db = SessionLocal()
        try:
            # スケジュールを取得
            schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()

            if not schedule or not schedule.enabled:
                return

            # ユーザーを取得
            user = schedule.user
            if not user or not user.email:
                logger.warning(f"No email for user {user.id if user else 'None'}")
                return

            # レポートタイプに応じて適切な間隔をチェック
            should_send = self._should_send_report(schedule)
            if not should_send:
                return

            # レポートデータを生成
            report_data = None

            if schedule.recipient_type == "personal":
                report_data = report_generator.generate_personal_report(user=user, db=db, report_type=schedule.report_type)
            elif schedule.recipient_type == "project" and schedule.project:
                report_data = report_generator.generate_project_report(
                    project=schedule.project, db=db, report_type=schedule.report_type
                )
            elif schedule.recipient_type == "team":
                report_data = report_generator.generate_team_report(db=db, report_type=schedule.report_type)

            if not report_data:
                logger.error(f"Failed to generate report for schedule {schedule_id}")
                return

            # レポートを送信
            success = report_email_service.send_report(
                to_email=user.email, report_type=schedule.report_type, report_data=report_data
            )

            # 配信履歴を記録
            history = ReportDeliveryHistory(
                schedule_id=schedule_id,
                user_id=user.id,
                report_type=schedule.report_type,
                recipient_type=schedule.recipient_type,
                project_id=schedule.project_id,
                email=user.email,
                status="success" if success else "failed",
                error_message=None if success else "Failed to send email",
                sent_at=datetime.now(),
            )
            db.add(history)

            # スケジュールの最終送信時刻を更新
            schedule.last_sent_at = datetime.now()
            schedule.next_send_at = self._calculate_next_send_time(schedule)

            db.commit()

            if success:
                logger.info(f"Report sent successfully for schedule {schedule_id}")
            else:
                logger.error(f"Failed to send report for schedule {schedule_id}")

        except Exception as e:
            logger.error(f"Error in scheduled report task: {str(e)}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    def _should_send_report(self, schedule: ReportSchedule) -> bool:
        """レポートを送信すべきかチェック"""
        if not schedule.last_sent_at:
            return True

        now = datetime.now()
        time_since_last = now - schedule.last_sent_at

        if schedule.report_type == "daily":
            # 24時間以上経過していれば送信
            return time_since_last >= timedelta(days=1)
        elif schedule.report_type == "weekly":
            # 7日以上経過していれば送信
            return time_since_last >= timedelta(days=7)
        elif schedule.report_type == "monthly":
            # 30日以上経過していれば送信
            return time_since_last >= timedelta(days=30)

        return False

    def _calculate_next_send_time(self, schedule: ReportSchedule) -> datetime:
        """次回送信時刻を計算"""
        now = datetime.now()

        if schedule.report_type == "daily":
            next_time = now + timedelta(days=1)
        elif schedule.report_type == "weekly":
            next_time = now + timedelta(days=7)
        elif schedule.report_type == "monthly":
            next_time = now + timedelta(days=30)
        else:
            next_time = now + timedelta(days=1)

        # 指定された時刻に設定
        if schedule.send_time:
            next_time = next_time.replace(
                hour=schedule.send_time.hour, minute=schedule.send_time.minute, second=0, microsecond=0
            )

        return next_time


# シングルトンインスタンス
report_scheduler = ReportSchedulerService()
