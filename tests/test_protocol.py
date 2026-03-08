"""
Tests for dccex_throttle.protocol module with mocked DCC-EX server.
"""
import pytest
import asyncio
from dccex_throttle.protocol import DCCEXProtocol
from dccex_throttle.models import Direction
from tests.mock_server import MockDCCEXServer


@pytest.fixture
async def mock_server():
    """Fixture to create and manage a mock DCC-EX server."""
    server = MockDCCEXServer()
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def protocol(mock_server):
    """Fixture to create a DCCEXProtocol connected to mock server."""
    responses = []
    broadcasts = []

    async def on_response(response):
        responses.append(response)

    async def on_broadcast(cmd_type, data):
        broadcasts.append((cmd_type, data))

    proto = DCCEXProtocol(
        host=mock_server.host,
        port=mock_server.port,
        timeout=5,
        on_response=on_response,
        on_broadcast=on_broadcast
    )
    proto.responses = responses
    proto.broadcasts = broadcasts
    
    yield proto
    
    if proto.connected:
        await proto.disconnect()


class TestDCCEXProtocolConnection:
    """Tests for protocol connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_server):
        """Test successful connection to server."""
        protocol = DCCEXProtocol(host=mock_server.host, port=mock_server.port)
        result = await protocol.connect()
        assert result is True
        assert protocol.connected is True
        await protocol.disconnect()

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        """Test connection timeout to non-existent server."""
        protocol = DCCEXProtocol(host="192.0.2.1", port=9999, timeout=0.1)
        result = await protocol.connect()
        assert result is False
        assert protocol.connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, protocol, mock_server):
        """Test disconnecting from server."""
        await protocol.connect()
        assert protocol.connected is True
        await protocol.disconnect()
        assert protocol.connected is False


class TestDCCEXProtocolPowerCommands:
    """Tests for track power commands."""

    @pytest.mark.asyncio
    async def test_send_power_on(self, protocol, mock_server):
        """Test sending power on command."""
        await protocol.connect()
        await asyncio.sleep(0.1)  # Let initial messages process
        
        result = await protocol.send_power_on()
        assert result is True
        
        await asyncio.sleep(0.1)
        assert mock_server.track_power is True
        
        # Check for power broadcast
        power_broadcasts = [
            b for b in protocol.broadcasts if b[0] == 'power_state'
        ]
        assert len(power_broadcasts) > 0
        assert power_broadcasts[-1][1]['power'] is True

    @pytest.mark.asyncio
    async def test_send_power_off(self, protocol, mock_server):
        """Test sending power off command."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        # Turn on first
        await protocol.send_power_on()
        await asyncio.sleep(0.1)
        
        # Then turn off
        result = await protocol.send_power_off()
        assert result is True
        
        await asyncio.sleep(0.1)
        assert mock_server.track_power is False


class TestDCCEXProtocolThrottleCommands:
    """Tests for throttle control commands."""

    @pytest.mark.asyncio
    async def test_send_throttle_forward(self, protocol, mock_server):
        """Test sending throttle command for forward movement."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        result = await protocol.send_throttle(3, 50, Direction.FORWARD)
        assert result is True
        
        await asyncio.sleep(0.1)
        
        # Check mock server received and processed command
        loco_state = mock_server.get_loco_state(3)
        assert loco_state is not None
        assert loco_state['speed'] == 50
        assert loco_state['direction'] == 1

    @pytest.mark.asyncio
    async def test_send_throttle_reverse(self, protocol, mock_server):
        """Test sending throttle command for reverse movement."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        result = await protocol.send_throttle(5, 75, Direction.REVERSE)
        assert result is True
        
        await asyncio.sleep(0.1)
        
        loco_state = mock_server.get_loco_state(5)
        assert loco_state is not None
        assert loco_state['speed'] == 75
        assert loco_state['direction'] == 0

    @pytest.mark.asyncio
    async def test_send_throttle_stop(self, protocol, mock_server):
        """Test sending stop command."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        # Set speed first
        await protocol.send_throttle(10, 60, Direction.FORWARD)
        await asyncio.sleep(0.1)
        
        # Then stop
        result = await protocol.send_throttle(10, 0, Direction.FORWARD)
        assert result is True
        
        await asyncio.sleep(0.1)
        
        loco_state = mock_server.get_loco_state(10)
        assert loco_state['speed'] == 0

    @pytest.mark.asyncio
    async def test_broadcast_received(self, protocol, mock_server):
        """Test receiving locomotive broadcast messages."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        await protocol.send_throttle(3, 50, Direction.FORWARD)
        await asyncio.sleep(0.2)
        
        # Check broadcasts were received
        loco_broadcasts = [
            b for b in protocol.broadcasts if b[0] == 'loco_state'
        ]
        assert len(loco_broadcasts) > 0
        
        # Check last broadcast data
        last_broadcast = loco_broadcasts[-1][1]
        assert last_broadcast['loco_address'] == 3
        assert last_broadcast['speed'] == 50
        assert last_broadcast['direction'] == Direction.FORWARD


