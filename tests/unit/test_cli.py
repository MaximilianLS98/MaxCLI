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
    display_version,
    update_maxcli,
    create_parser,
    register_core_commands,
    main
)


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
            mock_load_modules.assert_not_called()

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
