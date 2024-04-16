from datetime import datetime
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class File(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    file_path = Column(String)


class Audio(File):
    __tablename__ = "audio"


class DiaraziedText(File):
    __tablename__ = "diarazied_texts"


class Report(File):
    __tablename__ = "reports"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    status = Column(String)
    creation_date = Column(TIMESTAMP, default=datetime.utcnow)
    audio_id = Column(Integer, ForeignKey("audio.id"))
    text_id = Column(Integer, ForeignKey("diarazied_texts.id"))
    report_id = Column(Integer, ForeignKey("reports.id"))
