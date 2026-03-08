"""
Mock DCC-EX Command Station server for testing.

This module provides a mock TCP server that simulates DCC-EX Command Station
responses for testing the protocol implementation without real hardware.
"""
import asyncio
from typing import Optional, Callable, List, Dict
import logging

logger = logging.getLogger(__name__)


class MockDCCEXServer:
    """Mock DCC-EX Command Station TCP server for testing."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,  # 0 = let OS assign port
    ):
        """Initialize mock server."""
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.clients: List[asyncio.StreamWriter] = []
        self.received_commands: List[str] = []
        self.track_power = False
        self.locos: Dict[int, Dict] = {}  # loco_address -> state
        self.running = False

    async def start(self):
        """Start the mock server."""
        self.server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        # Get the actual port assigned
        self.port = self.server.sockets[0].getsockname()[1]
        self.running = True
        logger.info(f"Mock DCC-EX server started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the mock server."""
        self.running = False
        # Close all client connections
        for writer in self.clients:
            writer.close()
            await writer.wait_closed()
        self.clients.clear()

        # Stop the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("Mock DCC-EX server stopped")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle a client connection."""
        self.clients.append(writer)
        addr = writer.get_extra_info('peername')
        logger.debug(f"Client connected from {addr}")

        # Send initial info message
        await self._send_response(writer, "<iDCC-EX V-5.0.0 / MEGA / STANDARD_MOTOR_SHIELD G-9934>")

        try:
            while self.running:
                data = await reader.read(1024)
                if not data:
                    break

                message = data.decode('utf-8').strip()
                logger.debug(f"Received: {message}")
                self.received_commands.append(message)

                # Process command and send response
                await self._process_command(writer, message)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            if writer in self.clients:
                self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()
            logger.debug(f"Client disconnected from {addr}")

    async def _process_command(self, writer: asyncio.StreamWriter, cmd: str):
        """Process a DCC-EX command and send appropriate response."""
        # Remove < > brackets if present
        cmd = cmd.strip()
        if cmd.startswith('<'):
            cmd = cmd[1:]
        if cmd.endswith('>'):
            cmd = cmd[:-1]

        parts = cmd.split()
        if not parts:
            return

        cmd_type = parts[0]

        # Power commands
        if cmd_type == '1':
            # Power on
            self.track_power = True
            await self._send_response(writer, "<p1>")

        elif cmd_type == '0':
            # Power off
            self.track_power = False
            await self._send_response(writer, "<p0>")

        # Status request
        elif cmd_type == 's':
            power_state = "ON" if self.track_power else "OFF"
            await self._send_response(
                writer,
                f"<iDCC-EX V-5.0.0 / MEGA / STANDARD_MOTOR_SHIELD G-9934>"
            )
            await self._send_response(
                writer, f"<p{1 if self.track_power else 0}>"
            )

        # Throttle command: <t LOCO SPEED DIR>
        elif cmd_type == 't' and len(parts) >= 4:
            loco_addr = int(parts[1])
            speed = int(parts[2])
            direction = int(parts[3])

            # Store loco state
            if loco_addr not in self.locos:
                self.locos[loco_addr] = {
                    'speed': 0,
                    'direction': 1,
                    'functions': 0
                }

            self.locos[loco_addr]['speed'] = speed
            self.locos[loco_addr]['direction'] = direction

            # Calculate speedbyte
            speedbyte = self._calculate_speedbyte(speed, direction)

            # Broadcast loco state to all clients
            response = (
                f"<l {loco_addr} {speedbyte} {direction} "
                f"{self.locos[loco_addr]['functions']}>"
            )
            await self._broadcast(response)

        # Function command: <F LOCO FUNCTION STATE>
        elif cmd_type == 'F' and len(parts) >= 4:
            loco_addr = int(parts[1])
            fn_num = int(parts[2])
            fn_state = int(parts[3])

            # Initialize loco if needed
            if loco_addr not in self.locos:
                self.locos[loco_addr] = {
                    'speed': 0,
                    'direction': 1,
                    'functions': 0
                }

            # Update function bit
            if fn_state == 1:
                self.locos[loco_addr]['functions'] |= (1 << fn_num)
            else:
                self.locos[loco_addr]['functions'] &= ~(1 << fn_num)

            # Broadcast loco state
            speedbyte = self._calculate_speedbyte(
                self.locos[loco_addr]['speed'],
                self.locos[loco_addr]['direction']
            )
            response = (
                f"<l {loco_addr} {speedbyte} "
                f"{self.locos[loco_addr]['direction']} "
                f"{self.locos[loco_addr]['functions']}>"
            )
            await self._broadcast(response)

        # Emergency stop
        elif cmd_type == '!':
            # Stop all locos
            for loco_addr in self.locos:
                self.locos[loco_addr]['speed'] = 0
                speedbyte = self._calculate_speedbyte(
                    0, self.locos[loco_addr]['direction']
                )
                response = (
                    f"<l {loco_addr} {speedbyte} "
                    f"{self.locos[loco_addr]['direction']} "
                    f"{self.locos[loco_addr]['functions']}>"
                )
                await self._broadcast(response)

    def _calculate_speedbyte(self, speed: int, direction: int) -> int:
        """Calculate DCC-EX speedbyte from speed and direction."""
        if speed == 0:
            return 128 if direction == 1 else 0
        if direction == 1:  # Forward
            return speed + 129
        else:  # Reverse
            return speed + 1

    async def _send_response(self, writer: asyncio.StreamWriter, response: str):
        """Send a response to a specific client."""
        try:
            writer.write(f"{response}\n".encode('utf-8'))
            await writer.drain()
            logger.debug(f"Sent: {response}")
        except Exception as e:
            logger.error(f"Error sending response: {e}")

    async def _broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for writer in self.clients[:]:  # Copy list to avoid modification issues
            await self._send_response(writer, message)

    def get_received_commands(self) -> List[str]:
        """Get list of all received commands."""
        return self.received_commands.copy()

    def clear_received_commands(self):
        """Clear the list of received commands."""
        self.received_commands.clear()

    def get_loco_state(self, loco_addr: int) -> Optional[Dict]:
        """Get the current state of a locomotive."""
        return self.locos.get(loco_addr)
