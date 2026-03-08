"""
Pytest configuration and shared fixtures for DCC-EX Throttle TUI tests.
"""
import asyncio
import pytest
from pathlib import Path
from typing import Optional


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_config_dict():
    """Return a sample configuration dictionary."""
    return {
        'connection': {
            'host': 'localhost',
            'port': 2560,
            'auto_connect': False,
            'reconnect_delay': 5,
            'timeout': 10,
        },
        'ui': {
            'theme': 'dark',
            'show_debug_console': True,
            'max_log_lines': 100,
        },
        'throttle': {
            'default_loco_address': 3,
            'speed_step': 1,
            'max_speed': 126,
        }
    }


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
