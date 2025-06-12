"""
Import all models here to ensure they are registered with SQLAlchemy
"""

# Import the Base class
from app.db.base_class import Base  # noqa

# Import all models here
from app.models.user import User  # noqa
from app.models.auth import OAuthState, OAuthToken  # noqa
