from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from pathlib import Path
from abc import ABC, abstractmethod
import logging
import shutil
import time
import subprocess

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

class EDAToolBase(ABC):
    """Implements all shared infrastructure"""

    def __init__(self, work_dir : str|Path, *, timeout : int = 3600):
        """" Constructor for EDAToolBase """
        # Resolve work_dir to an abs Path
        self.work_dir = Path(work_dir).resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Set self.timeout for subprocess calls
        self.timeout = timeout
        # Initialise self._results as an empty list[RunResult]
        self._results = []
        # Configure a logger with both a StreamHandler (INFO level) and FileHandler (Debug level)
        self._logger = logging.getLogger(__name__)  
        self._logger.setLevel(logging.DEBUG)

        # Make StreamHandler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        self._logger.addHandler(ch)

        # Make FileHandler
        fh = logging.FileHandler(self.work_dir / f"{self._tool_name()}.log")
        fh.setLevel(logging.DEBUG)
        self._logger.addHandler(fh)
    
    @abstractmethod
    def _executable(self) -> str: ...  

    @abstractmethod
    def _tool_name(self) -> str: ...

    def _run(self, tcl_script: str | Path, extra_args: list[str] | None = None) -> RunResult:
        """ Method to run EDA Tool Wrapper """
        # 1.	Resolve tcl_script to a Path and raise FileNotFoundError if it does not exist
        # 2.	Call shutil.which(self._executable()) and raise EnvironmentError if the binary is not in PATH
        # 3.	Build the command list: [executable, '-f', str(tcl_script)] plus any extra_args
        # 4.	Record the start time with time.perf_counter()
        # 5.	Log the start of the invocation at INFO level
        # 6.	Call subprocess.run() with capture_output=True, text=True, cwd=self.work_dir, timeout=self.timeout
        # 7.	Catch subprocess.TimeoutExpired — log an error and construct a RunResult with returncode=-1
        # 8.	Catch any other exception and re-raise as a RuntimeError with context
        # 9.	Compute elapsed time, construct and append a RunResult to self._results
        # 10.	Log the result summary at INFO or ERROR level based on RunResult.ok
        # 11.	Return the RunResult

        tcl_script_p = Path(tcl_script).resolve()
        if not tcl_script_p.exists():
            raise FileNotFoundError(f"Tcl Script does not exist {tcl_script_p}")

        if not shutil.which(self._executable()):
            raise EnvironmentError(f"The executable is not in the PATH: {self._executable()}")

        cmd = [self._executable(), '-f', str(tcl_script)]
        if extra_args:
            cmd += extra_args
        
        start_time = time.perf_counter()
        self._logger.info(f"Starting {self._tool_name()} running {cmd}")

        # Subprocess run
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.work_dir,
                timeout=self.timeout
            )

        # Excpetion for Timeout
        except subprocess.TimeoutExpired:
            self._logger.error("Timeout Expired")
            result = RunResult(
                tool=self._tool_name(),
                command=" ".join(cmd),
                returncode=-1,
                stdout="",
                stderr="",
                elapsed=time.perf_counter()-start_time,
                log_file=self.work_dir / f"{self._tool_name()}.log"
            )
            return result

        # General Exception
        except Exception as e:
            raise RuntimeError(f"Non-Timeout Error: {self._tool_name()} caused error {e}") from e

        # Add Run Result to self._results
        elapsed_time = time.perf_counter() - start_time
        new_result = RunResult(
            tool=self._tool_name(),
            command=" ".join(cmd),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            elapsed=elapsed_time,
            log_file=self.work_dir / f"{self._tool_name()}.log"
        )
        self._results.append(new_result)

        # Log Result Summary at INFO or ERROR
        if new_result.ok:
            self._logger.info(str(new_result))
        else:
            self._logger.error(str(new_result))

        return new_result

