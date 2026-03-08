"""
DCC-EX Throttle TUI - Python Terminal User Interface for DCC-EX Command Station

A modern terminal-based throttle application for controlling model trains
through a DCC-EX Command Station over TCP socket connection.
"""

__version__ = "1.0.0"
__author__ = "DCC-EX Throttle TUI Contributors"
__license__ = "GPLv3"

from .config import Config
from .models import Locomotive, ThrottleState, Direction
from .protocol import DCCEXProtocol
from .ui import DCCEXThrottleApp

__all__ = [
    "Config",
    "Locomotive",
    "ThrottleState",
    "Direction",
    "DCCEXProtocol",
    "DCCEXThrottleApp",
]
