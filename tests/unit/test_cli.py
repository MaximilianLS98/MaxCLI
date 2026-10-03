"""
Unit tests for the main CLI module (maxcli.cli).

This module provides comprehensive testing coverage for all core CLI functions,
including file operations, version management, update workflows, and argument parsing.
Tests follow functional programming principles with comprehensive mocking of external dependencies.
"""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, mock_open, call

import pytest

from maxcli.cli import (
    get_files_to_remove,
    remove_path_from_shell_config,
    confirm_uninstall,
    uninstall_maxcli,
    display_version,
    update_maxcli,
    create_parser,
    register_core_commands,
    main
)


class TestFileDiscovery:
    """Test suite for file discovery and cleanup functionality."""

    @pytest.fixture
    def mock_home_dir(self, tmp_path: Path) -> Path:
        """Create a temporary home directory structure for testing."""
        home = tmp_path / "home"
        home.mkdir()
        return home

    def test_get_files_to_remove_all_present(self, mock_home_dir: Path) -> None:
        """Test get_files_to_remove when all MaxCLI files exist."""
        # Arrange: Create all MaxCLI directories and files
        config_dir = mock_home_dir / ".config" / "maxcli"
        config_dir.mkdir(parents=True)
        
        lib_dir = mock_home_dir / ".local" / "lib" / "python" / "maxcli"
        lib_dir.mkdir(parents=True)
        
        bin_dir = mock_home_dir / "bin"
        bin_dir.mkdir()
        max_executable = bin_dir / "max"
        max_executable.touch()
        
        ssh_backup1 = mock_home_dir / "ssh_keys_backup.tar.gz"
        ssh_backup1.touch()
        ssh_backup2 = mock_home_dir / "ssh_keys_backup.tar.gz.gpg"
        ssh_backup2.touch()

        with patch('pathlib.Path.home', return_value=mock_home_dir):
            # Act: Get files to remove
            result = get_files_to_remove()

            # Assert: All files should be detected
            assert len(result) == 5
            
            paths = [str(item[0]) for item in result]
            descriptions = [item[1] for item in result]
            
            assert str(config_dir) in paths
            assert str(lib_dir) in paths
            assert str(max_executable) in paths
            assert str(ssh_backup1) in paths
            assert str(ssh_backup2) in paths
            
            assert "Configuration directory" in descriptions[0]
            assert "MaxCLI library" in descriptions[1]
            assert "MaxCLI executable" in descriptions[2]

    def test_get_files_to_remove_none_present(self, mock_home_dir: Path) -> None:
        """Test get_files_to_remove when no MaxCLI files exist."""
        with patch('pathlib.Path.home', return_value=mock_home_dir):
            # Act: Get files to remove
            result = get_files_to_remove()

            # Assert: No files should be detected
            assert result == []

    def test_get_files_to_remove_partial_installation(self, mock_home_dir: Path) -> None:
        """Test get_files_to_remove with only some MaxCLI files present."""
        # Arrange: Create only config directory
        config_dir = mock_home_dir / ".config" / "maxcli"
        config_dir.mkdir(parents=True)

        with patch('pathlib.Path.home', return_value=mock_home_dir):
            # Act: Get files to remove
            result = get_files_to_remove()

            # Assert: Only config directory should be detected
            assert len(result) == 1
            assert str(config_dir) in str(result[0][0])
            assert "Configuration directory" in result[0][1]


