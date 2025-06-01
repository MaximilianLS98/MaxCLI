"""
Testing utility functions following functional programming principles.

This module provides pure functions for common testing operations,
ensuring no side effects and predictable behavior.
"""

from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import subprocess
import json
from unittest.mock import MagicMock


def create_test_config(enabled_modules: List[str]) -> Dict[str, Any]:
    """Create a test configuration with specified enabled modules.
    
    Args:
        enabled_modules: List of module names to enable.
        
    Returns:
        Complete configuration dictionary.
    """
    # Import the actual AVAILABLE_MODULES from production code
    from maxcli.modules.module_manager import AVAILABLE_MODULES
    
    module_info = {}
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


def mock_successful_subprocess(command_outputs: Dict[str, str]) -> Callable:
    """Create a mock subprocess function with predefined outputs.
    
    Args:
        command_outputs: Mapping of command strings to their expected outputs.
        
    Returns:
        Mock function that simulates subprocess.run behavior.
    """
    def mock_run(cmd, *args, **kwargs):
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = command_outputs.get(cmd_str, "")
        mock_result.stderr = ""
        return mock_result
    
    return mock_run


def mock_failing_subprocess(failing_commands: List[str]) -> Callable:
    """Create a mock subprocess function that fails for specific commands.
    
    Args:
        failing_commands: List of commands that should fail.
        
    Returns:
        Mock function that simulates subprocess failures.
    """
    def mock_run(cmd, *args, **kwargs):
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
        mock_result = MagicMock()
        
        if any(fail_cmd in cmd_str for fail_cmd in failing_commands):
            mock_result.returncode = 1
            mock_result.stderr = f"Command failed: {cmd_str}"
            raise subprocess.CalledProcessError(1, cmd, stderr=mock_result.stderr)
        else:
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
        
        return mock_result
    
    return mock_run


def assert_command_output_contains(output: str, expected_phrases: List[str]) -> bool:
    """Assert that command output contains all expected phrases.
    
    Args:
        output: The actual output string.
        expected_phrases: List of phrases that should be present.
        
    Returns:
        True if all phrases are found, raises AssertionError otherwise.
    """
    for phrase in expected_phrases:
        if phrase not in output:
            raise AssertionError(f"Expected phrase '{phrase}' not found in output: {output}")
    return True


def capture_cli_output(cli_function: Callable, args: List[str]) -> Dict[str, str]:
    """Capture stdout and stderr from a CLI function call.
    
    Args:
        cli_function: The CLI function to test.
        args: Command line arguments to pass.
        
    Returns:
        Dictionary with 'stdout' and 'stderr' keys containing captured output.
    """
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        try:
            cli_function(args)
        except SystemExit:
            pass  # CLI functions often call sys.exit()
    
    return {
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue()
    }


def validate_module_config_structure(config: Dict[str, Any]) -> bool:
    """Validate that a module configuration has the correct structure.
    
    Args:
        config: Configuration dictionary to validate.
        
    Returns:
        True if structure is valid, raises AssertionError otherwise.
    """
    required_keys = ["enabled_modules", "module_info"]
    
    for key in required_keys:
        if key not in config:
            raise AssertionError(f"Required key '{key}' missing from config")
    
    if not isinstance(config["enabled_modules"], list):
        raise AssertionError("enabled_modules must be a list")
    
    if not isinstance(config["module_info"], dict):
        raise AssertionError("module_info must be a dictionary")
    
    # Validate module_info structure
    for module_name, module_data in config["module_info"].items():
        required_module_keys = ["enabled", "description", "commands", "dependencies"]
        for key in required_module_keys:
            if key not in module_data:
                raise AssertionError(f"Module '{module_name}' missing required key '{key}'")
    
    return True


def create_mock_args(**kwargs) -> MagicMock:
    """Create a mock args object with specified attributes.
    
    Args:
        **kwargs: Attributes to set on the mock args object.
        
    Returns:
        Mock args object with specified attributes.
    """
    args = MagicMock()
    for key, value in kwargs.items():
        setattr(args, key, value)
    return args


def create_temporary_file_content(content: str) -> Path:
    """Create a temporary file with specified content.
    
    Args:
        content: Content to write to the file.
        
    Returns:
        Path to the temporary file.
    """
    import tempfile
    temp_file = Path(tempfile.mktemp())
    temp_file.write_text(content)
    return temp_file


def assert_files_equal(file1: Path, file2: Path) -> bool:
    """Assert that two files have identical content.
    
    Args:
        file1: First file to compare.
        file2: Second file to compare.
        
    Returns:
        True if files are identical, raises AssertionError otherwise.
    """
    content1 = file1.read_text()
    content2 = file2.read_text()
    
    if content1 != content2:
        raise AssertionError(f"Files differ:\nFile1: {content1}\nFile2: {content2}")
    
    return True


def count_subprocess_calls_with_command(mock_subprocess: MagicMock, command_fragment: str) -> int:
    """Count how many subprocess calls contained a specific command fragment.
    
    Args:
        mock_subprocess: Mock subprocess object.
        command_fragment: Fragment to search for in commands.
        
    Returns:
        Number of calls containing the fragment.
    """
    count = 0
    for call in mock_subprocess.call_args_list:
        args, kwargs = call
        if args and isinstance(args[0], list):
            cmd_str = ' '.join(args[0])
        else:
            cmd_str = str(args[0]) if args else ""
        
        if command_fragment in cmd_str:
            count += 1
    
    return count 