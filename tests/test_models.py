"""
Tests for dccex_throttle.models module.
"""
import pytest
from dccex_throttle.models import (
    Direction,
    Locomotive,
    ThrottleState,
    CommandLogEntry
)


class TestDirection:
    """Tests for Direction enum."""

    def test_direction_values(self):
        """Test Direction enum values match DCC-EX protocol."""
        assert Direction.REVERSE == 0
        assert Direction.FORWARD == 1


class TestLocomotive:
    """Tests for Locomotive dataclass."""

    def test_locomotive_creation(self):
        """Test creating a locomotive with defaults."""
        loco = Locomotive(address=3)
        assert loco.address == 3
        assert loco.name == ""
        assert loco.speed == 0
        assert loco.direction == Direction.FORWARD
        assert len(loco.functions) == 32
        assert all(not state for state in loco.functions.values())

    def test_locomotive_with_name(self):
        """Test creating a locomotive with a name."""
        loco = Locomotive(address=123, name="Big Boy")
        assert loco.address == 123
        assert loco.name == "Big Boy"

    def test_set_speed(self):
        """Test setting locomotive speed."""
        loco = Locomotive(address=3)
        loco.set_speed(50)
        assert loco.speed == 50

    def test_set_speed_clamps_to_max(self):
        """Test speed is clamped to maximum."""
        loco = Locomotive(address=3)
        loco.set_speed(200)
        assert loco.speed == 126

    def test_set_speed_clamps_to_min(self):
        """Test speed is clamped to minimum."""
        loco = Locomotive(address=3)
        loco.set_speed(-10)
        assert loco.speed == 0

    def test_set_direction(self):
        """Test setting locomotive direction."""
        loco = Locomotive(address=3)
        loco.set_direction(Direction.REVERSE)
        assert loco.direction == Direction.REVERSE

    def test_toggle_direction(self):
        """Test toggling locomotive direction."""
        loco = Locomotive(address=3)
        assert loco.direction == Direction.FORWARD
        loco.toggle_direction()
        assert loco.direction == Direction.REVERSE
        loco.toggle_direction()
        assert loco.direction == Direction.FORWARD

    def test_set_function(self):
        """Test setting a function state."""
        loco = Locomotive(address=3)
        loco.set_function(0, True)
        assert loco.functions[0] is True
        loco.set_function(0, False)
        assert loco.functions[0] is False

    def test_set_function_out_of_range(self):
        """Test setting function with invalid number does nothing."""
        loco = Locomotive(address=3)
        loco.set_function(32, True)  # Invalid
        loco.set_function(-1, True)  # Invalid
        # Should not raise exception

    def test_toggle_function(self):
        """Test toggling a function."""
        loco = Locomotive(address=3)
        assert loco.functions[5] is False
        loco.toggle_function(5)
        assert loco.functions[5] is True
        loco.toggle_function(5)
        assert loco.functions[5] is False

    def test_get_function(self):
        """Test getting function state."""
        loco = Locomotive(address=3)
        loco.set_function(10, True)
        assert loco.get_function(10) is True
        assert loco.get_function(11) is False

    def test_get_speed_byte_stop_forward(self):
        """Test speedbyte for stopped forward locomotive."""
        loco = Locomotive(address=3)
        loco.set_speed(0)
        loco.set_direction(Direction.FORWARD)
        assert loco.get_speed_byte() == 128

    def test_get_speed_byte_stop_reverse(self):
        """Test speedbyte for stopped reverse locomotive."""
        loco = Locomotive(address=3)
        loco.set_speed(0)
        loco.set_direction(Direction.REVERSE)
        assert loco.get_speed_byte() == 0

    def test_get_speed_byte_forward(self):
        """Test speedbyte for forward movement."""
        loco = Locomotive(address=3)
        loco.set_speed(50)
        loco.set_direction(Direction.FORWARD)
        # Forward: speed + 129
        assert loco.get_speed_byte() == 179

    def test_get_speed_byte_reverse(self):
        """Test speedbyte for reverse movement."""
        loco = Locomotive(address=3)
        loco.set_speed(75)
        loco.set_direction(Direction.REVERSE)
        # Reverse: speed + 1
        assert loco.get_speed_byte() == 76


class TestThrottleState:
    """Tests for ThrottleState dataclass."""

    def test_throttle_state_defaults(self):
        """Test ThrottleState default values."""
        state = ThrottleState()
        assert state.connected is False
        assert state.track_power is False
        assert state.current_loco is None
        assert state.acquired is False
        assert state.command_station_version == ""
        assert state.host == ""
        assert state.port == 2560

    def test_acquire_loco(self):
        """Test acquiring a locomotive."""
        state = ThrottleState()
        state.acquire_loco(123, "Switcher")
        assert state.acquired is True
        assert state.current_loco is not None
        assert state.current_loco.address == 123
        assert state.current_loco.name == "Switcher"

    def test_release_loco(self):
        """Test releasing a locomotive."""
        state = ThrottleState()
        state.acquire_loco(123)
        state.release_loco()
        assert state.acquired is False
        assert state.current_loco is None

    def test_has_loco(self):
        """Test checking if locomotive is acquired."""
        state = ThrottleState()
        assert state.has_loco() is False
        state.acquire_loco(123)
        assert state.has_loco() is True
        state.release_loco()
        assert state.has_loco() is False

    def test_emergency_stop(self):
        """Test emergency stop."""
        state = ThrottleState()
        state.acquire_loco(123)
        state.current_loco.set_speed(50)
        state.emergency_stop()
        assert state.current_loco.speed == 0

    def test_emergency_stop_no_loco(self):
        """Test emergency stop with no acquired loco."""
        state = ThrottleState()
        state.emergency_stop()  # Should not raise exception

    def test_get_connection_string_connected(self):
        """Test connection string when connected."""
        state = ThrottleState()
        state.connected = True
        state.host = "192.168.1.100"
        state.port = 2560
        assert state.get_connection_string() == "Connected: 192.168.1.100:2560"

    def test_get_connection_string_disconnected(self):
        """Test connection string when disconnected."""
        state = ThrottleState()
        assert state.get_connection_string() == "Disconnected"


class TestCommandLogEntry:
    """Tests for CommandLogEntry dataclass."""

    def test_command_log_entry_creation(self):
        """Test creating a command log entry."""
        entry = CommandLogEntry(direction='S', command='<t 3 50 1>')
        assert entry.direction == 'S'
        assert entry.command == '<t 3 50 1>'
        assert entry.timestamp is None

    def test_format_without_timestamp(self):
        """Test formatting without timestamp."""
        entry = CommandLogEntry(direction='R', command='<p1>')
        formatted = entry.format(show_timestamp=False)
        assert formatted == "[R] <p1>"

    def test_format_with_timestamp(self):
        """Test formatting with timestamp."""
        entry = CommandLogEntry(
            direction='S',
            command='<t 3 50 1>',
            timestamp='12:34:56.789'
        )
        formatted = entry.format(show_timestamp=True)
        assert formatted == "12:34:56.789 [S] <t 3 50 1>"
