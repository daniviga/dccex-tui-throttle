# DCC-EX Throttle TUI - Quick Start Guide

## Installation

```bash
# From the django-ram/ram directory
cd ram

# Install dependencies
pip install -r requirements-throttle.txt

# Verify installation
python -m dccex_throttle --version
```

## First Run

```bash
# Run with default settings (connects to localhost:2560)
python -m dccex_throttle

# Or specify your Command Station address
python -m dccex_throttle --host 192.168.1.100 --port 2560
```

## Basic Operation

1. **Start the application** - The TUI will launch in your terminal
2. **Enter loco address** - Type the DCC address in the "Loco Address" field
3. **Press Enter or click "Acquire"** - The app will connect (if not already connected) and acquire the loco
4. **Turn on track power** - Press `Ctrl+P` or toggle the power switch
5. **Control your locomotive**:
   - `↑/↓` arrows to adjust speed
   - `←/→` arrows to change direction
   - `F1-F12` keys for functions F0-F11
   - Click function buttons for all F0-F31 functions
   - `Ctrl+S` for emergency stop

## Essential Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Quit |
| `Ctrl+P` | Toggle track power |
| `Ctrl+S` | Emergency stop |
| `↑` / `↓` | Speed up/down |
| `←` / `→` | Reverse/Forward |
| `F1-F12` | Toggle functions |

## Configuration

Edit `~/.config/dccex_throttle/config.toml`:

```toml
[connection]
host = "192.168.1.100"  # Your Command Station IP
port = 2560
auto_connect = true      # Auto-connect on startup

[throttle]
speed_step = 1          # Speed increment per key press
```

## Troubleshooting

### Cannot connect
- Check Command Station IP and port
- Verify TCP server is enabled on Command Station
- Test with: `telnet <host> 2560`

### Loco doesn't move
- Ensure track power is ON (Ctrl+P)
- Check correct DCC address
- Verify locomotive is on the track

### Functions don't work
- Check decoder documentation for supported functions
- Not all decoders support all 32 functions

## Getting Help

- See full documentation in `README.md`
- DCC-EX documentation: https://dcc-ex.com
- Report issues at: https://github.com/daniviga/django-ram

## Example Session

```bash
# Start throttle
$ python -m dccex_throttle --host 192.168.1.100

# In the TUI:
1. Type loco address: 3
2. Press Enter to acquire
3. Press Ctrl+P to turn on power
4. Press ↑ to increase speed
5. Press F1 for lights (F0)
6. Press F2 for bell (F1)
7. Control your train!
```

Enjoy controlling your model railroad! 🚂
