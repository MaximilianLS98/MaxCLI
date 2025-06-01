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
    update_module_info_if_needed,
    AVAILABLE_MODULES
)
from tests.utils.test_helpers import (
    create_test_config,
    validate_module_config_structure
)


class TestModuleConfigLoading:
    """Test module configuration loading functionality."""
    
    def test_load_default_config_when_file_missing(self, isolated_module_manager: Dict[str, Any]):
        """Test that default config is created when file doesn't exist."""
        # File doesn't exist in isolated environment by default
        config = load_modules_config()
        
        # Validate structure
        validate_module_config_structure(config)
        
        # Check default modules are enabled
        assert "ssh_manager" in config["enabled_modules"]
        assert "setup_manager" in config["enabled_modules"]
    
    def test_load_existing_valid_config(self, cli_test_environment: Dict[str, Any]):
        """Test loading a valid existing configuration."""
        config = load_modules_config()
        
        # Should match the sample config
        assert "ssh_manager" in config["enabled_modules"]
        assert "docker_manager" in config["enabled_modules"]
        assert config["module_info"]["ssh_manager"]["enabled"] is True
        assert config["module_info"]["docker_manager"]["enabled"] is True
        
        # Check that some modules are disabled
        disabled_modules = [name for name, info in config["module_info"].items() 
                          if not info["enabled"]]
        assert len(disabled_modules) > 0
    
    def test_handle_corrupted_config_file(self, isolated_module_manager: Dict[str, Any]):
        """Test handling of corrupted JSON configuration file."""
        # Write invalid JSON
        modules_config_file = isolated_module_manager["modules_config_file"]
        with open(modules_config_file, 'w') as f:
            f.write("{ invalid json")
        
        config = load_modules_config()
        
        # Should fall back to default config
        validate_module_config_structure(config)
        assert "ssh_manager" in config["enabled_modules"]
    
    def test_legacy_config_conversion(self, isolated_module_manager: Dict[str, Any]):
        """Test conversion from legacy boolean flag format to new format."""
        # Create a legacy config with boolean flags
        legacy_config = {
            "ssh_manager": True,
            "docker_manager": False,
            "kubernetes_manager": True
        }
        
        modules_config_file = isolated_module_manager["modules_config_file"]
        with open(modules_config_file, 'w') as f:
            json.dump(legacy_config, f)
        
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
        # Find a module that's disabled in the sample config
        config = load_modules_config()
        disabled_modules = [name for name, info in config["module_info"].items() 
                          if not info["enabled"]]
        test_module = disabled_modules[0] if disabled_modules else "kubernetes_manager"
        
        result = enable_module(test_module)
        
        assert result is True
        
        # Verify it's now enabled
        updated_config = load_modules_config()
        assert test_module in updated_config["enabled_modules"]
        assert updated_config["module_info"][test_module]["enabled"] is True
    
    def test_enable_invalid_module(self, isolated_module_manager: Dict[str, Any]):
        """Test enabling a non-existent module."""
        result = enable_module("nonexistent_module")
        
        assert result is False
    
    def test_enable_already_enabled_module(self, cli_test_environment: Dict[str, Any]):
        """Test enabling an already enabled module."""
        # SSH manager is enabled in sample config
        result = enable_module("ssh_manager")
        
        assert result is True  # Should succeed even if already enabled
    
    def test_disable_enabled_module(self, cli_test_environment: Dict[str, Any]):
        """Test disabling an enabled module."""
        # SSH manager is enabled in sample config
        result = disable_module("ssh_manager")
        
        assert result is True
        
        # Verify it's now disabled
        config = load_modules_config()
        assert "ssh_manager" not in config["enabled_modules"]
        assert config["module_info"]["ssh_manager"]["enabled"] is False
    
    def test_disable_already_disabled_module(self, cli_test_environment: Dict[str, Any]):
        """Test disabling an already disabled module."""
        # Find a disabled module
        config = load_modules_config()
        disabled_modules = [name for name, info in config["module_info"].items() 
                          if not info["enabled"]]
        test_module = disabled_modules[0] if disabled_modules else "kubernetes_manager"
        
        result = disable_module(test_module)
        
        assert result is True  # Should succeed even if already disabled
    
    def test_disable_invalid_module(self, isolated_module_manager: Dict[str, Any]):
        """Test disabling a non-existent module."""
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
        # Description should be updated to current value
        expected_desc = AVAILABLE_MODULES["ssh_manager"]["description"]
        assert config["module_info"]["ssh_manager"]["description"] == expected_desc
    
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
        for module_name in AVAILABLE_MODULES.keys():
            assert module_name in config["module_info"]
        
        # New modules should have correct enabled state
        for module_name, info in config["module_info"].items():
            expected_enabled = module_name in config["enabled_modules"]
            assert info["enabled"] == expected_enabled


class TestConfigPersistence:
    """Test configuration file save and load operations."""
    
    def test_save_and_load_config_roundtrip(self, isolated_module_manager: Dict[str, Any]):
        """Test that saving and loading config preserves all data."""
        original_config = create_test_config(["ssh_manager", "coolify_manager"])
        
        # Save the config
        assert save_modules_config(original_config) is True
        
        # Load it back
        loaded_config = load_modules_config()
        
        # Should match exactly
        assert loaded_config["enabled_modules"] == original_config["enabled_modules"]
        assert loaded_config["module_info"] == original_config["module_info"]
    
    def test_save_config_creates_directory(self, temp_config_dir: Path):
        """Test that saving config creates directory if it doesn't exist."""
        # Remove the config directory
        config_dir = temp_config_dir
        if config_dir.exists():
            import shutil
            shutil.rmtree(config_dir)
        
        modules_config_file = config_dir / "modules_config.json"
        
        with patch('maxcli.modules.module_manager.CONFIG_DIR', config_dir), \
             patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', modules_config_file):
            
            test_config = create_test_config(["ssh_manager"])
            result = save_modules_config(test_config)
            
            assert result is True
            assert config_dir.exists()
            assert modules_config_file.exists()


@pytest.mark.parametrize("enabled_modules,expected_count", [
    ([], 0),
    (["ssh_manager"], 1),
    (["ssh_manager", "docker_manager"], 2),
    (["ssh_manager", "docker_manager", "kubernetes_manager"], 3),
])
def test_get_enabled_modules_count(enabled_modules, expected_count, isolated_module_manager):
    """Test that get_enabled_modules returns correct count."""
    # Create and save test config
    test_config = create_test_config(enabled_modules)
    assert save_modules_config(test_config) is True
    
    # Get enabled modules
    result = get_enabled_modules()
    
    assert len(result) == expected_count
    assert set(result) == set(enabled_modules)


@pytest.mark.parametrize("module_name,should_exist", [
    ("ssh_manager", True),
    ("docker_manager", True),
    ("kubernetes_manager", True),
    ("nonexistent_module", False),
    ("", False),
])
def test_module_existence_validation(module_name, should_exist, isolated_module_manager):
    """Test validation of module existence."""
    from maxcli.modules.module_manager import get_available_modules
    
    available_modules = get_available_modules()
    
    assert (module_name in available_modules) == should_exist 