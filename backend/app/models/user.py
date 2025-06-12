from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    backlog_id = Column(Integer, unique=True, index=True, nullable=True)
    user_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)

    oauth_tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
