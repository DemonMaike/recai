from enum import Enum
import os
import uuid

# Вынести ли эти утилсы в общие, так как статус будет общий для всех
# приложений. Хотя если подумать, то только статус. остальное нужно на
# шлюзе, если он ответсвенный за прием файлов. ⏪

description_message = {"task_id": None, "info": None}
final_message = {"status": None, "message": description_message}


class Status(Enum):
    AUDIO_RECEIVED = "Audio received"
    TEXT_RECEIVED = " Text received"
    AUDIO_DIARIZATION_PROCESSING = " Diarazing for audio"
    DIARIZATION_COMPLETED = "Diarization complited"
    LLM_ANALYSIS_PROCESSING = " Analizing of LLM"
    REPORT_COMPLETED = "Report complited"
    COMPLETED = "Task complited"
    ERROR = "Error"


class File:
    """Work with file in this app."""

    CHUNK_SIZE = 5 * 1024 * 1024
    AUDIO_FORMATS = ('.wav', '.mp3', '.aac', '.alac', '.flac', '.m4a', '.amr')
    TEXT_FORMATS = ('.txt', '.md')  # doc, pdf ? ⏪

    @classmethod
    def get_uuid_name(cls, filename: str) -> str:
        """ Get uuid name of file. """
        filename, extantion = os.path.splitext(filename)

        return f"{uuid.uuid4()}{extantion}"

    @classmethod
    def is_audio(cls, filename):
        """Сhecking that file is audio"""
        filename, extantion = os.path.splitext(filename)
        if extantion in cls.AUDIO_FORMATS:
            return True
        return False

    @classmethod
    def is_text(cls, filename):
        """Сhecking that file is text"""
        filename, extantion = os.path.splitext(filename)
        if extantion in cls.TEXT_FORMATS:
            return True
        return False