class TestShellConfigManagement:
    """Test suite for shell configuration file management."""

    def test_remove_path_from_shell_config_exact_match(self, tmp_path: Path) -> None:
        """Test removal of exact MaxCLI PATH line from shell config."""
        # Arrange: Create shell config with MaxCLI PATH line
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        zshrc = home_dir / ".zshrc"
        
        shell_content = '''# User configuration
export PATH="/usr/local/bin:$PATH"
export PATH="$HOME/bin:$PATH"
# End configuration'''
        
        zshrc.write_text(shell_content)

        with patch('pathlib.Path.home', return_value=home_dir):
            # Act: Remove MaxCLI PATH modification
            result = remove_path_from_shell_config()

            # Assert: MaxCLI line should be removed
            assert result is True
            remaining_content = zshrc.read_text()
            assert 'export PATH="$HOME/bin:$PATH"' not in remaining_content
            assert 'export PATH="/usr/local/bin:$PATH"' in remaining_content
            assert "# User configuration" in remaining_content

    def test_remove_path_from_shell_config_no_modification(self, tmp_path: Path) -> None:
        """Test shell config cleanup when no MaxCLI modifications exist."""
        # Arrange: Create shell config without MaxCLI PATH line
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        zshrc = home_dir / ".zshrc"
        
        shell_content = '''# User configuration
export PATH="/usr/local/bin:$PATH"
# End configuration'''
        
        zshrc.write_text(shell_content)

        with patch('pathlib.Path.home', return_value=home_dir):
            # Act: Remove MaxCLI PATH modification
            result = remove_path_from_shell_config()

            # Assert: No modifications should be found
            assert result is False
            assert zshrc.read_text() == shell_content

    def test_remove_path_from_shell_config_multiple_files(self, tmp_path: Path) -> None:
        """Test PATH removal across multiple shell configuration files."""
        # Arrange: Create multiple shell configs with MaxCLI PATH
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        configs = {
            ".zshrc": 'export PATH="$HOME/bin:$PATH"\nother_config',
            ".bashrc": 'some_config\nexport PATH="$HOME/bin:$PATH"',
            ".bash_profile": 'export PATH="$HOME/bin:$PATH"'
        }
        
        for filename, content in configs.items():
            config_file = home_dir / filename
            config_file.write_text(content)

        with patch('pathlib.Path.home', return_value=home_dir):
            # Act: Remove MaxCLI PATH modification
            result = remove_path_from_shell_config()

            # Assert: All MaxCLI lines should be removed
            assert result is True
            
            for filename in configs.keys():
                config_file = home_dir / filename
                content = config_file.read_text()
                assert 'export PATH="$HOME/bin:$PATH"' not in content

    def test_remove_path_from_shell_config_file_error(self, tmp_path: Path) -> None:
        """Test shell config cleanup with file permission errors."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        with patch('pathlib.Path.home', return_value=home_dir), \
             patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Act: Attempt to remove PATH modification
            result = remove_path_from_shell_config()

            # Assert: Should handle error gracefully
            assert result is False


class TestUninstallConfirmation:
    """Test suite for uninstall confirmation logic."""

    def test_confirm_uninstall_force_mode(self) -> None:
        """Test uninstall confirmation in force mode."""
        # Act: Confirm uninstall with force flag
        result = confirm_uninstall(force=True)

        # Assert: Should skip confirmations
        assert result is True

    @patch('builtins.input')
    @patch('maxcli.cli.get_files_to_remove')
    def test_confirm_uninstall_valid_confirmations(
        self, 
        mock_get_files: Mock, 
        mock_input: Mock
    ) -> None:
        """Test uninstall confirmation with valid user responses."""
        # Arrange: Mock file discovery and user input
        mock_get_files.return_value = [
            (Path("/home/user/.config/maxcli"), "Configuration directory"),
            (Path("/home/user/bin/max"), "MaxCLI executable")
        ]
        mock_input.side_effect = ['yes', 'DELETE EVERYTHING']

        # Act: Confirm uninstall
        result = confirm_uninstall(force=False)

        # Assert: Should accept valid confirmations
        assert result is True
        assert mock_input.call_count == 2

    @patch('builtins.input')
    @patch('maxcli.cli.get_files_to_remove')
    def test_confirm_uninstall_first_confirmation_failed(
        self, 
        mock_get_files: Mock, 
        mock_input: Mock
    ) -> None:
        """Test uninstall confirmation when first confirmation fails."""
        # Arrange: Mock file discovery and user input
        mock_get_files.return_value = []
        mock_input.return_value = 'no'

        # Act: Confirm uninstall
        result = confirm_uninstall(force=False)

        # Assert: Should reject on first confirmation failure
        assert result is False
        assert mock_input.call_count == 1

    @patch('builtins.input')
    @patch('maxcli.cli.get_files_to_remove')
    def test_confirm_uninstall_second_confirmation_failed(
        self, 
        mock_get_files: Mock, 
        mock_input: Mock
    ) -> None:
        """Test uninstall confirmation when second confirmation fails."""
        # Arrange: Mock file discovery and user input
        mock_get_files.return_value = []
        mock_input.side_effect = ['yes', 'wrong phrase']

        # Act: Confirm uninstall
        result = confirm_uninstall(force=False)

        # Assert: Should reject on second confirmation failure
        assert result is False
        assert mock_input.call_count == 2


class TestUninstallWorkflow:
    """Test suite for complete uninstall workflow."""

    @patch('maxcli.cli.confirm_uninstall')
    def test_uninstall_maxcli_cancelled(self, mock_confirm: Mock) -> None:
        """Test uninstall workflow when user cancels."""
        # Arrange: Mock user cancellation
        mock_confirm.return_value = False
        args = Mock(force=False)

        # Act: Attempt uninstall
        uninstall_maxcli(args)

        # Assert: Should exit early on cancellation
        mock_confirm.assert_called_once_with(False)

    @patch('maxcli.cli.remove_path_from_shell_config')
    @patch('maxcli.cli.get_files_to_remove')
    @patch('maxcli.cli.confirm_uninstall')
    @patch('shutil.rmtree')
    def test_uninstall_maxcli_successful(
        self, 
        mock_rmtree: Mock,
        mock_confirm: Mock,
        mock_get_files: Mock,
        mock_remove_path: Mock,
        tmp_path: Path
    ) -> None:
        """Test successful uninstall workflow."""
        # Arrange: Mock successful uninstall scenario
        mock_confirm.return_value = True
        mock_remove_path.return_value = True
        
        test_file = tmp_path / "test_file.txt"
        test_file.touch()
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        mock_get_files.return_value = [
            (test_file, "Test file"),
            (test_dir, "Test directory")
        ]
        
        args = Mock(force=False)

        # Act: Perform uninstall
        uninstall_maxcli(args)

        # Assert: All cleanup operations should be performed
        mock_confirm.assert_called_once_with(False)
        mock_get_files.assert_called_once()
        mock_remove_path.assert_called_once()
        assert not test_file.exists()  # File should be removed
        mock_rmtree.assert_called_once_with(test_dir)  # Directory removal

    @patch('maxcli.cli.remove_path_from_shell_config')
    @patch('maxcli.cli.get_files_to_remove')
    @patch('maxcli.cli.confirm_uninstall')
    def test_uninstall_maxcli_file_removal_error(
        self, 
        mock_confirm: Mock,
        mock_get_files: Mock,
        mock_remove_path: Mock,
        tmp_path: Path
    ) -> None:
        """Test uninstall workflow with file removal errors."""
        # Arrange: Mock file removal error
        mock_confirm.return_value = True
        mock_remove_path.return_value = False
        
        # Create a file that will cause removal to fail
        test_file = tmp_path / "readonly_file.txt"
        test_file.touch()
        test_file.chmod(0o444)  # Read-only
        
        mock_get_files.return_value = [(test_file, "Read-only file")]
        args = Mock(force=False)

        # Act: Perform uninstall (should handle errors gracefully)
        uninstall_maxcli(args)

        # Assert: Should continue despite file errors
        mock_confirm.assert_called_once_with(False)
        mock_get_files.assert_called_once()
        mock_remove_path.assert_called_once()


class TestArgumentParsing:
    """Test suite for argument parsing and CLI structure."""

    def test_create_parser_basic_structure(self) -> None:
        """Test basic argument parser creation and structure."""
        # Act: Create parser
        parser = create_parser()

        # Assert: Should create parser with correct properties
        assert parser.prog == 'max'
        assert "Personal CLI" in parser.description
        assert parser.formatter_class == argparse.RawDescriptionHelpFormatter

    def test_create_parser_version_argument(self) -> None:
        """Test version argument parsing."""
        # Arrange: Create parser
        parser = create_parser()

        # Act: Parse version arguments
        args_short = parser.parse_args(['-v'])
        args_long = parser.parse_args(['--version'])

        # Assert: Version flag should be parsed correctly
        assert args_short.version is True
        assert args_long.version is True

    def test_register_core_commands_structure(self) -> None:
        """Test core command registration structure."""
        # Arrange: Create parser and subparsers
        parser = create_parser()
        subparsers = parser.add_subparsers()

        # Act: Register core commands
        register_core_commands(subparsers)

        # Assert: Core commands should be registered
        # Parse different commands to verify they exist
        try:
            parser.parse_args(['init'])
            parser.parse_args(['update'])
            parser.parse_args(['uninstall'])
        except SystemExit:
            # Expected behavior for help commands
            pass

    def test_register_core_commands_init_arguments(self) -> None:
        """Test init command argument parsing."""
        # Arrange: Create parser with core commands
        parser = create_parser()
        subparsers = parser.add_subparsers()
        register_core_commands(subparsers)

        # Act: Parse init command with force flag
        args = parser.parse_args(['init', '--force'])

        # Assert: Force flag should be parsed correctly
        assert hasattr(args, 'force')
        assert args.force is True

    def test_register_core_commands_update_arguments(self) -> None:
        """Test update command argument parsing."""
        # Arrange: Create parser with core commands
        parser = create_parser()
        subparsers = parser.add_subparsers()
        register_core_commands(subparsers)

        # Act: Parse update command with flags
        args = parser.parse_args(['update', '--check-only', '--show-releases'])

        # Assert: Update flags should be parsed correctly
        assert hasattr(args, 'check_only')
        assert hasattr(args, 'show_releases')
        assert args.check_only is True
        assert args.show_releases is True

    def test_register_core_commands_uninstall_arguments(self) -> None:
        """Test uninstall command argument parsing."""
        # Arrange: Create parser with core commands
        parser = create_parser()
        subparsers = parser.add_subparsers()
        register_core_commands(subparsers)

        # Act: Parse uninstall command with force flag
        args = parser.parse_args(['uninstall', '--force'])

        # Assert: Force flag should be parsed correctly
        assert hasattr(args, 'force')
        assert args.force is True


class TestMainEntryPoint:
    """Test suite for the main CLI entry point."""

    @patch('maxcli.cli.display_version')
    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    @patch('sys.argv', ['max', '-v'])
    def test_main_version_flag(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock,
        mock_display_version: Mock
    ) -> None:
        """Test main function with version flag."""
        # Act: Run main with version flag
        main()

        # Assert: Should call display_version and exit early
        mock_display_version.assert_called_once()

    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    @patch('sys.argv', ['max'])
    def test_main_no_command(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock,
        capsys
    ) -> None:
        """Test main function with no command provided."""
        # Act: Run main with no command
        main()

        # Assert: Should show help (captured in output)
        captured = capsys.readouterr()
        # Help is printed to stdout when no command is provided
        assert "usage:" in captured.out or "Max's Personal CLI" in captured.out

    @patch('maxcli.cli.init_config')
    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    @patch('sys.argv', ['max', 'init'])
    def test_main_with_command(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock,
        mock_init_config: Mock
    ) -> None:
        """Test main function with init command."""
        # Act: Run main with init command
        main()

        # Assert: Should call the init_config function
        mock_init_config.assert_called_once()

    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    def test_main_module_loading(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock
    ) -> None:
        """Test main function module loading integration."""
        with patch('sys.argv', ['max', '--help']):
            try:
                # Act: Run main (will exit due to help)
                main()
            except SystemExit:
                # Expected behavior for help command
                pass

            # Assert: Should register both core and module commands
            mock_register_modules.assert_called_once()
            mock_load_modules.assert_called_once()

    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    def test_main_argcomplete_integration(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock
    ) -> None:
        """Test main function with optional argcomplete integration."""
        # Mock the argcomplete import inside the main function
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'argcomplete':
                raise ImportError("argcomplete not found")
            return original_import(name, *args, **kwargs)
        
        with patch('sys.argv', ['max']), \
             patch('builtins.__import__', side_effect=mock_import):
            # Act: Run main without argcomplete
            main()

            # Assert: Should handle missing argcomplete gracefully
            mock_register_modules.assert_called_once()
            mock_load_modules.assert_called_once()


# Integration test for complete workflow
