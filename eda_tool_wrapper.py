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

@dataclass
class SynthesisReport():
    """ Dataclass for Synthesis Report """
    timing_slack_ns: Optional[float] = None # worst negative slack (ns)
    total_area : Optional[float] = None # total cell area
    cell_count : Optional[int] = None # number of cells in the synthesised design
    dynamic_power_mw : Optional[float] = None # total dynamic power in mW
    leakage_power_uw : Optional[float] = None# total leakage power in uW
    raw_timing : str = "" # Text Report for Debugging
    raw_area : str = "" # Text Report for Debugging
    raw_power : str = "" # Text Report for Debugging    

    def summary(self):
        return f"""
                Slack: {self.timing_slack_ns} ns
                Area:  {self.total_area}
                Cell Count: {self.cell_count}
                Dynamic Power: {self.dynamic_power_mw} mW
                Leakage Power: {self.leakage_power_uw} uW
                """

@dataclass
class PowerReport():
    """ Dataclass for Power Report """
    total_power_mw : Optional[float] = None # total power in mW
    dynamic_power_mw : Optional[float] = None # dynamic power in mW
    leakage_power_mw: Optional[float] = None # leakage power in mW
    top_consumers : list[tuple[str, float]] = field(default_factory=list) # (module_name, power_mw) pairs
    raw : str = "" # Full Raw Report Rext

    def summary(self):
        result = ""
        for table in self.top_consumers[:10]:
            result += str(table[0]) + ": " + str(table[1]) + "mW\n"
        return result




