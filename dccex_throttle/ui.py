"""
Textual UI for DCC-EX Throttle TUI application.
"""
import time
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Input, Static, Label, Switch, RichLog
)
from textual.binding import Binding
from textual.reactive import reactive
from textual import on

from .protocol import DCCEXProtocol
from .models import ThrottleState, Direction
from .config import Config
from .utils import validate_loco_address, get_timestamp, parse_response
from typing import Optional


class DCCEXThrottleApp(App):
    """DCC-EX Throttle TUI Application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #connection-panel {
        height: 5;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    #control-container {
        height: 1fr;
    }

    #throttle-panel {
        width: 50;
        height: 100%;
        padding: 1;
        background: $panel;
        border: solid $secondary;
    }

    #function-panel {
        width: 1fr;
        height: 100%;
        padding: 1;
        background: $panel;
        border: solid $secondary;
    }

    #debug-panel {
        height: 15;
        padding: 1;
        background: $panel;
        border: solid $accent;
    }

    .function-button {
        width: 12;
        margin: 0 1;
    }

    .function-row {
        height: auto;
        margin: 1 0;
    }

    #speed-display {
        text-align: center;
        padding: 1;
        background: $boost;
        color: $text;
        margin: 1 0;
    }

    #status-label {
        padding: 0 1;
    }

    .control-button {
        margin: 1 0;
    }

    #debug-log {
        height: 1fr;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("ctrl+p", "toggle_power", "Toggle Power", show=True),
        Binding("ctrl+s", "emergency_stop", "E-Stop", show=True),
        Binding("up", "speed_up", "Speed Up", show=True),
        Binding("down", "speed_down", "Speed Down", show=True),
        Binding("left", "direction_reverse", "Reverse", show=True),
        Binding("right", "direction_forward", "Forward", show=True),
        Binding("f1", "toggle_f0", "F0", show=False),
        Binding("f2", "toggle_f1", "F1", show=False),
        Binding("f3", "toggle_f2", "F2", show=False),
        Binding("f4", "toggle_f3", "F3", show=False),
        Binding("f5", "toggle_f4", "F4", show=False),
        Binding("f6", "toggle_f5", "F5", show=False),
        Binding("f7", "toggle_f6", "F6", show=False),
        Binding("f8", "toggle_f7", "F7", show=False),
        Binding("f9", "toggle_f8", "F8", show=False),
        Binding("f10", "toggle_f9", "F9", show=False),
        Binding("f11", "toggle_f10", "F10", show=False),
        Binding("f12", "toggle_f11", "F11", show=False),
    ]

    # Reactive properties
    connected = reactive(False)
    track_power = reactive(False)
    acquired = reactive(False)
    current_speed = reactive(0)
    current_direction = reactive(Direction.FORWARD)

    def __init__(self, config: Config):
        """Initialize the application."""
        super().__init__()
        self.config = config
        self.state = ThrottleState()
        self.protocol: Optional[DCCEXProtocol] = None
        self.last_command_time = 0.0  # Track last command sent time

        # Get config values
        conn_config = config.get_connection_config()
        self.state.host = conn_config.get('host', 'localhost')
        self.state.port = conn_config.get('port', 2560)

        self.throttle_config = config.get_throttle_config()
        self.speed_step = self.throttle_config.get('speed_step', 1)
        self.max_speed = self.throttle_config.get('max_speed', 126)

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()

        with Container(id="main-container"):
            # Connection panel
            with Container(id="connection-panel"):
                with Horizontal():
                    yield Static("Loco Address: N/A", id="loco-address-display")
                    yield Input(
                        placeholder="Enter loco address",
                        id="loco-input",
                        type="integer"
                    )
                    yield Button("Acquire", id="acquire-btn", variant="primary")
                    yield Button("Release", id="release-btn", variant="default")
                    yield Static("Power: OFF", id="power-status")
                    yield Switch(value=False, id="power-switch")

            # Main control area
            with Horizontal(id="control-container"):
                # Throttle panel (left)
                with ScrollableContainer(id="throttle-panel"):
                    yield Static(
                        "Speed: 0\nDirection: FWD",
                        id="speed-display"
                    )
                    # Speed and direction controls in two columns
                    with Horizontal():
                        with Vertical():
                            yield Button("▲ Faster", id="speed-up-btn", classes="control-button")
                            yield Button("▶ Forward", id="dir-forward-btn", classes="control-button")
                            yield Button("STOP", id="stop-btn", variant="warning", classes="control-button")
                        with Vertical():
                            yield Button("▼ Slower", id="speed-down-btn", classes="control-button")
                            yield Button("◀ Reverse", id="dir-reverse-btn", classes="control-button")
                            yield Button("E-STOP", id="estop-btn", variant="error", classes="control-button")

                # Function panel (right)
                with ScrollableContainer(id="function-panel"):
                    yield Label("Functions (F0-F31)")

                    # Function buttons F0-F11
                    with Horizontal(classes="function-row"):
                        yield Button("F0", id="fn-0", classes="function-button")
                        yield Button("F1", id="fn-1", classes="function-button")
                        yield Button("F2", id="fn-2", classes="function-button")
                        yield Button("F3", id="fn-3", classes="function-button")

                    with Horizontal(classes="function-row"):
                        yield Button("F4", id="fn-4", classes="function-button")
                        yield Button("F5", id="fn-5", classes="function-button")
                        yield Button("F6", id="fn-6", classes="function-button")
                        yield Button("F7", id="fn-7", classes="function-button")

                    with Horizontal(classes="function-row"):
                        yield Button("F8", id="fn-8", classes="function-button")
                        yield Button("F9", id="fn-9", classes="function-button")
                        yield Button("F10", id="fn-10", classes="function-button")
                        yield Button("F11", id="fn-11", classes="function-button")

                    # Extended function buttons F12-F31 (now always visible)
                    with Horizontal(classes="function-row"):
                        yield Button("F12", id="fn-12", classes="function-button")
                        yield Button("F13", id="fn-13", classes="function-button")
                        yield Button("F14", id="fn-14", classes="function-button")
                        yield Button("F15", id="fn-15", classes="function-button")

                    with Horizontal(classes="function-row"):
                        yield Button("F16", id="fn-16", classes="function-button")
                        yield Button("F17", id="fn-17", classes="function-button")
                        yield Button("F18", id="fn-18", classes="function-button")
                        yield Button("F19", id="fn-19", classes="function-button")

                    with Horizontal(classes="function-row"):
                        yield Button("F20", id="fn-20", classes="function-button")
                        yield Button("F21", id="fn-21", classes="function-button")
                        yield Button("F22", id="fn-22", classes="function-button")
                        yield Button("F23", id="fn-23", classes="function-button")

                    with Horizontal(classes="function-row"):
                        yield Button("F24", id="fn-24", classes="function-button")
                        yield Button("F25", id="fn-25", classes="function-button")
                        yield Button("F26", id="fn-26", classes="function-button")
                        yield Button("F27", id="fn-27", classes="function-button")

                    with Horizontal(classes="function-row"):
                        yield Button("F28", id="fn-28", classes="function-button")
                        yield Button("F29", id="fn-29", classes="function-button")
                        yield Button("F30", id="fn-30", classes="function-button")
                        yield Button("F31", id="fn-31", classes="function-button")

            # Debug console
            with Container(id="debug-panel"):
                yield Label("Debug Console:")
                yield RichLog(id="debug-log", wrap=True, highlight=True)
                with Horizontal():
                    yield Input(
                        placeholder="Enter direct command (without < >)",
                        id="direct-input"
                    )
                    yield Button("Send", id="send-btn", variant="primary")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle mount event."""
        # Set initial subtitle
        self.sub_title = f"Disconnected | {self.state.host}:{self.state.port}"

        # Auto-connect if configured
        if self.config.get('connection', 'auto_connect', False):
            await self.action_connect()

        # Log startup
        await self.log_message("S", "DCC-EX Throttle TUI started")
        await self.log_message("S", f"Configured host: {self.state.host}:{self.state.port}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "acquire-btn":
            await self.acquire_loco()
        elif button_id == "release-btn":
            await self.release_loco()
        elif button_id == "speed-up-btn":
            await self.action_speed_up()
        elif button_id == "speed-down-btn":
            await self.action_speed_down()
        elif button_id == "dir-forward-btn":
            await self.set_direction(Direction.FORWARD)
        elif button_id == "dir-reverse-btn":
            await self.set_direction(Direction.REVERSE)
        elif button_id == "stop-btn":
            await self.stop_loco()
        elif button_id == "estop-btn":
            await self.action_emergency_stop()
        elif button_id == "send-btn":
            await self.send_direct_command()
        elif button_id and button_id.startswith("fn-"):
            # Function button
            fn_num = int(button_id.split("-")[1])
            await self.toggle_function(fn_num)

    @on(Switch.Changed, "#power-switch")
    async def on_power_switch_changed(self, event: Switch.Changed) -> None:
        """Handle power switch toggle."""
        await self.toggle_power_internal(event.value)

    @on(Input.Submitted, "#direct-input")
    async def on_direct_input_submitted(self) -> None:
        """Handle direct command submission."""
        await self.send_direct_command()

    @on(Input.Submitted, "#loco-input")
    async def on_loco_input_submitted(self) -> None:
        """Handle loco address submission."""
        await self.acquire_loco()

    # Action methods

    async def action_connect(self) -> None:
        """Connect to Command Station."""
        if self.connected:
            await self.log_message("S", "Already connected")
            return

        await self.log_message("S", f"Connecting to {self.state.host}:{self.state.port}...")

        # Create protocol
        self.protocol = DCCEXProtocol(
            host=self.state.host,
            port=self.state.port,
            timeout=self.config.get('connection', 'timeout', 10),
            on_response=self.handle_response,
            on_disconnect=self.handle_disconnect,
            on_broadcast=self.handle_broadcast
        )

        # Connect
        success = await self.protocol.connect()

        if success:
            self.connected = True
            self.state.connected = True
            self.sub_title = f"Connected | {self.state.host}:{self.state.port}"
            await self.log_message("S", "Connected successfully")
        else:
            await self.log_message("S", "Connection failed")

    async def handle_response(self, response: str) -> None:
        """Handle response from Command Station."""
        await self.log_message("R", response)

        # Parse response
        cmd_type, params = parse_response(response)

        # Handle specific responses
        if cmd_type == "p":
            # Power state
            if params and params[0] == "1":
                self.track_power = True
                self.state.track_power = True
                power_status = self.query_one("#power-status", Static)
                power_status.update("Power: ON")

                power_switch = self.query_one("#power-switch", Switch)
                power_switch.value = True
            elif params and params[0] == "0":
                self.track_power = False
                self.state.track_power = False
                power_status = self.query_one("#power-status", Static)
                power_status.update("Power: OFF")

                power_switch = self.query_one("#power-switch", Switch)
                power_switch.value = False

        elif cmd_type == "i" or cmd_type.startswith("iDCC"):
            # Command station info
            await self.log_message("S", "Command Station ready")

    async def handle_broadcast(self, cmd_type: str, data: dict) -> None:
        """
        Handle broadcast messages from Command Station.

        This is called for any broadcast message, allowing the UI to update
        based on commands sent by other throttles or the Command Station itself.

        Args:
            cmd_type: Type of broadcast (loco_state, power_state, etc.)
            data: Parsed data from the broadcast
        """
        if cmd_type == "loco_state":
            # Locomotive state update: <l LOCO SPEEDBYTE DIR FUNCTIONS>
            loco_addr = data.get("loco_address")
            speed = data.get("speed")
            direction = data.get("direction")
            functions = data.get("functions")

            # Only update if this is our currently acquired loco
            if (self.acquired and self.state.current_loco and
                    self.state.current_loco.address == loco_addr and
                    speed is not None and direction is not None):

                # Ignore broadcasts that arrive too soon after our own command
                # This prevents race conditions where the CS echoes old state
                time_since_command = time.time() - self.last_command_time
                if time_since_command < 0.15:  # 150ms grace period
                    await self.log_message("S", f"Ignoring broadcast (too soon after command: {time_since_command:.3f}s)")
                    return

                # Update local state
                self.current_speed = speed
                self.current_direction = direction
                self.state.current_loco.set_speed(speed)
                self.state.current_loco.set_direction(direction)

                # Update speed display
                try:
                    self.update_speed_display()
                except Exception:
                    pass  # Widget might not be mounted yet

                # Update direction button appearance
                try:
                    fwd_btn = self.query_one("#dir-forward-btn", Button)
                    rev_btn = self.query_one("#dir-reverse-btn", Button)
                    if direction == Direction.FORWARD:
                        fwd_btn.variant = "primary"
                        rev_btn.variant = "default"
                    else:
                        fwd_btn.variant = "default"
                        rev_btn.variant = "primary"
                except Exception:
                    pass  # Buttons might not be mounted yet

                # Update function states
                if functions is not None:
                    for fn_num in range(32):
                        fn_state = (functions >> fn_num) & 0x1
                        self.state.current_loco.set_function(fn_num, fn_state == 1)

                        # Update button appearance
                        try:
                            button = self.query_one(f"#fn-{fn_num}", Button)
                            button.variant = "success" if fn_state == 1 else "default"
                        except Exception:
                            pass  # Button might not be visible

                await self.log_message("S", f"Updated loco {loco_addr} from broadcast (Speed: {speed}, Dir: {'FWD' if direction == Direction.FORWARD else 'REV'})")

        elif cmd_type == "power_state":
            # Power state update
            power = data.get("power", False)
            self.track_power = power
            self.state.track_power = power

            power_status = self.query_one("#power-status", Static)
            power_status.update("Power: ON" if power else "Power: OFF")

            power_switch = self.query_one("#power-switch", Switch)
            power_switch.value = power

        elif cmd_type == "cs_info":
            # Command station info
            info = data.get("info", "")
            # Extract version if present
            if "V-" in info or "VERSION" in info.upper():
                self.state.command_station_version = info

    async def handle_disconnect(self) -> None:
        """Handle disconnection from Command Station."""
        self.connected = False
        self.state.connected = False
        self.sub_title = f"Disconnected | {self.state.host}:{self.state.port}"
        await self.log_message("S", "Disconnected from Command Station")

    async def acquire_loco(self) -> None:
        """Acquire a locomotive."""
        if not self.connected:
            await self.action_connect()
            if not self.connected:
                return

        loco_input = self.query_one("#loco-input", Input)
        address_str = loco_input.value.strip()

        if not address_str:
            await self.log_message("S", "Please enter a loco address")
            return

        address = validate_loco_address(address_str)
        if address is None:
            await self.log_message("S", f"Invalid address: {address_str}")
            return

        # Acquire loco
        self.state.acquire_loco(address)
        self.acquired = True
        self.current_speed = 0
        self.current_direction = Direction.FORWARD

        await self.log_message("S", f"Acquired loco {address}")
        self.update_loco_address_display()
        self.update_speed_display()

        # Initialize direction button states
        try:
            fwd_btn = self.query_one("#dir-forward-btn", Button)
            rev_btn = self.query_one("#dir-reverse-btn", Button)
            fwd_btn.variant = "primary"
            rev_btn.variant = "default"
        except Exception:
            pass

        # Send initial throttle command
        if self.protocol:
            self.last_command_time = time.time()
            await self.protocol.send_throttle(address, 0, Direction.FORWARD)

    async def release_loco(self) -> None:
        """Release the current locomotive."""
        if not self.acquired:
            return

        # Stop loco before releasing
        if self.protocol and self.state.current_loco:
            await self.protocol.send_throttle(
                self.state.current_loco.address, 0, self.current_direction
            )

        address = self.state.current_loco.address if self.state.current_loco else 0
        self.state.release_loco()
        self.acquired = False
        self.current_speed = 0

        await self.log_message("S", f"Released loco {address}")
        self.update_loco_address_display()
        self.update_speed_display()

    async def action_speed_up(self) -> None:
        """Increase speed."""
        if not self.acquired or not self.state.current_loco:
            return

        new_speed = min(self.current_speed + self.speed_step, self.max_speed)
        self.current_speed = new_speed
        self.state.current_loco.set_speed(new_speed)
        self.update_speed_display()

        if self.protocol:
            self.last_command_time = time.time()
            await self.protocol.send_throttle(
                self.state.current_loco.address,
                new_speed,
                self.current_direction
            )

    async def action_speed_down(self) -> None:
        """Decrease speed."""
        if not self.acquired or not self.state.current_loco:
            return

        new_speed = max(self.current_speed - self.speed_step, 0)
        self.current_speed = new_speed
        self.state.current_loco.set_speed(new_speed)
        self.update_speed_display()

        if self.protocol:
            self.last_command_time = time.time()
            await self.protocol.send_throttle(
                self.state.current_loco.address,
                new_speed,
                self.current_direction
            )

    async def set_direction(self, direction: Direction) -> None:
        """Set direction."""
        if not self.acquired or not self.state.current_loco:
            return

        self.current_direction = direction
        self.state.current_loco.set_direction(direction)
        self.update_speed_display()

        # Update direction button appearance
        try:
            fwd_btn = self.query_one("#dir-forward-btn", Button)
            rev_btn = self.query_one("#dir-reverse-btn", Button)
            if direction == Direction.FORWARD:
                fwd_btn.variant = "primary"
                rev_btn.variant = "default"
            else:
                fwd_btn.variant = "default"
                rev_btn.variant = "primary"
        except Exception:
            pass  # Buttons might not be mounted yet

        if self.protocol:
            self.last_command_time = time.time()
            await self.protocol.send_throttle(
                self.state.current_loco.address,
                self.current_speed,
                direction
            )

    async def action_direction_forward(self) -> None:
        """Set direction to forward."""
        await self.set_direction(Direction.FORWARD)

    async def action_direction_reverse(self) -> None:
        """Set direction to reverse."""
        await self.set_direction(Direction.REVERSE)

    async def stop_loco(self) -> None:
        """Stop locomotive."""
        if not self.acquired or not self.state.current_loco:
            return

        self.current_speed = 0
        self.state.current_loco.set_speed(0)
        self.update_speed_display()

        if self.protocol:
            self.last_command_time = time.time()
            await self.protocol.send_throttle(
                self.state.current_loco.address,
                0,
                self.current_direction
            )

    async def action_emergency_stop(self) -> None:
        """Emergency stop all locomotives."""
        if self.protocol:
            await self.protocol.send_emergency_stop()

        self.current_speed = 0
        if self.state.current_loco:
            self.state.current_loco.set_speed(0)

        self.update_speed_display()
        await self.log_message("S", "EMERGENCY STOP")

    async def toggle_function(self, fn_num: int) -> None:
        """Toggle a function."""
        if not self.acquired or not self.state.current_loco:
            return

        self.state.current_loco.toggle_function(fn_num)
        new_state = self.state.current_loco.get_function(fn_num)

        # Update button variant
        button = self.query_one(f"#fn-{fn_num}", Button)
        button.variant = "success" if new_state else "default"

        if self.protocol:
            self.last_command_time = time.time()
            await self.protocol.send_function(
                self.state.current_loco.address,
                fn_num,
                new_state
            )

    async def action_toggle_power(self) -> None:
        """Toggle track power."""
        power_switch = self.query_one("#power-switch", Switch)
        power_switch.toggle()

    async def toggle_power_internal(self, state: bool) -> None:
        """Internal power toggle handler."""
        if not self.protocol:
            await self.action_connect()
            if not self.protocol:
                return

        if state:
            await self.protocol.send_power_on()
        else:
            await self.protocol.send_power_off()

    async def send_direct_command(self) -> None:
        """Send a direct command."""
        if not self.protocol:
            await self.action_connect()
            if not self.protocol:
                return

        direct_input = self.query_one("#direct-input", Input)
        command = direct_input.value.strip()

        if not command:
            return

        await self.protocol.send_direct(command)
        direct_input.value = ""

    # Function key bindings
    async def action_toggle_f0(self) -> None:
        await self.toggle_function(0)

    async def action_toggle_f1(self) -> None:
        await self.toggle_function(1)

    async def action_toggle_f2(self) -> None:
        await self.toggle_function(2)

    async def action_toggle_f3(self) -> None:
        await self.toggle_function(3)

    async def action_toggle_f4(self) -> None:
        await self.toggle_function(4)

    async def action_toggle_f5(self) -> None:
        await self.toggle_function(5)

    async def action_toggle_f6(self) -> None:
        await self.toggle_function(6)

    async def action_toggle_f7(self) -> None:
        await self.toggle_function(7)

    async def action_toggle_f8(self) -> None:
        await self.toggle_function(8)

    async def action_toggle_f9(self) -> None:
        await self.toggle_function(9)

    async def action_toggle_f10(self) -> None:
        await self.toggle_function(10)

    async def action_toggle_f11(self) -> None:
        await self.toggle_function(11)

    # Helper methods

    def update_loco_address_display(self) -> None:
        """Update loco address display in connection panel."""
        loco_addr_display = self.query_one("#loco-address-display", Static)
        if self.state.current_loco:
            loco_addr_display.update(f"Loco Address: {self.state.current_loco.address}")
        else:
            loco_addr_display.update("Loco Address: N/A")

    def update_speed_display(self) -> None:
        """Update speed display."""
        dir_str = "FWD" if self.current_direction == Direction.FORWARD else "REV"
        speed_display = self.query_one("#speed-display", Static)
        speed_display.update(
            f"Speed: {self.current_speed}\n"
            f"Direction: {dir_str}"
        )

    async def log_message(self, direction: str, message: str) -> None:
        """Log a message to the debug console."""
        debug_log = self.query_one("#debug-log", RichLog)
        timestamp = get_timestamp()

        if direction == "S":
            formatted = f"[cyan]{timestamp} [S] <{message}>[/cyan]"
        elif direction == "R":
            formatted = f"[green]{timestamp} [R] {message}[/green]"
        else:
            formatted = f"{timestamp} {message}"

        debug_log.write(formatted)

    async def on_unmount(self) -> None:
        """Handle unmount event - cleanup."""
        if self.protocol:
            await self.protocol.disconnect()
