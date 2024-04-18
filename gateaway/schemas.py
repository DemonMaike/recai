from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from .utils import Status


class Task(BaseModel):
    status: Status
    audio_path: Optional[str] = None
    text_path: Optional[str] = None
    report_path: Optional[str] = None
