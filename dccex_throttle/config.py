"""
Configuration management for DCC-EX Throttle TUI application.
"""
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Handle Python 3.11+ built-in tomllib vs older tomli package
if sys.version_info >= (3, 11):
    import tomllib

    def load_toml(path: Path) -> Dict[str, Any]:
        with open(path, 'rb') as f:
            return tomllib.load(f)
else:
    import tomli

    def load_toml(path: Path) -> Dict[str, Any]:
        with open(path, 'rb') as f:
            return tomli.load(f)


DEFAULT_CONFIG = {
    'connection': {
        'host': 'localhost',
        'port': 2560,
        'auto_connect': False,
        'reconnect_delay': 5,
        'timeout': 10,
    },
    'ui': {
        'theme': 'dark',
        'show_debug_console': True,
        'max_log_lines': 100,
        'show_extended_functions': False,
    },
    'throttle': {
        'default_loco_address': 3,
        'speed_step': 1,
        'max_speed': 126,
    }
}


class Config:
    """Configuration manager for DCC-EX Throttle."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()

        if self.config_path.exists():
            self.load()

    @staticmethod
    def _get_default_config_path() -> Path:
        """Get default configuration file path."""
        # Try to use user's home directory
        home = Path.home()
        config_dir = home / '.config' / 'dccex_throttle'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.toml'

    def load(self):
        """Load configuration from TOML file."""
        try:
            loaded_config = load_toml(self.config_path)
            # Merge with defaults (preserve any new defaults not in file)
            self._merge_config(loaded_config)
        except Exception as e:
            print(
                f"Warning: Could not load config from {self.config_path}: {e}"
            )
            print("Using default configuration.")

    def _merge_config(self, loaded: Dict[str, Any]):
        """Merge loaded config with defaults."""
        for section, values in loaded.items():
            if section in self.config and isinstance(values, dict):
                self.config[section].update(values)
            else:
                self.config[section] = values

    def save(self):
        """Save configuration to TOML file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write TOML file manually (tomli is read-only)
            with open(self.config_path, 'w') as f:
                self._write_toml(f, self.config)
        except Exception as e:
            print(f"Error saving config to {self.config_path}: {e}")

    def _write_toml(self, f, config: Dict[str, Any]):
        """Write configuration to TOML format."""
        for section, values in config.items():
            f.write(f"[{section}]\n")
            for key, value in values.items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                elif isinstance(value, bool):
                    f.write(f'{key} = {str(value).lower()}\n')
                else:
                    f.write(f'{key} = {value}\n')
            f.write('\n')

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        """Set configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def get_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration."""
        return self.config.get('connection', {})

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return self.config.get('ui', {})

    def get_throttle_config(self) -> Dict[str, Any]:
        """Get throttle configuration."""
        return self.config.get('throttle', {})

    def update_from_args(self, args):
        """Update configuration from command-line arguments."""
        if hasattr(args, 'host') and args.host:
            self.set('connection', 'host', args.host)
        if hasattr(args, 'port') and args.port:
            self.set('connection', 'port', args.port)
