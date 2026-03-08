"""
Data models for DCC-EX Throttle TUI application.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import IntEnum


class Direction(IntEnum):
    """Locomotive direction constants."""

    REVERSE = 0
    FORWARD = 1


@dataclass
class Locomotive:
    """Represents a locomotive and its current state."""

    address: int
    name: str = ""
    speed: int = 0
    direction: Direction = Direction.FORWARD
    functions: Dict[int, bool] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize functions dictionary if empty."""
        if not self.functions:
            self.functions = {i: False for i in range(32)}

    def set_speed(self, speed: int):
        """Set locomotive speed (0-126)."""
        self.speed = max(0, min(126, speed))

    def set_direction(self, direction: Direction):
        """Set locomotive direction."""
        self.direction = direction

    def toggle_direction(self):
        """Toggle between forward and reverse."""
        self.direction = (
            Direction.REVERSE
            if self.direction == Direction.FORWARD
            else Direction.FORWARD
        )

    def set_function(self, fn_number: int, state: bool):
        """Set function state."""
        if 0 <= fn_number <= 31:
            self.functions[fn_number] = state

    def toggle_function(self, fn_number: int):
        """Toggle function state."""
        if 0 <= fn_number <= 31:
            self.functions[fn_number] = not self.functions[fn_number]

    def get_function(self, fn_number: int) -> bool:
        """Get function state."""
        return self.functions.get(fn_number, False)

    def get_speed_byte(self) -> int:
        """Convert speed and direction to DCC-EX speed byte format."""
        if self.speed == 0:
            return 128 if self.direction == Direction.FORWARD else 0
        if self.direction == Direction.FORWARD:
            return self.speed + 129
        else:
            return self.speed + 1


@dataclass
class ThrottleState:
    """Global throttle state."""

    connected: bool = False
    track_power: bool = False
    current_loco: Optional[Locomotive] = None
    acquired: bool = False
    command_station_version: str = ""
    host: str = ""
    port: int = 2560

    def acquire_loco(self, address: int, name: str = ""):
        """Acquire a locomotive."""
        self.current_loco = Locomotive(address=address, name=name)
        self.acquired = True

    def release_loco(self):
        """Release the current locomotive."""
        self.current_loco = None
        self.acquired = False

    def has_loco(self) -> bool:
        """Check if a locomotive is acquired."""
        return self.acquired and self.current_loco is not None

    def emergency_stop(self):
        """Emergency stop - set speed to 0."""
        if self.current_loco:
            self.current_loco.set_speed(0)

    def get_connection_string(self) -> str:
        """Get connection string for display."""
        if self.connected:
            return f"Connected: {self.host}:{self.port}"
        return "Disconnected"


@dataclass
class CommandLogEntry:
    """Represents a command log entry."""

    direction: str  # 'S' for sent, 'R' for received
    command: str
    timestamp: Optional[str] = None

    def format(self, show_timestamp: bool = False) -> str:
        """Format the log entry for display."""
        if show_timestamp and self.timestamp:
            return f"{self.timestamp} [{self.direction}] {self.command}"
        return f"[{self.direction}] {self.command}"
