# DCC-EX Throttle TUI

A modern Python Terminal User Interface (TUI) application for controlling model trains through a DCC-EX Command Station. Built with [Textual](https://textual.textualize.io/), this throttle provides a feature-rich interface for locomotive control over TCP socket connection.

## Features

### Core Throttle Controls
- **Locomotive Management**: Simple address-based acquisition and release
- **Speed Control**: Adjustable speed (0-126) with keyboard shortcuts and buttons
- **Direction Control**: Forward/Reverse with quick toggle and visual feedback
- **Function Control**: All 32 functions (F0-F31) with visual feedback
  - F0-F11 always visible in first row
  - F12-F31 always visible below
- **Track Power**: Easy on/off toggle with visual feedback
- **Emergency Stop**: Instant stop for all locomotives
- **Direct Commands**: Send raw DCC-EX commands for advanced control
- **Debug Console**: Real-time command logging (sent/received)
- **Broadcast Listening**: Automatically updates when other throttles control the same locomotive
  - Speed sync with display update
  - Direction sync with button visual feedback
  - Function state sync with button visual feedback
  - Multi-throttle support (WebThrottle-EX, JMRI, hardware throttles)

### User Interface
- Clean, organized terminal-based layout
- Keyboard shortcuts for common operations
- Visual feedback for function AND direction button states
- Connection status display
- Responsive design
- Real-time updates from Command Station broadcasts

## Requirements

- Python 3.11+ (or 3.9+ with `tomli` package)
- DCC-EX Command Station with TCP server enabled (port 2560)
- Terminal with color support

## Installation

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install manually
pip install textual tomli  # tomli only needed for Python <3.11

# Run the application
python -m dccex_throttle
```

## Usage

### Basic Usage

```bash
# Run with default settings (localhost:2560)
python -m dccex_throttle

# Connect to a specific Command Station
python -m dccex_throttle --host 192.168.1.100 --port 2560

# Use a custom configuration file
python -m dccex_throttle --config /path/to/config.toml

# Enable debug logging
python -m dccex_throttle --debug --log-file throttle.log
```

### Configuration

The application uses a TOML configuration file. On first run, it creates a default configuration at:
- Linux/Mac: `~/.config/dccex_throttle/config.toml`
- Windows: `%USERPROFILE%\.config\dccex_throttle\config.toml`

You can also copy and customize the example configuration:

```bash
cp dccex_throttle/config.toml.example ~/.config/dccex_throttle/config.toml
```

Example configuration:

```toml
[connection]
host = "localhost"
port = 2560
auto_connect = false
reconnect_delay = 5
timeout = 10

[ui]
theme = "dark"
show_debug_console = true
max_log_lines = 100

[throttle]
default_loco_address = 3
speed_step = 1
max_speed = 126
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` / `Ctrl+Q` | Quit application |
| `Ctrl+P` | Toggle track power |
| `Ctrl+S` | Emergency stop |
| `↑` | Increase speed |
| `↓` | Decrease speed |
| `←` | Set direction to reverse |
| `→` | Set direction to forward |
| `F1` - `F12` | Toggle functions F0-F11 |
| `Enter` (in loco input) | Acquire locomotive |
| `Enter` (in direct command) | Send command |

### Operation

1. **Connect to Command Station**
   - The app will attempt to connect on startup (if `auto_connect = true`)
   - Or connection happens automatically when you acquire a loco

2. **Acquire a Locomotive**
   - Enter the DCC address in the "Loco Address" field
   - Press Enter or click "Acquire"
   - Valid addresses: 1-10239

3. **Control Speed**
   - Use ↑/↓ arrow keys or +/- buttons
   - Speed range: 0-126
   - Configurable speed step (default: 1)

4. **Change Direction**
   - Use ←/→ arrow keys or direction buttons
   - Direction changes are sent immediately

5. **Toggle Functions**
   - Click function buttons (F0-F31)
   - Use F1-F12 keys for quick access to F0-F11
   - Active functions show in green

6. **Track Power**
   - Toggle with Ctrl+P or the power switch
   - Status displayed at top of screen

7. **Emergency Stop**
   - Press Ctrl+S or click "E-STOP" button
   - Stops ALL locomotives on the track

8. **Direct Commands**
   - Enter DCC-EX commands in the direct command field
   - Commands are automatically wrapped in `<>` brackets
   - Example: Enter `s` to send `<s>` (status request)

## Multi-Throttle Support

This throttle supports multi-throttle operation by **continuously listening to broadcast messages** from the Command Station. This means:

- **Multiple throttles can control the same locomotive** - If another throttle (web, hardware, or another TUI instance) controls your locomotive, this throttle will automatically update to reflect the changes
- **Real-time synchronization** - Speed, direction, and function states are updated in real-time when broadcast messages are received
- **Visual feedback** - The UI immediately reflects changes made by other controllers
- **No conflicts** - All commands are sent through the Command Station, which manages the actual DCC packets

### How It Works

1. The throttle maintains a persistent TCP connection to the Command Station
2. The Command Station broadcasts state updates for all locomotives: `<l LOCO SPEEDBYTE DIR FUNCTIONS>`
3. When a broadcast is received for your acquired locomotive, the UI automatically updates
4. This works seamlessly whether commands come from:
   - This throttle
   - Another TUI throttle instance
   - WebThrottle-EX in a browser
   - JMRI or other DCC-EX throttle software
   - Hardware throttles connected to the Command Station

### Example Multi-Throttle Scenario

```
Throttle A (this TUI): Acquires loco 3, sets speed to 50
Command Station: Broadcasts <l 3 179 1 0>
Throttle B (WebThrottle): Also controlling loco 3, sees speed update
Throttle B: Changes speed to 75
Command Station: Broadcasts <l 3 204 1 0>
Throttle A (this TUI): Automatically updates to show speed 75
```

This ensures a consistent experience across all throttles controlling the same locomotive.

## DCC-EX Protocol Reference

The application communicates with the DCC-EX Command Station using the native protocol:

### Commands Sent
- `<t LOCO SPEED DIR>` - Throttle control (speed: 0-126, dir: 0=reverse, 1=forward)
- `<F LOCO FUNCTION STATE>` - Function control (function: 0-31, state: 0/1)
- `<1>` - Track power on
- `<0>` - Track power off
- `<s>` - Status request
- `<!>` - Emergency stop all locomotives

### Responses Parsed
- `<p0>` / `<p1>` - Track power state (0=off, 1=on)
- `<l LOCO SPEEDBYTE DIR FUNCTIONS>` - Locomotive state update (broadcast)
- `<iDCC-EX ...>` - Command station information
- `<H ID STATE>` - Turnout state (for future enhancement)

### Broadcast Message Handling

The throttle continuously listens for broadcast messages and automatically updates the UI when:
- **Locomotive state changes** (`<l>`) - Speed, direction, and function updates
- **Power state changes** (`<p>`) - Track power on/off
- **Command station events** - Status and information updates

This enables seamless multi-throttle operation where multiple controllers can work together without conflicts.

For a complete protocol reference, see: [DCC-EX Command Reference](https://dcc-ex.com/reference/software/command-reference.html)

## Architecture

```
dccex_throttle/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point with argument parsing
├── config.py            # Configuration management (TOML)
├── models.py            # Data models (Locomotive, ThrottleState)
├── protocol.py          # DCC-EX TCP protocol implementation
├── ui.py                # Textual UI components and app
├── utils.py             # Utility functions
└── config.toml.example  # Example configuration
```

### Key Components

- **DCCEXProtocol**: Async TCP socket communication with Command Station
- **DCCEXThrottleApp**: Main Textual application with UI layout
- **Locomotive**: Data model for locomotive state (speed, direction, functions)
- **ThrottleState**: Global application state
- **Config**: TOML-based configuration management

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Command Station
- Verify the Command Station is running and accessible
- Check host and port configuration
- Ensure TCP server is enabled on the Command Station (port 2560)
- Test with: `telnet <host> 2560` or `nc <host> 2560`

**Problem**: Connection drops unexpectedly
- Check network stability
- Verify Command Station is not overloaded
- Increase `timeout` in configuration

### Locomotive Control Issues

**Problem**: Locomotive doesn't respond
- Verify track power is ON (toggle with Ctrl+P)
- Check correct DCC address is entered
- Ensure locomotive decoder is properly programmed
- Try sending status command `<s>` in direct command field

**Problem**: Functions not working
- Some decoders don't support all 32 functions
- Check decoder documentation for supported functions
- Verify function mapping in decoder CVs

### UI Issues

**Problem**: UI looks corrupted or displays incorrectly
- Ensure terminal supports color and Unicode
- Try resizing terminal window
- Use a modern terminal emulator (kitty, iTerm2, Windows Terminal, etc.)

## Development

### Running Tests

```bash
# TODO: Add tests
# python -m pytest tests/
```

### Contributing

Contributions are welcome! Please follow these guidelines:
- Follow PEP 8 style guide (79 character line length)
- Use type hints where appropriate
- Add docstrings to functions and classes
- Test with real DCC-EX hardware when possible

## Related Projects

- **DCC-EX**: Open-source DCC Command Station - https://dcc-ex.com
- **WebThrottle-EX**: Browser-based throttle - https://github.com/DCC-EX/WebThrottle-EX
- **Django-RAM**: Railroad Assets Manager - https://github.com/daniviga/django-ram
- **Textual**: Python TUI framework - https://textual.textualize.io

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

## Credits

- DCC-EX Project Team
- Django-RAM Contributors
- Textual Framework by Textualize

## Version

**Version**: 1.0.0  
**Author**: DCC-EX Throttle TUI Contributors  
**Python**: 3.11+ (or 3.9+ with tomli)
