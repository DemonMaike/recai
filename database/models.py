from datetime import datetime
from sqlalchemy import TIMESTAMP, Column, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    status = Column(String)
    creation_date = Column(TIMESTAMP, default=datetime.utcnow)
    audio_path = Column(String)
    text_path = Column(String)
    report_path = Column(String)
