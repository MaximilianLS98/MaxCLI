"""
Unit tests for the maxcli.config module.

This module tests all configuration management functionality including:
- Configuration directory management
- Config file loading and saving
- Initialization state checking
- Configuration value retrieval
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from typing import Dict, Any

import pytest

from maxcli.config import (
    ensure_config_dir,
    load_config,
    save_config,
    is_initialized,
    get_config_value,
    get_quota_project_mappings,
    CONFIG_FILE,
    CONFIG_DIR
)


class TestConfigDirectoryManagement:
    """Test configuration directory creation and management."""
    
    @patch('maxcli.config.CONFIG_DIR')
    def test_ensure_config_dir_creates_directory(self, mock_config_dir):
        """Test that ensure_config_dir creates the directory if it doesn't exist."""
        mock_path = MagicMock()
        mock_config_dir.mkdir = mock_path
        
        ensure_config_dir()
        
        mock_path.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch('maxcli.config.CONFIG_DIR')
    def test_ensure_config_dir_permission_error(self, mock_config_dir):
        """Test that ensure_config_dir handles permission errors gracefully."""
        mock_config_dir.mkdir.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(PermissionError):
            ensure_config_dir()


class TestConfigLoading:
    """Test configuration file loading functionality."""
    
    @patch('maxcli.config.CONFIG_FILE')
    def test_load_config_file_exists(self, mock_config_file):
        """Test loading configuration when file exists."""
        test_config = {"user": "test_user", "setting": "value"}
        mock_config_file.exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            result = load_config()
            
        assert result == test_config
    
    @patch('maxcli.config.CONFIG_FILE')
    def test_load_config_file_not_exists(self, mock_config_file):
        """Test loading configuration when file doesn't exist."""
        mock_config_file.exists.return_value = False
        
        result = load_config()
        
        assert result == {}
    
    @patch('maxcli.config.CONFIG_FILE')
    def test_load_config_invalid_json(self, mock_config_file, capsys):
        """Test loading configuration with invalid JSON content."""
        mock_config_file.exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data="invalid json")):
            result = load_config()
            
            # Should return empty dict and print warning
            assert result == {}
            captured = capsys.readouterr()
            assert "⚠️ Warning: Could not load config file" in captured.out
    
    @patch('maxcli.config.CONFIG_FILE')
    def test_load_config_permission_error(self, mock_config_file, capsys):
        """Test loading configuration with permission error."""
        mock_config_file.exists.return_value = True
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = load_config()
            
            # Should return empty dict and print warning
            assert result == {}
            captured = capsys.readouterr()
            assert "⚠️ Warning: Could not load config file" in captured.out


class TestConfigSaving:
    """Test configuration file saving functionality."""
    
    def test_save_config_success(self):
        """Test saving configuration successfully."""
        test_config = {"user": "test_user", "setting": "value"}
        
        with patch('maxcli.config.ensure_config_dir') as mock_ensure_dir:
            with patch('builtins.open', mock_open()) as mock_file:
                result = save_config(test_config)
                
                assert result is True
                mock_ensure_dir.assert_called_once()
                mock_file.assert_called_once_with(CONFIG_FILE, 'w')
    
    def test_save_config_empty_dict(self):
        """Test saving empty configuration."""
        with patch('maxcli.config.ensure_config_dir'):
            with patch('builtins.open', mock_open()) as mock_file:
                result = save_config({})
                
                assert result is True
                mock_file.assert_called_once_with(CONFIG_FILE, 'w')
    
    def test_save_config_permission_error(self, capsys):
        """Test saving configuration with permission error."""
        with patch('maxcli.config.ensure_config_dir'):
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                result = save_config({"test": "value"})
                
                # Should return False and print error message
                assert result is False
                captured = capsys.readouterr()
                assert "❌ Error saving config" in captured.out


class TestInitializationChecks:
    """Test configuration initialization state checking."""
    
    def test_is_initialized_true(self):
        """Test is_initialized returns True when required fields exist."""
        test_config = {"git_name": "test", "git_email": "test@example.com"}
        
        with patch('maxcli.config.load_config', return_value=test_config):
            assert is_initialized() is True
    
    def test_is_initialized_false_missing_fields(self):
        """Test is_initialized returns False when required fields are missing."""
        test_config = {"git_name": "test"}  # Missing git_email
        
        with patch('maxcli.config.load_config', return_value=test_config):
            assert is_initialized() is False
    
    def test_is_initialized_false_empty_config(self):
        """Test is_initialized returns False when config is empty."""
        with patch('maxcli.config.load_config', return_value={}):
            assert is_initialized() is False
    
    def test_is_initialized_false_empty_values(self):
        """Test is_initialized returns False when required fields are empty."""
        test_config = {"git_name": "", "git_email": "test@example.com"}
        
        with patch('maxcli.config.load_config', return_value=test_config):
            assert is_initialized() is False


