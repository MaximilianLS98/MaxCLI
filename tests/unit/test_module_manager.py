"""
Unit tests for the module manager functionality.

Tests the core module management features including loading, enabling,
disabling modules, and configuration management.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from maxcli.modules.module_manager import (
    load_modules_config,
    save_modules_config,
    get_enabled_modules,
    enable_module,
    disable_module,
    create_config_with_modules,
    update_module_info_if_needed
)
from tests.utils.test_helpers import (
    create_test_config,
    validate_module_config_structure
)


class TestModuleConfigLoading:
    """Test module configuration loading functionality."""
    
    def test_load_default_config_when_file_missing(self, cli_test_environment: Dict[str, Any]):
        """Test that default config is created when file doesn't exist."""
        # Remove the config file
        cli_test_environment["modules_config_file"].unlink()
        
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            config = load_modules_config()
        
        # Validate structure
        validate_module_config_structure(config)
        
        # Check default modules are enabled
        assert "ssh_manager" in config["enabled_modules"]
        assert "setup_manager" in config["enabled_modules"]
    
    def test_load_existing_valid_config(self, cli_test_environment: Dict[str, Any]):
        """Test loading a valid existing configuration."""
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            config = load_modules_config()
        
        # Should match the sample config
        assert config["enabled_modules"] == ["ssh_manager", "docker_manager"]
        assert config["module_info"]["ssh_manager"]["enabled"] is True
        assert config["module_info"]["docker_manager"]["enabled"] is True
        assert config["module_info"]["kubernetes_manager"]["enabled"] is False
    
    def test_handle_corrupted_config_file(self, cli_test_environment: Dict[str, Any]):
        """Test handling of corrupted JSON configuration file."""
        # Write invalid JSON
        with open(cli_test_environment["modules_config_file"], 'w') as f:
            f.write("{ invalid json")
        
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            config = load_modules_config()
        
        # Should fall back to default config
        validate_module_config_structure(config)
        assert "ssh_manager" in config["enabled_modules"]
    
    def test_legacy_config_conversion(self, cli_test_environment: Dict[str, Any]):
        """Test conversion from legacy boolean flag format to new format."""
        # Create a legacy config with boolean flags
        legacy_config = {
            "ssh_manager": True,
            "docker_manager": False,
            "kubernetes_manager": True
        }
        
        with open(cli_test_environment["modules_config_file"], 'w') as f:
            json.dump(legacy_config, f)
        
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            config = load_modules_config()
        
        # Should be converted to new format
        validate_module_config_structure(config)
        assert "ssh_manager" in config["enabled_modules"]
        assert "kubernetes_manager" in config["enabled_modules"]
        assert "docker_manager" not in config["enabled_modules"]


class TestModuleEnableDisable:
    """Test module enable/disable functionality."""
    
    def test_enable_valid_module(self, cli_test_environment: Dict[str, Any]):
        """Test enabling a valid module."""
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            # Kubernetes is disabled in sample config
            result = enable_module("kubernetes_manager")
            
            assert result is True
            
            # Verify it's now enabled
            config = load_modules_config()
            assert "kubernetes_manager" in config["enabled_modules"]
            assert config["module_info"]["kubernetes_manager"]["enabled"] is True
    
    def test_enable_invalid_module(self, cli_test_environment: Dict[str, Any]):
        """Test enabling a non-existent module."""
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            result = enable_module("nonexistent_module")
            
            assert result is False
    
    def test_enable_already_enabled_module(self, cli_test_environment: Dict[str, Any]):
        """Test enabling an already enabled module."""
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            # SSH manager is enabled in sample config
            result = enable_module("ssh_manager")
            
            assert result is True  # Should succeed even if already enabled
    
    def test_disable_enabled_module(self, cli_test_environment: Dict[str, Any]):
        """Test disabling an enabled module."""
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            # SSH manager is enabled in sample config
            result = disable_module("ssh_manager")
            
            assert result is True
            
            # Verify it's now disabled
            config = load_modules_config()
            assert "ssh_manager" not in config["enabled_modules"]
            assert config["module_info"]["ssh_manager"]["enabled"] is False
    
    def test_disable_already_disabled_module(self, cli_test_environment: Dict[str, Any]):
        """Test disabling an already disabled module."""
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            # Kubernetes is already disabled in sample config
            result = disable_module("kubernetes_manager")
            
            assert result is True  # Should succeed even if already disabled
    
    def test_disable_invalid_module(self, cli_test_environment: Dict[str, Any]):
        """Test disabling a non-existent module."""
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            result = disable_module("nonexistent_module")
            
            assert result is False


