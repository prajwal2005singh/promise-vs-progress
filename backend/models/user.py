from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime
)

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    phone = Column(String, unique=True, nullable=False)

    password_hash = Column(String, nullable=True)

    google_id = Column(String, unique=True, nullable=True)

    role = Column(String, nullable=False, default="CITIZEN")

    is_verified = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    last_login = Column(DateTime, nullable=True)

    status = Column(String, nullable=False, default="ACTIVE")