class TestConfigValueRetrieval:
    """Test configuration value retrieval functionality."""
    
    def test_get_config_value_exists(self):
        """Test getting a configuration value that exists."""
        test_config = {"user": "test_user", "setting": "value"}
        
        with patch('maxcli.config.load_config', return_value=test_config):
            result = get_config_value("user")
            assert result == "test_user"
    
    def test_get_config_value_not_exists_no_default(self):
        """Test getting a configuration value that doesn't exist without default."""
        test_config = {"user": "test_user"}
        
        with patch('maxcli.config.load_config', return_value=test_config):
            result = get_config_value("missing_key")
            assert result is None
    
    def test_get_config_value_not_exists_with_default(self):
        """Test getting a configuration value that doesn't exist with default."""
        test_config = {"user": "test_user"}
        
        with patch('maxcli.config.load_config', return_value=test_config):
            result = get_config_value("missing_key", "default_value")
            assert result == "default_value"
    
    def test_get_config_value_nested_key(self):
        """Test getting a nested configuration value."""
        test_config = {"database": {"host": "localhost", "port": 5432}}
        
        with patch('maxcli.config.load_config', return_value=test_config):
            result = get_config_value("database")
            assert result == {"host": "localhost", "port": 5432}
    
    def test_get_quota_project_mappings(self):
        """Test getting quota project mappings."""
        test_config = {
            "quota_project_mappings": {
                "dev": "project-dev-123",
                "prod": "project-prod-456"
            }
        }
        
        with patch('maxcli.config.load_config', return_value=test_config):
            result = get_quota_project_mappings()
            assert result == {"dev": "project-dev-123", "prod": "project-prod-456"}
    
    def test_get_quota_project_mappings_empty(self):
        """Test getting quota project mappings when not configured."""
        with patch('maxcli.config.load_config', return_value={}):
            result = get_quota_project_mappings()
            assert result == {}


class TestConfigConstants:
    """Test configuration constants and paths."""
    
    def test_config_dir_path(self):
        """Test that CONFIG_DIR is properly set."""
        assert CONFIG_DIR is not None
        assert isinstance(CONFIG_DIR, Path)
        assert str(CONFIG_DIR).endswith(".config/maxcli")
    
    def test_config_file_path(self):
        """Test that CONFIG_FILE is properly set."""
        assert CONFIG_FILE is not None
        assert isinstance(CONFIG_FILE, Path)
        assert CONFIG_FILE.name == "config.json"
        assert CONFIG_FILE.parent == CONFIG_DIR


class TestConfigIntegration:
    """Integration tests for configuration functionality."""
    
    @patch('maxcli.config.CONFIG_FILE')
    def test_save_and_load_workflow(self, mock_config_file):
        """Test basic save and load workflow."""
        test_config = {
            "git_name": "Test User",
            "git_email": "test@example.com",
            "coolify_api_key": "test-key"
        }
        
        # Test saving
        with patch('maxcli.config.ensure_config_dir'):
            with patch('builtins.open', mock_open()) as mock_file:
                result = save_config(test_config)
                assert result is True
        
        # Test loading  
        mock_config_file.exists.return_value = True
        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            loaded_config = load_config()
            assert loaded_config == test_config
        
        # Test config value retrieval
        with patch('maxcli.config.load_config', return_value=test_config):
            git_name = get_config_value("git_name")
            assert git_name == "Test User"
            
            # Test initialization check
            assert is_initialized() is True
    
    def test_error_handling_workflow(self, capsys):
        """Test error handling in configuration workflow."""
        # Test load with invalid JSON
        with patch('maxcli.config.CONFIG_FILE') as mock_config_file:
            mock_config_file.exists.return_value = True
            with patch('builtins.open', mock_open(read_data="invalid json")):
                result = load_config()
                assert result == {}
                
                captured = capsys.readouterr()
                assert "⚠️ Warning: Could not load config file" in captured.out
        
        # Test save with permission error
        with patch('maxcli.config.ensure_config_dir'):
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                result = save_config({"test": "value"})
                assert result is False
                
                captured = capsys.readouterr()
                assert "❌ Error saving config" in captured.out 