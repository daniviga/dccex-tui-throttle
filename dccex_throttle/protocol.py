"""
DCC-EX Protocol implementation for TCP socket communication.
"""
import asyncio
import logging
from typing import Optional, Callable, Awaitable, Dict, Any
from .models import Direction
from .utils import parse_response


logger = logging.getLogger(__name__)


class DCCEXProtocol:
    """DCC-EX Command Station protocol handler."""

    def __init__(
        self,
        host: str,
        port: int = 2560,
        timeout: int = 10,
        on_response: Optional[Callable[[str], Awaitable[None]]] = None,
        on_disconnect: Optional[Callable[[], Awaitable[None]]] = None,
        on_broadcast: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
    ):
        """
        Initialize DCC-EX protocol handler.

        Args:
            host: Command Station host address
            port: Command Station port (default 2560)
            timeout: Connection timeout in seconds
            on_response: Async callback for responses
            on_disconnect: Async callback for disconnection
            on_broadcast: Async callback for broadcast messages
                         (command_type, parsed_data)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.on_response = on_response
        self.on_disconnect = on_disconnect
        self.on_broadcast = on_broadcast

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.receive_task: Optional[asyncio.Task] = None
        self._buffer = ""

    async def connect(self) -> bool:
        """
        Connect to DCC-EX Command Station.

        Returns:
            bool: True if connected successfully
        """
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout
            )
            self.connected = True
            logger.info(f"Connected to {self.host}:{self.port}")

            # Start receive loop
            self.receive_task = asyncio.create_task(self._receive_loop())

            # Request status to check connection
            await self.send_status()

            return True
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {self.host}:{self.port}")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Command Station."""
        self.connected = False

        # Cancel receive task
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        # Close writer
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

        logger.info("Disconnected from Command Station")

        # Notify UI of disconnection
        if self.on_disconnect:
            await self.on_disconnect()

    async def _receive_loop(self):
        """Continuously receive and process responses."""
        try:
            while self.connected and self.reader:
                data = await self.reader.read(1024)
                if not data:
                    # Connection closed
                    await self.disconnect()
                    break

                # Decode and process data
                self._buffer += data.decode('utf-8', errors='ignore')

                # Process complete messages (ending with \n or \r\n)
                while '\n' in self._buffer:
                    line, self._buffer = self._buffer.split('\n', 1)
                    line = line.strip()

                    if line:
                        await self._handle_response(line)
        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            await self.disconnect()

    async def _handle_response(self, response: str):
        """Handle a received response."""
        logger.debug(f"Received: {response}")

        # Notify UI of raw response
        if self.on_response:
            await self.on_response(response)

        # Parse and handle broadcast messages
        if self.on_broadcast:
            cmd_type, params = parse_response(response)

            # Parse specific broadcast message types
            if cmd_type == "l" and len(params) >= 4:
                # Locomotive state broadcast: <l LOCO REG SPEEDBYTE FUNCTMAP>
                try:
                    loco_addr = int(params[0])
                    # params[1] is register (not used, legacy)
                    speedbyte = int(params[2])
                    functions = int(params[3]) if len(params) > 3 else 0

                    # Decode speed and direction from speedbyte
                    # Speedbyte format (DCC-EX protocol):
                    # 0 = stop reverse
                    # 1 = emergency stop reverse (treat as speed 0)
                    # 2-127 = reverse (speed = speedbyte - 1, gives 1-126)
                    # 128 = stop forward
                    # 129 = emergency stop forward (treat as speed 0)
                    # 130-255 = forward (speed = speedbyte - 129, gives 1-126)
                    if speedbyte == 0 or speedbyte == 1:
                        speed = 0
                        direction = Direction.REVERSE
                    elif speedbyte == 128 or speedbyte == 129:
                        speed = 0
                        direction = Direction.FORWARD
                    elif 2 <= speedbyte <= 127:
                        speed = speedbyte - 1
                        direction = Direction.REVERSE
                    elif 130 <= speedbyte <= 255:
                        speed = speedbyte - 129
                        direction = Direction.FORWARD
                    else:
                        # Shouldn't happen, but default to stop forward
                        speed = 0
                        direction = Direction.FORWARD

                    broadcast_data = {
                        "loco_address": loco_addr,
                        "speed": speed,
                        "direction": direction,
                        "speedbyte": speedbyte,
                        "functions": functions
                    }

                    await self.on_broadcast("loco_state", broadcast_data)

                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing loco state: {e}")

            elif cmd_type == "p" and len(params) >= 1:
                # Power state broadcast: <p0> or <p1>
                try:
                    power_state = int(params[0])
                    broadcast_data = {
                        "power": power_state == 1
                    }
                    await self.on_broadcast("power_state", broadcast_data)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing power state: {e}")

            elif cmd_type.startswith("iDCC") or cmd_type == "i":
                # Command station info
                broadcast_data = {
                    "info": response
                }
                await self.on_broadcast("cs_info", broadcast_data)

            elif cmd_type == "H" and len(params) >= 2:
                # Turnout state: <H ID STATE>
                try:
                    turnout_id = int(params[0])
                    turnout_state = int(params[1])
                    broadcast_data = {
                        "turnout_id": turnout_id,
                        "state": turnout_state
                    }
                    await self.on_broadcast("turnout_state", broadcast_data)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing turnout state: {e}")

    async def send_command(self, command: str) -> bool:
        """
        Send a command to the Command Station.

        Args:
            command: Command string (without < > brackets)

        Returns:
            bool: True if sent successfully
        """
        if not self.connected or not self.writer:
            logger.error("Not connected to Command Station")
            return False

        try:
            # Format command with brackets and newline
            formatted = f"<{command}>\n"
            self.writer.write(formatted.encode('utf-8'))
            await self.writer.drain()
            logger.debug(f"Sent: <{command}>")
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            await self.disconnect()
            return False

    # Throttle commands

    async def send_throttle(
        self, loco_address: int, speed: int, direction: Direction
    ) -> bool:
        """
        Send throttle command.

        Args:
            loco_address: Locomotive DCC address
            speed: Speed (0-126)
            direction: Direction (0=reverse, 1=forward)
        """
        return await self.send_command(
            f"t {loco_address} {speed} {direction.value}"
        )

    async def send_function(
        self, loco_address: int, function: int, state: bool
    ) -> bool:
        """
        Send function command.

        Args:
            loco_address: Locomotive DCC address
            function: Function number (0-31)
            state: Function state (True=on, False=off)
        """
        state_val = 1 if state else 0
        return await self.send_command(
            f"F {loco_address} {function} {state_val}"
        )

    async def send_emergency_stop(self) -> bool:
        """Send emergency stop command (stop all locomotives)."""
        return await self.send_command("!")

    # Track power commands

    async def send_power_on(self) -> bool:
        """Turn track power on."""
        return await self.send_command("1")

    async def send_power_off(self) -> bool:
        """Turn track power off."""
        return await self.send_command("0")

    # Status commands

    async def send_status(self) -> bool:
        """Request status from Command Station."""
        return await self.send_command("s")

    # Direct command

    async def send_direct(self, command: str) -> bool:
        """
        Send a direct command to the Command Station.

        Args:
            command: Command string (with or without < > brackets)
        """
        # Remove brackets if present
        command = command.strip()
        if command.startswith('<'):
            command = command[1:]
        if command.endswith('>'):
            command = command[:-1]

        return await self.send_command(command)
