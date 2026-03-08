# Multi-Throttle Operation Example

This document demonstrates how the DCC-EX Throttle TUI handles multi-throttle scenarios through continuous broadcast listening.

## Scenario: Two Throttles Controlling the Same Locomotive

### Setup
- **Throttle A**: DCC-EX Throttle TUI (this application)
- **Throttle B**: WebThrottle-EX in a browser
- **Locomotive**: DCC Address 3
- **Command Station**: DCC-EX on 192.168.1.100:2560

## Sequence of Events

### 1. Initial Connection (Throttle A)

```bash
$ python -m dccex_throttle --host 192.168.1.100

# In the TUI:
[S] <s>                          # Status request
[R] <iDCC-EX V-5.0.0 ...>       # Command station responds
[S] Connected successfully
```

### 2. Acquire Locomotive (Throttle A)

```
User enters: 3
[S] <t 3>                        # Request loco info
[S] Acquired loco 3
[R] <l 3 128 1 0>               # Current state: stopped, forward
```

### 3. Set Speed (Throttle A)

```
User presses ↑ (increase speed)
[S] <t 3 50 1>                  # Send speed 50, forward
[R] <l 3 179 1 0>               # CS broadcasts new state
```

**Speedbyte calculation**: Forward + Speed 50 = 129 + 50 = 179

### 4. Another Throttle Connects (Throttle B)

WebThrottle-EX connects to the same Command Station and acquires loco 3.

### 5. Throttle B Changes Speed

Throttle B (WebThrottle) sets speed to 75:

```
[R] <l 3 204 1 0>               # Broadcast from Command Station

# Throttle A automatically updates:
Speed Display: "Speed: 75, Direction: FWD"
[S] Updated loco 3 from broadcast (Speed: 75, Dir: FWD)
```

**Throttle A didn't send this command, but it received and processed the broadcast!**

### 6. Throttle B Toggles Function F0 (Lights)

```
[R] <l 3 204 1 1>               # Function bit 0 is now set

# Throttle A updates function button:
F0 button changes from gray to green
[S] Updated loco 3 from broadcast (Speed: 75, Dir: FWD)
```

### 7. Throttle A Changes Direction

```
User presses ← (reverse)
[S] <t 3 75 0>                  # Send speed 75, reverse
[R] <l 3 76 0 1>                # CS broadcasts: 1 + 75 = 76

# Both throttles now show:
Speed: 75, Direction: REV, F0: ON
```

### 8. Throttle B Emergency Stops

```
[R] <l 3 0 0 1>                 # Speed 0, reverse, F0 still on

# Throttle A immediately shows:
Speed Display: "Speed: 0, Direction: REV"
[S] Updated loco 3 from broadcast (Speed: 0, Dir: REV)
```

### 9. Power Toggle from Any Source

If anyone turns off track power:

```
[R] <p0>                        # Power off broadcast

# Throttle A updates:
Power Status: "Power: OFF"
Power Switch: Toggles to OFF position
```

## Technical Details

### Speedbyte Encoding

The DCC-EX protocol uses a "speedbyte" that combines speed and direction:

| Speedbyte | Meaning |
|-----------|---------|
| 0 | Stop (direction: reverse) |
| 1-127 | Reverse (speed = speedbyte - 1) |
| 128 | Stop (direction: forward) |
| 129-255 | Forward (speed = speedbyte - 129) |

Examples:
- Speedbyte 76 = Reverse at speed 75 (76 - 1)
- Speedbyte 179 = Forward at speed 50 (179 - 129)
- Speedbyte 204 = Forward at speed 75 (204 - 129)

### Function Bits

Functions are encoded as a 32-bit integer where each bit represents a function state:

```
Bit 0 = F0 (lights)
Bit 1 = F1 (bell)
Bit 2 = F2 (horn)
...
Bit 31 = F31
```

Example: `functions = 1` means F0 is ON, all others OFF
Example: `functions = 7` (binary: 111) means F0, F1, F2 are ON

### Broadcast Message Format

```
<l LOCO SPEEDBYTE DIR FUNCTIONS>
   │    │         │    └─ 32-bit function state
   │    │         └─ Direction (redundant, encoded in speedbyte)
   │    └─ Speed + direction combined
   └─ Locomotive DCC address
```

## Benefits of Broadcast Listening

1. **Seamless Multi-Throttle Operation**: Multiple controllers work together naturally
2. **Real-Time Sync**: No polling needed, updates are instant
3. **Consistent State**: All throttles show the same locomotive state
4. **Flexible Control**: Switch between throttles without conflicts
5. **Better UX**: User sees changes from other sources immediately

## Supported Broadcasts

The throttle currently listens for and handles:

- ✅ **Locomotive state** (`<l>`) - Speed, direction, functions
- ✅ **Power state** (`<p>`) - Track power on/off
- ✅ **Command station info** (`<i>`) - Version, status
- ⏳ **Turnout state** (`<H>`) - Parsed but not displayed (future feature)

## Testing Multi-Throttle Operation

### Quick Test

1. Start this TUI throttle:
   ```bash
   python -m dccex_throttle --host <your-cs-ip>
   ```

2. Open WebThrottle-EX in a browser:
   ```
   https://dcc-ex.com/WebThrottle-EX/
   ```

3. Connect both to the same Command Station

4. Acquire the same locomotive in both throttles

5. Control from either throttle and watch the other update automatically!

### Expected Behavior

- ✅ Speed changes in one throttle appear immediately in the other
- ✅ Direction changes sync across throttles
- ✅ Function buttons update when toggled from other throttle
- ✅ Power state changes reflect everywhere
- ✅ Emergency stop from any throttle stops the loco everywhere

### Debugging

Enable debug mode to see all broadcast messages:

```bash
python -m dccex_throttle --debug --log-file throttle.log
```

Watch the log file:
```bash
tail -f throttle.log
```

You'll see entries like:
```
[R] <l 3 179 1 0>
[S] Updated loco 3 from broadcast (Speed: 50, Dir: FWD)
```

## Conclusion

The broadcast listening feature makes the DCC-EX Throttle TUI a true multi-throttle citizen, working seamlessly alongside other control methods. This is essential for modern model railroad operations where operators may use a mix of hardware throttles, web throttles, and computer applications.