class TestDCCEXProtocolFunctionCommands:
    """Tests for function control commands."""

    @pytest.mark.asyncio
    async def test_send_function_on(self, protocol, mock_server):
        """Test turning function on."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        result = await protocol.send_function(3, 0, True)
        assert result is True
        
        await asyncio.sleep(0.1)
        
        loco_state = mock_server.get_loco_state(3)
        assert loco_state is not None
        # F0 is bit 0, so functions should be 1
        assert loco_state['functions'] & 1 == 1

    @pytest.mark.asyncio
    async def test_send_function_off(self, protocol, mock_server):
        """Test turning function off."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        # Turn on first
        await protocol.send_function(3, 1, True)
        await asyncio.sleep(0.1)
        
        # Then turn off
        result = await protocol.send_function(3, 1, False)
        assert result is True
        
        await asyncio.sleep(0.1)
        
        loco_state = mock_server.get_loco_state(3)
        # F1 is bit 1, should be 0
        assert loco_state['functions'] & 2 == 0

    @pytest.mark.asyncio
    async def test_multiple_functions(self, protocol, mock_server):
        """Test controlling multiple functions."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        # Turn on F0, F2, F5
        await protocol.send_function(7, 0, True)
        await asyncio.sleep(0.05)
        await protocol.send_function(7, 2, True)
        await asyncio.sleep(0.05)
        await protocol.send_function(7, 5, True)
        await asyncio.sleep(0.1)
        
        loco_state = mock_server.get_loco_state(7)
        # Check bits: 0, 2, 5 should be set
        # Binary: 100101 = 37
        assert loco_state['functions'] & 1 == 1    # F0
        assert loco_state['functions'] & 4 == 4    # F2
        assert loco_state['functions'] & 32 == 32  # F5


class TestDCCEXProtocolEmergencyStop:
    """Tests for emergency stop command."""

    @pytest.mark.asyncio
    async def test_emergency_stop(self, protocol, mock_server):
        """Test emergency stop stops all locos."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        # Start multiple locos
        await protocol.send_throttle(3, 50, Direction.FORWARD)
        await protocol.send_throttle(5, 75, Direction.REVERSE)
        await asyncio.sleep(0.1)
        
        # Emergency stop
        result = await protocol.send_emergency_stop()
        assert result is True
        
        await asyncio.sleep(0.1)
        
        # All locos should be stopped
        loco3 = mock_server.get_loco_state(3)
        loco5 = mock_server.get_loco_state(5)
        assert loco3['speed'] == 0
        assert loco5['speed'] == 0


class TestDCCEXProtocolDirectCommands:
    """Tests for direct command sending."""

    @pytest.mark.asyncio
    async def test_send_direct_with_brackets(self, protocol, mock_server):
        """Test sending direct command with brackets."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        result = await protocol.send_direct("<1>")
        assert result is True
        
        await asyncio.sleep(0.1)
        assert mock_server.track_power is True

    @pytest.mark.asyncio
    async def test_send_direct_without_brackets(self, protocol, mock_server):
        """Test sending direct command without brackets."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        result = await protocol.send_direct("1")
        assert result is True
        
        await asyncio.sleep(0.1)
        assert mock_server.track_power is True

    @pytest.mark.asyncio
    async def test_send_status(self, protocol, mock_server):
        """Test sending status request."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        result = await protocol.send_status()
        assert result is True
        
        await asyncio.sleep(0.1)
        
        # Should have received info response
        assert len(protocol.responses) > 0


class TestDCCEXProtocolSpeedByteDecoding:
    """Tests for speedbyte decoding in broadcasts."""

    @pytest.mark.asyncio
    async def test_decode_speedbyte_stop_forward(self, protocol, mock_server):
        """Test decoding speedbyte for stopped forward."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        await protocol.send_throttle(3, 0, Direction.FORWARD)
        await asyncio.sleep(0.1)
        
        loco_broadcasts = [
            b for b in protocol.broadcasts 
            if b[0] == 'loco_state' and b[1]['loco_address'] == 3
        ]
        assert len(loco_broadcasts) > 0
        
        broadcast = loco_broadcasts[-1][1]
        assert broadcast['speed'] == 0
        assert broadcast['direction'] == Direction.FORWARD
        assert broadcast['speedbyte'] == 128

    @pytest.mark.asyncio
    async def test_decode_speedbyte_forward_movement(self, protocol, mock_server):
        """Test decoding speedbyte for forward movement."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        await protocol.send_throttle(3, 50, Direction.FORWARD)
        await asyncio.sleep(0.1)
        
        loco_broadcasts = [
            b for b in protocol.broadcasts 
            if b[0] == 'loco_state' and b[1]['loco_address'] == 3
        ]
        
        broadcast = loco_broadcasts[-1][1]
        assert broadcast['speed'] == 50
        assert broadcast['direction'] == Direction.FORWARD
        # Forward: 50 + 129 = 179
        assert broadcast['speedbyte'] == 179

    @pytest.mark.asyncio
    async def test_decode_speedbyte_reverse_movement(self, protocol, mock_server):
        """Test decoding speedbyte for reverse movement."""
        await protocol.connect()
        await asyncio.sleep(0.1)
        
        await protocol.send_throttle(5, 75, Direction.REVERSE)
        await asyncio.sleep(0.1)
        
        loco_broadcasts = [
            b for b in protocol.broadcasts 
            if b[0] == 'loco_state' and b[1]['loco_address'] == 5
        ]
        
        broadcast = loco_broadcasts[-1][1]
        assert broadcast['speed'] == 75
        assert broadcast['direction'] == Direction.REVERSE
        # Reverse: 75 + 1 = 76
        assert broadcast['speedbyte'] == 76
