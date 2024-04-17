from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

# Вынести в utils


class Status(Enum):
    AUDIO_RECEIVED = "Audio received"
    TEXT_RECEIVED = " Text received"
    AUDIO_DIARIZATION_PROCESSING = " Diarazing for audio"
    DIARIZATION_COMPLETED = "Diarization complited"
    LLM_ANALYSIS_PROCESSING = " Analizing of LLM"
    REPORT_COMPLETED = "Report complited"
    COMPLETED = "Task complited"
    ERROR = "Error"


class Task(BaseModel):
    status: Status
    audio_path: Optional[str] = None
    text_path: Optional[str] = None
    report_path: Optional[str] = None


class Audio(BaseModel):
    audio_path: str = "/audio/audio.wav"


class Text(BaseModel):
    text_path: str = "/text/file.txt"
