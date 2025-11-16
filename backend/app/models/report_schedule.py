"""
レポート配信スケジュールモデル
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from app.db.base_class import BaseModel


class ReportSchedule(BaseModel):
    """レポート配信スケジュール"""

    __tablename__ = "report_schedules"
    __table_args__ = {"schema": "team_insight"}

    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)
    report_type = Column(String, nullable=False)  # daily, weekly, monthly
    recipient_type = Column(String, nullable=False)  # personal, project, team
    project_id = Column(Integer, ForeignKey("team_insight.projects.id"), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    send_time = Column(Time, nullable=True)  # 送信時刻（HH:MM）
    last_sent_at = Column(DateTime, nullable=True)
    next_send_at = Column(DateTime, nullable=True)

    # リレーション
    user = relationship("User", back_populates="report_schedules")
    project = relationship("Project", back_populates="report_schedules")
    delivery_history = relationship("ReportDeliveryHistory", back_populates="schedule", cascade="all, delete-orphan")


class ReportDeliveryHistory(BaseModel):
    """レポート配信履歴"""

    __tablename__ = "report_delivery_history"
    __table_args__ = {"schema": "team_insight"}

    schedule_id = Column(Integer, ForeignKey("team_insight.report_schedules.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)
    report_type = Column(String, nullable=False)
    recipient_type = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("team_insight.projects.id"), nullable=True)
    email = Column(String, nullable=False)
    status = Column(String, nullable=False)  # success, failed
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=False)

    # リレーション
    schedule = relationship("ReportSchedule", back_populates="delivery_history")
    user = relationship("User")
    project = relationship("Project")
