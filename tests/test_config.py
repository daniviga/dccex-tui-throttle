"""
Tests for dccex_throttle.config module.
"""
import pytest
from pathlib import Path
from dccex_throttle.config import Config, DEFAULT_CONFIG


class TestConfig:
    """Tests for Config class."""

    def test_default_config_structure(self):
        """Test DEFAULT_CONFIG has all required sections."""
        assert 'connection' in DEFAULT_CONFIG
        assert 'ui' in DEFAULT_CONFIG
        assert 'throttle' in DEFAULT_CONFIG

    def test_default_connection_config(self):
        """Test default connection configuration."""
        assert DEFAULT_CONFIG['connection']['host'] == 'localhost'
        assert DEFAULT_CONFIG['connection']['port'] == 2560
        assert DEFAULT_CONFIG['connection']['auto_connect'] is False

    def test_config_initialization_no_file(self, temp_config_dir):
        """Test initializing config without existing file."""
        config_path = temp_config_dir / "config.toml"
        config = Config(config_path)
        assert config.config_path == config_path
        assert config.config == DEFAULT_CONFIG

    def test_config_get(self, temp_config_dir):
        """Test getting configuration values."""
        config = Config(temp_config_dir / "config.toml")
        assert config.get('connection', 'host') == 'localhost'
        assert config.get('connection', 'port') == 2560
        assert config.get('throttle', 'max_speed') == 126

    def test_config_get_with_default(self, temp_config_dir):
        """Test getting non-existent value with default."""
        config = Config(temp_config_dir / "config.toml")
        assert config.get('connection', 'nonexistent', 'default') == 'default'

    def test_config_set(self, temp_config_dir):
        """Test setting configuration values."""
        config = Config(temp_config_dir / "config.toml")
        config.set('connection', 'host', '192.168.1.100')
        assert config.get('connection', 'host') == '192.168.1.100'

    def test_config_set_new_section(self, temp_config_dir):
        """Test setting value in new section."""
        config = Config(temp_config_dir / "config.toml")
        config.set('new_section', 'new_key', 'new_value')
        assert config.get('new_section', 'new_key') == 'new_value'

    def test_get_connection_config(self, temp_config_dir):
        """Test getting connection configuration."""
        config = Config(temp_config_dir / "config.toml")
        conn_config = config.get_connection_config()
        assert isinstance(conn_config, dict)
        assert 'host' in conn_config
        assert 'port' in conn_config

    def test_get_ui_config(self, temp_config_dir):
        """Test getting UI configuration."""
        config = Config(temp_config_dir / "config.toml")
        ui_config = config.get_ui_config()
        assert isinstance(ui_config, dict)
        assert 'theme' in ui_config

    def test_get_throttle_config(self, temp_config_dir):
        """Test getting throttle configuration."""
        config = Config(temp_config_dir / "config.toml")
        throttle_config = config.get_throttle_config()
        assert isinstance(throttle_config, dict)
        assert 'speed_step' in throttle_config
        assert 'max_speed' in throttle_config

    def test_config_save_and_load(self, temp_config_dir):
        """Test saving and loading configuration."""
        config_path = temp_config_dir / "config.toml"
        
        # Create and modify config
        config1 = Config(config_path)
        config1.set('connection', 'host', '192.168.1.200')
        config1.set('throttle', 'speed_step', 5)
        config1.save()
        
        # Load in new instance
        config2 = Config(config_path)
        assert config2.get('connection', 'host') == '192.168.1.200'
        assert config2.get('throttle', 'speed_step') == 5

    def test_update_from_args(self, temp_config_dir):
        """Test updating config from command-line arguments."""
        config = Config(temp_config_dir / "config.toml")
        
        # Mock args object
        class Args:
            host = '10.0.0.1'
            port = 3000
        
        args = Args()
        config.update_from_args(args)
        
        assert config.get('connection', 'host') == '10.0.0.1'
        assert config.get('connection', 'port') == 3000

    def test_update_from_args_partial(self, temp_config_dir):
        """Test updating config with partial args."""
        config = Config(temp_config_dir / "config.toml")
        
        # Mock args with only host
        class Args:
            host = '172.16.0.1'
        
        args = Args()
        config.update_from_args(args)
        
        assert config.get('connection', 'host') == '172.16.0.1'
        # Port should remain default
        assert config.get('connection', 'port') == 2560
