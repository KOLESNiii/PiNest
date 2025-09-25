import time
import json
from enum import Enum
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "origin": self.origin,
            "level": self.level.value,
            "message": self.message,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def show(self, logging_level: LogLevel = LogLevel.DEBUG) -> bool:
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
        }
        return level_order[self.level] >= level_order[logging_level]
