"""
Unit tests for Docker manager module functionality.

Tests Docker command parsing, cleanup operations, and subprocess interactions
using mocked Docker commands to avoid requiring Docker installation.
"""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import subprocess

from maxcli.commands.docker import (
    docker_clean_extensive,
    docker_clean_minimal,
    docker_clean_command
)
from tests.utils.test_helpers import (
    mock_successful_subprocess,
    mock_failing_subprocess,
    capture_cli_output,
    create_mock_args,
    count_subprocess_calls_with_command
)


class TestDockerCleanExtensive:
    """Test extensive Docker cleanup functionality."""
    
    def test_successful_extensive_cleanup(self, mock_subprocess):
        """Test successful extensive cleanup operation."""
        mock_subprocess.return_value.returncode = 0
        
        # Capture output
        output = capture_cli_output(lambda _: docker_clean_extensive(), [])
        
        # Verify correct command was called
        mock_subprocess.assert_called_once_with(
            ["docker", "system", "prune", "-af"], 
            check=True
        )
        
        # Verify success message
        assert "🧹 Performing extensive Docker cleanup..." in output["stdout"]
        assert "✅ Extensive Docker cleanup completed!" in output["stdout"]
    
    def test_failed_extensive_cleanup(self, mock_subprocess):
        """Test handling of failed extensive cleanup."""
        # Mock subprocess to raise CalledProcessError
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, ["docker", "system", "prune", "-af"])
        
        # Should exit with error
        with pytest.raises(SystemExit) as excinfo:
            docker_clean_extensive()
        
        assert excinfo.value.code == 1
    
    def test_extensive_cleanup_command_structure(self, mock_subprocess):
        """Test that extensive cleanup calls the correct Docker command."""
        mock_subprocess.return_value.returncode = 0
        
        docker_clean_extensive()
        
        # Verify the exact command structure
        args, kwargs = mock_subprocess.call_args
        assert args[0] == ["docker", "system", "prune", "-af"]
        assert kwargs.get("check") is True


