from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Task(BaseModel):
    task_id: int
    status: str
    creation_date: Optional[datetime] = None
    audio_id: int
    text_id: int
    report_id: int
    error_info: Optional[str] = None


class Audio(BaseModel):
    audio_id: int
    audio_path: str
    error_info: Optional[str] = None


class DiaraziedText(BaseModel):
    text_id: int
    text_path: str
    task_id: int
    error_info: Optional[str] = None


class Report(BaseModel):
    report_id: int
    report_path: str
    task_id: int
    error_info: Optional[str] = None