class TestConfigCreation:
    """Test configuration creation and update functionality."""
    
    def test_create_config_with_specific_modules(self):
        """Test creating configuration with specific enabled modules."""
        enabled_modules = ["ssh_manager", "docker_manager", "gcp_manager"]
        config = create_config_with_modules(enabled_modules)
        
        validate_module_config_structure(config)
        assert config["enabled_modules"] == enabled_modules
        
        # Check that specified modules are enabled
        for module in enabled_modules:
            assert config["module_info"][module]["enabled"] is True
        
        # Check that other modules are disabled
        all_modules = set(config["module_info"].keys())
        disabled_modules = all_modules - set(enabled_modules)
        for module in disabled_modules:
            assert config["module_info"][module]["enabled"] is False
    
    def test_create_config_with_empty_modules(self):
        """Test creating configuration with no enabled modules."""
        config = create_config_with_modules([])
        
        validate_module_config_structure(config)
        assert config["enabled_modules"] == []
        
        # All modules should be disabled
        for module_data in config["module_info"].values():
            assert module_data["enabled"] is False
    
    def test_update_module_info_preserves_existing_data(self):
        """Test that updating module info preserves existing configuration."""
        # Start with a basic config
        config = {
            "enabled_modules": ["ssh_manager"],
            "module_info": {
                "ssh_manager": {
                    "enabled": True,
                    "description": "Old description",
                    "commands": ["ssh"],
                    "dependencies": ["custom_dependency"]
                }
            }
        }
        
        # Update should preserve custom dependencies while updating description
        modified = update_module_info_if_needed(config)
        
        assert modified is True  # Should have been modified
        assert config["module_info"]["ssh_manager"]["dependencies"] == ["custom_dependency"]
        assert "SSH connection and target management" in config["module_info"]["ssh_manager"]["description"]
    
    def test_update_module_info_adds_missing_modules(self):
        """Test that updating module info adds missing modules."""
        config = {
            "enabled_modules": ["ssh_manager"],
            "module_info": {
                "ssh_manager": {
                    "enabled": True,
                    "description": "SSH management",
                    "commands": ["ssh"],
                    "dependencies": []
                }
            }
        }
        
        modified = update_module_info_if_needed(config)
        
        assert modified is True
        # Should now include all available modules
        assert "docker_manager" in config["module_info"]
        assert "kubernetes_manager" in config["module_info"]
        
        # New modules should be disabled
        assert config["module_info"]["docker_manager"]["enabled"] is False


class TestConfigPersistence:
    """Test configuration file save and load operations."""
    
    def test_save_and_load_config_roundtrip(self, cli_test_environment: Dict[str, Any]):
        """Test that saving and loading config preserves all data."""
        original_config = create_test_config(["ssh_manager", "coolify_manager"])
        
        with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
                  cli_test_environment["modules_config_file"]):
            # Save the config
            result = save_modules_config(original_config)
            assert result is True
            
            # Load it back
            loaded_config = load_modules_config()
            
            # Should be identical
            assert loaded_config["enabled_modules"] == original_config["enabled_modules"]
            assert loaded_config["module_info"] == original_config["module_info"]
    
    def test_save_config_creates_directory(self, temp_config_dir: Path):
        """Test that saving config creates the directory if it doesn't exist."""
        # Remove the config directory
        config_dir = temp_config_dir
        config_dir.rmdir()
        
        config_file = config_dir / "max_modules.json"
        config = create_test_config(["ssh_manager"])
        
        # Patch both CONFIG_DIR and MODULES_CONFIG_FILE
        with patch('maxcli.modules.module_manager.CONFIG_DIR', config_dir), \
             patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', config_file):
            result = save_modules_config(config)
            
            assert result is True
            assert config_file.exists()
            assert config_dir.exists()


@pytest.mark.parametrize("enabled_modules,expected_count", [
    ([], 0),
    (["ssh_manager"], 1),
    (["ssh_manager", "docker_manager"], 2),
    (["ssh_manager", "docker_manager", "kubernetes_manager"], 3),
])
def test_get_enabled_modules_count(enabled_modules, expected_count, cli_test_environment):
    """Test getting enabled modules with various configurations."""
    # Create custom config
    config = create_test_config(enabled_modules)
    
    # Save to test environment
    with open(cli_test_environment["modules_config_file"], 'w') as f:
        json.dump(config, f)
    
    with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
              cli_test_environment["modules_config_file"]):
        enabled = get_enabled_modules()
        
        assert len(enabled) == expected_count
        assert set(enabled) == set(enabled_modules)


@pytest.mark.parametrize("module_name,should_exist", [
    ("ssh_manager", True),
    ("docker_manager", True),
    ("kubernetes_manager", True),
    ("nonexistent_module", False),
    ("", False),
])
def test_module_existence_validation(module_name, should_exist, cli_test_environment):
    """Test module existence validation for various module names."""
    with patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', 
              cli_test_environment["modules_config_file"]):
        if should_exist:
            # Valid modules should be enabled/disabled successfully
            enable_result = enable_module(module_name)
            assert enable_result is True
            
            disable_result = disable_module(module_name)
            assert disable_result is True
        else:
            # Invalid modules should fail
            enable_result = enable_module(module_name)
            assert enable_result is False
            
            disable_result = disable_module(module_name)
            assert disable_result is False 