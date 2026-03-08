# Agent Development Guide

This document provides guidelines for AI coding agents working on the DCC-EX Throttle TUI project.

## Project Overview

A Python Terminal User Interface (TUI) application for controlling model trains through a DCC-EX Command Station. Built with [Textual](https://textual.textualize.io/) framework for the UI and asyncio for TCP socket communication.

**Tech Stack:**
- Python 3.11+ (or 3.9+ with `tomli`)
- Textual (TUI framework)
- asyncio (async networking)
- TOML configuration (tomllib/tomli)

## Build & Run Commands

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install with Python 3.9-3.10 (requires tomli)
pip install textual tomli
```

### Running the Application
```bash
# Run with default settings
python -m dccex_throttle

# Connect to specific host
python -m dccex_throttle --host 192.168.1.100 --port 2560

# Enable debug logging
python -m dccex_throttle --debug --log-file throttle.log

# Use custom config
python -m dccex_throttle --config /path/to/config.toml
```

### Testing
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=dccex_throttle --cov-report=html

# Run specific test file
python -m pytest tests/test_models.py

# Run specific test function
python -m pytest tests/test_models.py::TestLocomotive::test_set_speed

# Run tests matching pattern
python -m pytest -k "test_speed"

# Run async tests only
python -m pytest -m asyncio

# Verbose output
python -m pytest -v

# Show local variables on failure
python -m pytest -l

# Stop on first failure
python -m pytest -x
```

### Linting & Formatting
```bash
# Format code with Black (recommended)
black dccex_throttle/

# Check PEP 8 compliance with flake8
flake8 dccex_throttle/ --max-line-length=79

# Or use ruff (faster alternative)
ruff check .
ruff format .

# Type checking with mypy
mypy dccex_throttle/
```

## Code Architecture

```
dccex_throttle/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point (argparse)
├── config.py            # TOML configuration management
├── models.py            # Data classes (Locomotive, ThrottleState, Direction)
├── protocol.py          # DCC-EX TCP protocol (asyncio)
├── ui.py                # Textual TUI application
├── utils.py             # Utility functions
└── config.toml.example  # Example config file
```

**Key Components:**
- `DCCEXProtocol`: Async TCP client for DCC-EX Command Station communication
- `DCCEXThrottleApp`: Main Textual app with UI layout and event handling
- `Locomotive`: Dataclass for loco state (address, speed, direction, functions)
- `ThrottleState`: Global application state management
- `Config`: TOML-based configuration with defaults

## Code Style Guidelines

### General Python Style
- **PEP 8 Standards**: Follow PEP 8 style guide strictly
  - 79 characters per line maximum
  - 4 spaces for indentation (no tabs)
  - Two blank lines between top-level functions/classes
  - One blank line between methods
- **Black Formatting**: Code should be formatted with Black (or Black-compatible)
  - Use double quotes for strings
  - Trailing commas in multi-line structures
  - Consistent spacing around operators
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use docstrings for all functions, classes, and modules
- **Python version**: Target 3.11+, but maintain 3.9+ compatibility

### Import Organization
```python
# Standard library imports first
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Third-party imports second
from textual.app import App
from textual.widgets import Button

# Local imports last
from .config import Config
from .models import Locomotive, Direction
```

### Naming Conventions
- **Classes**: PascalCase (`DCCEXProtocol`, `ThrottleState`)
- **Functions/methods**: snake_case (`send_throttle`, `acquire_loco`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_CONFIG`, `MAX_SPEED`)
- **Private methods**: Leading underscore (`_receive_loop`, `_handle_response`)
- **Async methods**: Prefix with `async def`, use `await` for async calls

### Type Hints
```python
# Function signatures with type hints
def validate_loco_address(address: str) -> Optional[int]:
    """Validate and parse locomotive address."""
    ...

async def send_throttle(
    self, loco_address: int, speed: int, direction: Direction
) -> bool:
    """Send throttle command."""
    ...

# Type aliases for clarity
from typing import Dict, Any
ConfigDict = Dict[str, Any]
```

### Dataclasses
Use `@dataclass` decorator for data models:
```python
from dataclasses import dataclass, field

@dataclass
class Locomotive:
    """Represents a locomotive and its current state."""
    address: int
    name: str = ""
    speed: int = 0
    direction: Direction = Direction.FORWARD
    functions: Dict[int, bool] = field(default_factory=dict)
```

### Async/Await Patterns
```python
# Async functions for I/O operations
async def connect(self) -> bool:
    """Connect to DCC-EX Command Station."""
    try:
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=self.timeout
        )
        return True
    except asyncio.TimeoutError:
        logger.error(f"Connection timeout to {self.host}:{self.port}")
        return False
```

### Error Handling
```python
# Specific exceptions with logging
try:
    loaded_config = load_toml(self.config_path)
    self._merge_config(loaded_config)
except Exception as e:
    logger.error(f"Error loading config: {e}")
    # Fallback to defaults
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debug information")
logger.info("Connection established")
logger.warning("Invalid address format")
logger.error("Connection failed")
```

### Textual UI Patterns
```python
# Widget IDs use kebab-case
yield Button("Acquire", id="acquire-btn", variant="primary")

# CSS classes use kebab-case
yield Button("F0", id="fn-0", classes="function-button")

# Query widgets by ID/type
button = self.query_one("#acquire-btn", Button)
buttons = self.query(".function-button")

# Event handlers with @on decorator
@on(Switch.Changed, "#power-switch")
async def on_power_switch_changed(self, event: Switch.Changed) -> None:
    """Handle power switch toggle."""
    await self.toggle_power_internal(event.value)
```

## DCC-EX Protocol Notes

The application implements the DCC-EX native protocol over TCP (port 2560):

**Commands Sent:**
- `<t LOCO SPEED DIR>` - Throttle control
- `<F LOCO FUNCTION STATE>` - Function control
- `<1>` / `<0>` - Track power on/off
- `<!>` - Emergency stop

**Responses Parsed:**
- `<p0>` / `<p1>` - Track power state
- `<l LOCO SPEEDBYTE DIR FUNCTIONS>` - Locomotive state broadcast
- `<iDCC-EX ...>` - Command station info

**Important**: The throttle listens for broadcast messages to support multi-throttle operation.

## Configuration

Configuration uses TOML format with three sections:
- `[connection]` - Host, port, timeout settings
- `[ui]` - Theme, debug console, display settings
- `[throttle]` - Speed step, max speed, defaults

Config file location: `~/.config/dccex_throttle/config.toml`

## Testing Guidelines

**Test Structure:**
- All tests in `tests/` directory
- Test files named `test_*.py`
- Use pytest framework with pytest-asyncio for async tests
- Mock DCC-EX server available in `tests/mock_server.py`

**Running Tests:**
- `python -m pytest` - Run all tests
- `python -m pytest tests/test_models.py` - Run single test file
- `python -m pytest -k "test_speed"` - Run tests matching pattern
- `python -m pytest --cov` - Run with coverage report

**Writing Tests:**
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use `@pytest.mark.asyncio` for async tests
- Use `mock_server` fixture for protocol testing
- Test both sync and async code
- Mock DCC-EX Command Station responses
- Test edge cases (invalid addresses, disconnections, etc.)

**Mock DCC-EX Server:**
```python
@pytest.mark.asyncio
async def test_example(mock_server):
    protocol = DCCEXProtocol(host=mock_server.host, port=mock_server.port)
    await protocol.connect()
    await protocol.send_power_on()
    # Assert behavior
```

## Common Tasks

### Adding a New DCC-EX Command
1. Add method to `DCCEXProtocol` class in `protocol.py`
2. Update `_handle_response()` to parse responses
3. Add UI handler in `ui.py` if user-facing
4. Update docstrings and type hints

### Adding a New UI Widget
1. Add widget in `compose()` method in `ui.py`
2. Define CSS styling in `CSS` class variable
3. Add event handler method (`on_*` or `@on` decorator)
4. Update keyboard bindings in `BINDINGS` if needed

### Modifying Configuration
1. Update `DEFAULT_CONFIG` in `config.py`
2. Update `config.toml.example`
3. Add getter method if new section
4. Update README.md configuration section

## Git Workflow

**Commit Messages:**
- Use imperative mood ("Add feature" not "Added feature")
- Keep first line under 50 characters
- Reference related issues if applicable

**Example commits:**
```
Add turnout control feature
Fix speed sync in multi-throttle mode
Update README with new keyboard shortcuts
Refactor protocol parsing for clarity
```

## Related Resources

- [DCC-EX Command Reference](https://dcc-ex.com/reference/software/command-reference.html)
- [Textual Documentation](https://textual.textualize.io/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

## Notes for Agents

- **Code Style**: Strictly follow PEP 8 and Black formatting guidelines
- **License**: GPLv3 - ensure all new code is GPL-compatible
- **Python compatibility**: Maintain 3.9+ support (use tomli for TOML parsing on <3.11)
- **Dependencies**: Minimize external dependencies; prefer stdlib when possible
- **Performance**: Use async/await for all I/O; avoid blocking operations
- **UI responsiveness**: Keep UI operations fast; use background tasks for network calls
- **Multi-throttle support**: Always consider broadcast message handling when modifying loco state
- **Line length**: Never exceed 79 characters per line (PEP 8 compliance required)