class TestDockerCleanMinimal:
    """Test minimal Docker cleanup functionality."""
    
    def test_successful_minimal_cleanup(self, mock_subprocess):
        """Test successful minimal cleanup operation."""
        mock_subprocess.return_value.returncode = 0
        
        # Capture output
        output = capture_cli_output(lambda _: docker_clean_minimal(), [])
        
        # Verify all expected commands were called
        assert mock_subprocess.call_count == 4
        
        # Verify success messages
        assert "🧹 Performing minimal Docker cleanup..." in output["stdout"]
        assert "✅ Minimal Docker cleanup completed!" in output["stdout"]
        assert "💡 For extensive cleanup" in output["stdout"]
    
    def test_minimal_cleanup_command_sequence(self, mock_subprocess):
        """Test that minimal cleanup calls the correct sequence of commands."""
        mock_subprocess.return_value.returncode = 0
        
        docker_clean_minimal()
        
        # Should call exactly 4 commands
        assert mock_subprocess.call_count == 4
        
        # Verify command sequence
        calls = mock_subprocess.call_args_list
        
        # Container prune with 24h filter
        assert calls[0][0][0][:3] == ["docker", "container", "prune"]
        assert "--filter" in calls[0][0][0]
        assert "until=24h" in calls[0][0][0]
        
        # Image prune (dangling only)
        assert calls[1][0][0] == ["docker", "image", "prune", "-f"]
        
        # Network prune
        assert calls[2][0][0] == ["docker", "network", "prune", "-f"]
        
        # Builder prune with 7 day filter
        assert calls[3][0][0][:3] == ["docker", "builder", "prune"]
        assert "until=168h" in calls[3][0][0]
    
    def test_partial_failure_minimal_cleanup(self, mock_subprocess):
        """Test handling when one command in minimal cleanup fails."""
        # Mock to fail on the second call (image prune)
        call_count = 0
        def failing_on_second_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise subprocess.CalledProcessError(1, args[0])
            return MagicMock(returncode=0)
        
        mock_subprocess.side_effect = failing_on_second_call
        
        # Should exit with error on first failure
        with pytest.raises(SystemExit) as excinfo:
            docker_clean_minimal()
        
        assert excinfo.value.code == 1
        # Should have stopped after the failing command
        assert call_count == 2
    
    def test_minimal_cleanup_error_messages(self, mock_subprocess):
        """Test that minimal cleanup shows appropriate error messages."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["docker", "container", "prune"], stderr="Permission denied"
        )
        
        output = capture_cli_output(lambda _: docker_clean_minimal(), [])
        
        # Should show error message
        assert "❌ Error during Docker cleanup" in output["stderr"]


class TestDockerCleanCommand:
    """Test the main docker clean command handler."""
    
    def test_extensive_flag_triggers_extensive_cleanup(self, mock_subprocess):
        """Test that --extensive flag triggers extensive cleanup."""
        args = create_mock_args(extensive=True, minimal=False)
        
        mock_subprocess.return_value.returncode = 0
        
        docker_clean_command(args)
        
        # Should call docker system prune -af
        mock_subprocess.assert_called_once_with(
            ["docker", "system", "prune", "-af"],
            check=True
        )
    
    def test_minimal_flag_triggers_minimal_cleanup(self, mock_subprocess):
        """Test that --minimal flag triggers minimal cleanup."""
        args = create_mock_args(extensive=False, minimal=True)
        
        mock_subprocess.return_value.returncode = 0
        
        docker_clean_command(args)
        
        # Should call multiple minimal cleanup commands
        assert mock_subprocess.call_count == 4
    
    def test_no_flags_defaults_to_minimal(self, mock_subprocess):
        """Test that no flags defaults to minimal cleanup."""
        args = create_mock_args(extensive=False, minimal=False)
        
        mock_subprocess.return_value.returncode = 0
        
        output = capture_cli_output(lambda _: docker_clean_command(args), [])
        
        # Should default to minimal
        assert mock_subprocess.call_count == 4
        assert "defaulting to minimal cleanup" in output["stdout"]
    
    def test_extensive_flag_priority_over_minimal(self, mock_subprocess):
        """Test that extensive flag takes priority if both are set."""
        args = create_mock_args(extensive=True, minimal=True)
        
        mock_subprocess.return_value.returncode = 0
        
        docker_clean_command(args)
        
        # Should call extensive cleanup (single command)
        assert mock_subprocess.call_count == 1
        assert mock_subprocess.call_args[0][0] == ["docker", "system", "prune", "-af"]


class TestDockerCommandCounting:
    """Test command counting and verification utilities."""
    
    def test_count_docker_commands(self, mock_subprocess):
        """Test counting specific Docker commands."""
        mock_subprocess.return_value.returncode = 0
        
        docker_clean_minimal()
        
        # Count different types of commands
        container_commands = count_subprocess_calls_with_command(mock_subprocess, "container")
        image_commands = count_subprocess_calls_with_command(mock_subprocess, "image")
        network_commands = count_subprocess_calls_with_command(mock_subprocess, "network")
        builder_commands = count_subprocess_calls_with_command(mock_subprocess, "builder")
        
        assert container_commands == 1
        assert image_commands == 1
        assert network_commands == 1
        assert builder_commands == 1
    
    def test_prune_command_verification(self, mock_subprocess):
        """Test that all commands are prune operations."""
        mock_subprocess.return_value.returncode = 0
        
        docker_clean_minimal()
        
        # All commands should contain "prune"
        prune_commands = count_subprocess_calls_with_command(mock_subprocess, "prune")
        assert prune_commands == 4


class TestLegacyFunctions:
    """Test backward compatibility functions."""
    
    def test_legacy_docker_clean_function(self, mock_subprocess):
        """Test legacy docker_clean function."""
        from maxcli.commands.docker import docker_clean
        
        mock_subprocess.return_value.returncode = 0
        args = create_mock_args()
        
        docker_clean(args)
        
        # Should call extensive cleanup
        mock_subprocess.assert_called_once_with(
            ["docker", "system", "prune", "-af"],
            check=True
        )
    
    def test_legacy_docker_tidy_function(self, mock_subprocess):
        """Test legacy docker_tidy function."""
        from maxcli.commands.docker import docker_tidy
        
        mock_subprocess.return_value.returncode = 0
        args = create_mock_args()
        
        docker_tidy(args)
        
        # Should call minimal cleanup (4 commands)
        assert mock_subprocess.call_count == 4


@pytest.mark.parametrize("cleanup_type,expected_command_count", [
    ("extensive", 1),  # Single docker system prune command
    ("minimal", 4),    # Four separate cleanup commands
])
def test_cleanup_command_counts(cleanup_type, expected_command_count, mock_subprocess):
    """Test that different cleanup types call expected number of commands."""
    args = create_mock_args(
        extensive=(cleanup_type == "extensive"),
        minimal=(cleanup_type == "minimal")
    )
    
    mock_subprocess.return_value.returncode = 0
    
    docker_clean_command(args)
    
    assert mock_subprocess.call_count == expected_command_count


@pytest.mark.parametrize("command_should_fail,expected_exit", [
    (False, None),  # Success case
    (True, 1),      # Failure case should exit with code 1
])
def test_error_handling_scenarios(command_should_fail, expected_exit, mock_subprocess):
    """Test error handling for different failure scenarios."""
    if command_should_fail:
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, ["docker"])
        with pytest.raises(SystemExit) as excinfo:
            docker_clean_extensive()
        assert excinfo.value.code == expected_exit
    else:
        mock_subprocess.return_value.returncode = 0
        # Should not raise
        docker_clean_extensive() 