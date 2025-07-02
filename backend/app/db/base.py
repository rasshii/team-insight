"""
Import all models here to ensure they are registered with SQLAlchemy
"""

# Import the Base class
from app.db.base_class import Base  # noqa

# Import all models here
from app.models.user import User  # noqa
from app.models.auth import OAuthState, OAuthToken  # noqa
from app.models.project import Project, project_members  # noqa
from app.models.task import Task  # noqa
from app.models.sync_history import SyncHistory  # noqa
from app.models.rbac import Role, Permission, UserRole, role_permissions  # noqa
from app.models.report_schedule import ReportSchedule, ReportDeliveryHistory  # noqa
