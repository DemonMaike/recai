from datetime import datetime
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users.models import ID
from sqlalchemy import TIMESTAMP, UUID, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base, relationship


Base: DeclarativeMeta = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    # UUID ForeignKey, если ваш id пользователя — UUID
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'))
    user = relationship("User", back_populates="tasks")
    status = Column(String)
    creation_date = Column(TIMESTAMP, default=datetime.utcnow)
    audio_path = Column(String)
    text_path = Column(String)
    report_path = Column(String)


class User(SQLAlchemyBaseUserTableUUID, Base):
    id: ID
    email: str
    hashed_password: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    tasks = relationship("Task", back_populates="user")
