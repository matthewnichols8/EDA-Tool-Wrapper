from dataclasses import dataclass
from enum import Enum, auto

@dataclass
class ToolStatus(Enum):
    """ Displays the Tool's Current Status """
    NOT_RUN = auto() # tool not running
    RUNNING = auto() # subprocess is active
    SUCCESS = auto() # returncode == 0, no warnings
    WARNING = auto() # returncode == 0, stdout contains warning
    ERROR   = auto() # returncode != 0



