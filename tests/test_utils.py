"""
Tests for dccex_throttle.utils module.
"""
import pytest
from dccex_throttle.utils import (
    validate_loco_address,
    validate_speed,
    validate_function_number,
    parse_response,
    format_command,
    get_timestamp
)


class TestValidateLocoAddress:
    """Tests for validate_loco_address function."""

    def test_valid_address(self):
        """Test valid locomotive addresses."""
        assert validate_loco_address("3") == 3
        assert validate_loco_address("123") == 123
        assert validate_loco_address("10239") == 10239

    def test_address_boundaries(self):
        """Test address boundary values."""
        assert validate_loco_address("1") == 1
        assert validate_loco_address("10239") == 10239

    def test_address_below_minimum(self):
        """Test address below minimum returns None."""
        assert validate_loco_address("0") is None
        assert validate_loco_address("-1") is None

    def test_address_above_maximum(self):
        """Test address above maximum returns None."""
        assert validate_loco_address("10240") is None
        assert validate_loco_address("99999") is None

    def test_invalid_address_format(self):
        """Test invalid address format returns None."""
        assert validate_loco_address("abc") is None
        assert validate_loco_address("12.5") is None
        assert validate_loco_address("") is None


class TestValidateSpeed:
    """Tests for validate_speed function."""

    def test_valid_speed(self):
        """Test valid speed values."""
        assert validate_speed("0") == 0
        assert validate_speed("50") == 50
        assert validate_speed("126") == 126

    def test_speed_boundaries(self):
        """Test speed boundary values."""
        assert validate_speed("0") == 0
        assert validate_speed("126") == 126

    def test_speed_below_minimum(self):
        """Test speed below minimum returns None."""
        assert validate_speed("-1") is None
        assert validate_speed("-10") is None

    def test_speed_above_maximum(self):
        """Test speed above maximum returns None."""
        assert validate_speed("127") is None
        assert validate_speed("200") is None

    def test_invalid_speed_format(self):
        """Test invalid speed format returns None."""
        assert validate_speed("abc") is None
        assert validate_speed("12.5") is None
        assert validate_speed("") is None


class TestValidateFunctionNumber:
    """Tests for validate_function_number function."""

    def test_valid_function_number(self):
        """Test valid function numbers."""
        assert validate_function_number("0") == 0
        assert validate_function_number("15") == 15
        assert validate_function_number("31") == 31

    def test_function_boundaries(self):
        """Test function number boundary values."""
        assert validate_function_number("0") == 0
        assert validate_function_number("31") == 31

    def test_function_below_minimum(self):
        """Test function below minimum returns None."""
        assert validate_function_number("-1") is None

    def test_function_above_maximum(self):
        """Test function above maximum returns None."""
        assert validate_function_number("32") is None
        assert validate_function_number("100") is None

    def test_invalid_function_format(self):
        """Test invalid function format returns None."""
        assert validate_function_number("abc") is None
        assert validate_function_number("") is None


class TestParseResponse:
    """Tests for parse_response function."""

    def test_parse_simple_response(self):
        """Test parsing simple response."""
        cmd_type, params = parse_response("<p1>")
        assert cmd_type == "p"
        assert params == ["1"]

    def test_parse_complex_response(self):
        """Test parsing complex response with multiple parameters."""
        cmd_type, params = parse_response("<l 3 179 1 0>")
        assert cmd_type == "l"
        assert params == ["3", "179", "1", "0"]

    def test_parse_without_brackets(self):
        """Test parsing response without brackets."""
        cmd_type, params = parse_response("p0")
        assert cmd_type == "p"
        assert params == ["0"]

    def test_parse_info_response(self):
        """Test parsing info response."""
        cmd_type, params = parse_response(
            "<iDCC-EX V-5.0.0 / MEGA / STANDARD_MOTOR_SHIELD G-9934>"
        )
        assert cmd_type == "iDCC-EX"
        assert "V-5.0.0" in params

    def test_parse_empty_response(self):
        """Test parsing empty response."""
        cmd_type, params = parse_response("<>")
        assert cmd_type == ""
        assert params == []

    def test_parse_whitespace(self):
        """Test parsing with extra whitespace."""
        cmd_type, params = parse_response("  <p1>  ")
        assert cmd_type == "p"
        assert params == ["1"]


class TestFormatCommand:
    """Tests for format_command function."""

    def test_format_command_without_brackets(self):
        """Test formatting command without brackets."""
        assert format_command("t 3 50 1") == "<t 3 50 1>"

    def test_format_command_with_brackets(self):
        """Test formatting command that already has brackets."""
        assert format_command("<t 3 50 1>") == "<t 3 50 1>"

    def test_format_command_partial_brackets(self):
        """Test formatting command with partial brackets."""
        assert format_command("<t 3 50 1") == "<t 3 50 1>"
        assert format_command("t 3 50 1>") == "<t 3 50 1>"

    def test_format_empty_command(self):
        """Test formatting empty command."""
        assert format_command("") == ""
        assert format_command("  ") == ""

    def test_format_command_strips_whitespace(self):
        """Test formatting strips extra whitespace."""
        assert format_command("  t 3 50 1  ") == "<t 3 50 1>"


class TestGetTimestamp:
    """Tests for get_timestamp function."""

    def test_timestamp_format(self):
        """Test timestamp has correct format."""
        timestamp = get_timestamp()
        # Should be HH:MM:SS.mmm format
        parts = timestamp.split(':')
        assert len(parts) == 3
        assert len(parts[0]) == 2  # Hours
        assert len(parts[1]) == 2  # Minutes
        # Seconds with milliseconds
        assert '.' in parts[2]
        sec_parts = parts[2].split('.')
        assert len(sec_parts[0]) == 2  # Seconds
        assert len(sec_parts[1]) == 3  # Milliseconds

    def test_timestamp_is_string(self):
        """Test timestamp returns a string."""
        timestamp = get_timestamp()
        assert isinstance(timestamp, str)
