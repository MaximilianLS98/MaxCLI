"""
Pytest configuration and shared fixtures for MaxCLI testing.

This module provides the foundational testing infrastructure following
functional programming principles with immutable fixtures and pure functions.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator, Optional
from unittest.mock import patch, MagicMock
import pytest


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary configuration directory for testing.
    
    Yields:
        Path to temporary config directory that gets cleaned up automatically.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / ".config" / "maxcli"
        config_path.mkdir(parents=True)
        yield config_path


@pytest.fixture
def mock_home_dir(temp_config_dir: Path) -> Generator[Path, None, None]:
    """Mock the home directory to use temporary directory.
    
    Args:
        temp_config_dir: Temporary config directory fixture.
        
    Yields:
        Path to mocked home directory.
    """
    home_path = temp_config_dir.parent.parent
    with patch('pathlib.Path.home', return_value=home_path):
        yield home_path


@pytest.fixture
def isolated_module_manager(mock_home_dir: Path):
    """Create an isolated module manager environment for testing.
    
    This fixture ensures that module manager operations are completely
    isolated from the real configuration files.
    
    Args:
        mock_home_dir: Mocked home directory from fixture.
        
    Yields:
        Dictionary with isolated paths and configuration.
    """
    config_dir = mock_home_dir / ".config" / "maxcli"
    modules_config_file = config_dir / "modules_config.json"
    
    # Patch all the module manager paths to use temporary directory
    with patch('maxcli.modules.module_manager.CONFIG_DIR', config_dir), \
         patch('maxcli.modules.module_manager.MODULES_CONFIG_FILE', modules_config_file):
        yield {
            "config_dir": config_dir,
            "modules_config_file": modules_config_file,
            "mock_home": mock_home_dir
        }


@pytest.fixture
def sample_module_config() -> Dict[str, Any]:
    """Create a sample module configuration for testing.
    
    Returns:
        Dictionary containing sample module configuration using actual modules.
    """
    # Import the actual modules to ensure tests stay in sync
    from maxcli.modules.module_manager import AVAILABLE_MODULES
    
    # Create module_info for all available modules
    module_info = {}
    enabled_modules = ["ssh_manager", "docker_manager"]
    
    for module_name, module_data in AVAILABLE_MODULES.items():
        module_info[module_name] = {
            "enabled": module_name in enabled_modules,
            "description": module_data["description"],
            "commands": module_data["commands"],
            "dependencies": []
        }
    
    return {
        "enabled_modules": enabled_modules,
        "module_info": module_info,
        "created_at": "2024-01-01T00:00:00Z",
        "bootstrap_version": "1.0.0"
    }


@pytest.fixture
def mock_subprocess() -> Generator[MagicMock, None, None]:
    """Mock subprocess calls for command testing.
    
    Yields:
        Mock subprocess object with controllable behavior.
    """
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def cli_test_environment(isolated_module_manager: Dict, sample_module_config: Dict) -> Dict[str, Any]:
    """Create a complete CLI testing environment.
    
    Args:
        isolated_module_manager: Isolated module manager environment.
        sample_module_config: Sample configuration data.
        
    Returns:
        Dictionary containing all environment paths and configs.
    """
    config_dir = isolated_module_manager["config_dir"]
    modules_config_file = isolated_module_manager["modules_config_file"]
    
    # Create config file
    with open(modules_config_file, 'w') as f:
        json.dump(sample_module_config, f, indent=2)
    
    return {
        "home_dir": isolated_module_manager["mock_home"],
        "config_dir": config_dir,
        "modules_config_file": modules_config_file,
        "config_data": sample_module_config
    }


@pytest.fixture
def isolated_cli_parser():
    """Create an isolated CLI parser for testing command registration.
    
    Returns:
        Fresh ArgumentParser instance with no registered commands.
    """
    import argparse
    parser = argparse.ArgumentParser(prog='max-test')
    subparsers = parser.add_subparsers(dest="command")
    return parser, subparsers 