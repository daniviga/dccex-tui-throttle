"""
DCC-EX Throttle TUI - Entry point
"""

import argparse
import sys
from pathlib import Path

from .config import Config
from .ui import DCCEXThrottleApp
from .utils import setup_logging


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="DCC-EX Throttle TUI - Control your model trains",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python -m dccex_throttle

  # Connect to a specific Command Station
  python -m dccex_throttle --host 192.168.1.100 --port 2560

  # Use a custom configuration file
  python -m dccex_throttle --config /path/to/config.toml

  # Enable debug logging
  python -m dccex_throttle --debug
        """,
    )

    parser.add_argument(
        "--host", type=str, help="DCC-EX Command Station host address"
    )

    parser.add_argument(
        "--port", type=int, help="DCC-EX Command Station port (default: 2560)"
    )

    parser.add_argument(
        "--config", type=str, help="Path to configuration file"
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )

    parser.add_argument("--log-file", type=str, help="Log file path")

    parser.add_argument(
        "--version", action="version", version="DCC-EX Throttle TUI v1.0.0"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    import logging

    log_level = logging.DEBUG if args.debug else logging.INFO
    if args.log_file:
        setup_logging(args.log_file, log_level)

    # Load configuration
    config_path = Path(args.config) if args.config else None
    config = Config(config_path)

    # Update config from command-line arguments
    config.update_from_args(args)

    # Create and run the application
    app = DCCEXThrottleApp(config)

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExiting DCC-EX Throttle TUI...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
