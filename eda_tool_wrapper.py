from dataclasses import dataclass
from enum import Enum, auto

@dataclass
class ToolStatus(Enum):
    """ Displays the Tool's Current Status """
    NOT_RUN = auto()
    RUNNING = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR   = auto()

