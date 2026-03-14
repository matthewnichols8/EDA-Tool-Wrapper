from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from pathlib import Path

class ToolStatus(Enum):
    """ Displays the Tool's Current Status """
    NOT_RUN = auto() # tool not running
    RUNNING = auto() # subprocess is active
    SUCCESS = auto() # returncode == 0, no warnings
    WARNING = auto() # returncode == 0, stdout contains warning
    ERROR   = auto() # returncode != 0

@dataclass
class RunResult():
    """ Displays the Run Result of the Tool """
    tool : str
    command : str
    returncode : int
    stdout : str
    stderr : str
    elapsed : float # seconds
    log_file : Optional[Path]
    status : ToolStatus = field(init=False, default=ToolStatus.NOT_RUN)

    @property
    def ok(self) -> bool:
        return self.status in {ToolStatus.SUCCESS, ToolStatus.WARNING}
        
    def __str__(self):
        return f"{self.tool}: {self.command} returned {self.returncode} with stdout {self.stdout} and stderr {self.stderr} for {self.elapsed} seconds. LogPath: {self.log_file}"

    def __post_init__(self):
        # status = None
        if self.returncode == 0 and "warning" in self.stdout:
            self.status = ToolStatus.WARNING
        elif self.returncode == 0 and "warning" not in self.stdout:
            self.status = ToolStatus.SUCCESS
        else:
            self.status = ToolStatus.ERROR




