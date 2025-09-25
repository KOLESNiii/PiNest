import time
import json
from enum import Enum

class LogLevel(Enum):
    DEBUG = "D"
    INFO = "I"
    WARNING = "W"
    ERROR = "E"

class Log:
    def __init__(self, origin: str, message: str, level: LogLevel = LogLevel.INFO):
        self.level = level
        self.message = message
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.origin = origin

    def to_dict(self) -> dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "origin": self.origin,
            "level": self.level.value,
            "message": self.message,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
