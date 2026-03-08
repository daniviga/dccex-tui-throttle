"""
Utility functions for DCC-EX Throttle TUI application.
"""
import logging
from datetime import datetime
from typing import Optional


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """Setup logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if log_file:
        logging.basicConfig(
            level=level,
            format=log_format,
            filename=log_file,
            filemode='a'
        )
    else:
        logging.basicConfig(
            level=level,
            format=log_format
        )


def get_timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def validate_loco_address(address: str) -> Optional[int]:
    """
    Validate and parse locomotive address.

    Returns:
        int: Valid address (1-10239) or None if invalid
    """
    try:
        addr = int(address)
        if 1 <= addr <= 10239:
            return addr
        return None
    except (ValueError, TypeError):
        return None


def validate_speed(speed: str) -> Optional[int]:
    """
    Validate and parse speed value.

    Returns:
        int: Valid speed (0-126) or None if invalid
    """
    try:
        spd = int(speed)
        if 0 <= spd <= 126:
            return spd
        return None
    except (ValueError, TypeError):
        return None


def validate_function_number(fn_num: str) -> Optional[int]:
    """
    Validate and parse function number.

    Returns:
        int: Valid function number (0-31) or None if invalid
    """
    try:
        fn = int(fn_num)
        if 0 <= fn <= 31:
            return fn
        return None
    except (ValueError, TypeError):
        return None


def parse_response(response: str) -> tuple[str, list[str]]:
    """
    Parse DCC-EX response.

    Returns:
        tuple: (command_type, parameters)

    Example:
        "<p1>" -> ("p", ["1"])
        "<l 3 173 1 0>" -> ("l", ["3", "173", "1", "0"])
    """
    # Remove < and > brackets
    response = response.strip()
    if response.startswith('<') and response.endswith('>'):
        response = response[1:-1]

    # Split into parts
    parts = response.split()
    if not parts:
        return ("", [])

    command_type = parts[0]
    parameters = parts[1:] if len(parts) > 1 else []

    return (command_type, parameters)


def format_command(cmd: str) -> str:
    """
    Format command for DCC-EX (add brackets if not present).

    Args:
        cmd: Command string (with or without < > brackets)

    Returns:
        str: Properly formatted command with <> brackets
    """
    cmd = cmd.strip()
    if not cmd:
        return ""

    # Remove existing brackets
    if cmd.startswith('<'):
        cmd = cmd[1:]
    if cmd.endswith('>'):
        cmd = cmd[:-1]

    # Add brackets
    return f"<{cmd}>"
