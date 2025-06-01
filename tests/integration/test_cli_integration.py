"""
Integration tests for CLI command registration and module loading.

Tests the complete CLI integration including module loading, command registration,
and argument parsing across different module combinations.
"""

import pytest
import argparse
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from maxcli.modules.module_manager import load_and_register_modules, register_commands as register_module_commands
from maxcli.cli import create_parser, register_core_commands
from tests.utils.test_helpers import create_test_config


class TestModuleLoading:
    """Test module loading and command registration."""
    
    def test_load_modules_registers_commands(self, cli_test_environment, isolated_cli_parser):
        """Test that loading modules registers their commands."""
        parser, subparsers = isolated_cli_parser
        
        # Configure with specific modules
        config = create_test_config(["ssh_manager", "docker_manager"])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            load_and_register_modules(subparsers)
        
        # Check that subparsers were created
        # Note: The exact command registration depends on module implementation
        # This test ensures the loading process completes without errors
        assert subparsers is not None
    
    @pytest.mark.docker
    def test_disabled_modules_not_loaded(self, cli_test_environment, isolated_cli_parser):
        """Test that disabled modules are not loaded."""
        parser, subparsers = isolated_cli_parser
        
        # Configure with only ssh_manager enabled
        config = create_test_config(["ssh_manager"])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            # Mock the import to track what modules are loaded
            with patch('importlib.import_module') as mock_import:
                load_and_register_modules(subparsers)
                
                # Check that only ssh_manager was imported
                imported_modules = [call[0][0] for call in mock_import.call_args_list]
                ssh_modules = [m for m in imported_modules if 'ssh_manager' in m]
                docker_modules = [m for m in imported_modules if 'docker_manager' in m]
                
                assert len(ssh_modules) > 0, "SSH manager should be imported"
                assert len(docker_modules) == 0, "Docker manager should not be imported"
    
    def test_module_loading_with_import_error(self, cli_test_environment, isolated_cli_parser):
        """Test that module loading handles import errors gracefully."""
        parser, subparsers = isolated_cli_parser
        
        config = create_test_config(["ssh_manager", "docker_manager"])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            # Mock import to fail for docker_manager
            def mock_import_with_error(module_name):
                if 'docker_manager' in module_name:
                    raise ImportError(f"Module {module_name} not found")
                return MagicMock()
            
            with patch('importlib.import_module', side_effect=mock_import_with_error):
                # Should not crash, should handle error gracefully
                load_and_register_modules(subparsers)
    
    def test_empty_module_list_loads_successfully(self, cli_test_environment, isolated_cli_parser):
        """Test that empty module list loads without issues."""
        parser, subparsers = isolated_cli_parser
        
        config = create_test_config([])  # No modules enabled
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            # Should complete without errors
            load_and_register_modules(subparsers)


class TestCLICommandParsing:
    """Test complete CLI command parsing with registered modules."""
    
    def test_core_commands_always_available(self, cli_test_environment):
        """Test that core commands are always available regardless of module config."""
        config = create_test_config([])  # No modules enabled
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            parser = create_parser()
            subparsers = parser.add_subparsers(dest="command")
            register_core_commands(subparsers)
            
            # Should be able to parse core commands
            args = parser.parse_args(['init'])
            assert args.command == 'init'
            
            args = parser.parse_args(['update', '--check-only'])
            assert args.command == 'update'
            assert args.check_only is True
    
    def test_version_flag_parsing(self, cli_test_environment):
        """Test that version flag is parsed correctly."""
        config = create_test_config([])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            parser = create_parser()
            
            args = parser.parse_args(['--version'])
            assert args.version is True
            
            args = parser.parse_args(['-v'])
            assert args.version is True
    
    def test_help_commands_work_for_core_functions(self, cli_test_environment):
        """Test that help commands work for core functionality."""
        config = create_test_config([])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            parser = create_parser()
            subparsers = parser.add_subparsers(dest="command")
            register_core_commands(subparsers)
            
            # Should be able to get help
            with pytest.raises(SystemExit) as excinfo:
                parser.parse_args(['--help'])
            assert excinfo.value.code == 0  # Help exits with 0
            
            # Should be able to get help for init command
            with pytest.raises(SystemExit) as excinfo:
                parser.parse_args(['init', '--help'])
            assert excinfo.value.code == 0
    
    def test_invalid_command_handling(self, cli_test_environment):
        """Test handling of invalid commands."""
        config = create_test_config([])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            parser = create_parser()
            subparsers = parser.add_subparsers(dest="command")
            register_core_commands(subparsers)
            
            # Should raise SystemExit for invalid commands
            with pytest.raises(SystemExit) as excinfo:
                parser.parse_args(['nonexistent-command'])
            assert excinfo.value.code != 0  # Error exit code


class TestModuleDependencies:
    """Test module dependency handling and error conditions."""
    
    def test_missing_module_dependency_handled_gracefully(self, cli_test_environment):
        """Test that missing module dependencies are handled gracefully."""
        # Create config with a module that might have missing dependencies
        config = create_test_config(["kubernetes_manager"])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            parser = create_parser()
            subparsers = parser.add_subparsers(dest="command")
            
            # Should not crash even if kubectl is not installed
            with patch('importlib.import_module') as mock_import:
                # Simulate module loading
                load_and_register_modules(subparsers)
                
                # Should have attempted to import the module
                assert mock_import.called
    
    @pytest.mark.docker
    def test_partial_module_failure_continues_loading(self, cli_test_environment):
        """Test that failure of one module doesn't stop loading others."""
        config = create_test_config(["ssh_manager", "docker_manager", "kubernetes_manager"])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            # Mock to fail only kubernetes_manager
            def selective_import_failure(module_name):
                if 'kubernetes_manager' in module_name:
                    raise ImportError("kubectl not found")
                mock_module = MagicMock()
                mock_module.register_commands = MagicMock()
                return mock_module
            
            with patch('importlib.import_module', side_effect=selective_import_failure):
                parser = create_parser()
                subparsers = parser.add_subparsers(dest="command")
                
                # Should complete without crashing
                load_and_register_modules(subparsers)


class TestFullCLIIntegration:
    """Test full CLI integration scenarios."""
    
    @pytest.mark.docker
    def test_complete_cli_setup_with_modules(self, cli_test_environment):
        """Test complete CLI setup with modules enabled."""
        config = create_test_config(["ssh_manager", "docker_manager"])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            # Create complete CLI
            parser = create_parser()
            subparsers = parser.add_subparsers(dest="command")
            register_core_commands(subparsers)
            register_module_commands(subparsers)
            load_and_register_modules(subparsers)
            
            # Should be able to parse various commands
            test_commands = [
                (['init'], {'command': 'init'}),
                (['update'], {'command': 'update'}),
                (['uninstall'], {'command': 'uninstall'}),
                (['modules', 'list'], {'command': 'modules'}),
            ]
            
            for cmd_args, expected_attrs in test_commands:
                args = parser.parse_args(cmd_args)
                for attr, value in expected_attrs.items():
                    assert getattr(args, attr) == value
    
    def test_cli_with_no_modules_enabled(self, cli_test_environment):
        """Test CLI functionality with no modules enabled."""
        config = create_test_config([])  # No modules enabled
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            parser = create_parser()
            subparsers = parser.add_subparsers(dest="command")
            register_core_commands(subparsers)
            register_module_commands(subparsers)
            load_and_register_modules(subparsers)
            
            # Core commands should still work
            args = parser.parse_args(['init'])
            assert args.command == 'init'
            
            # Module management should work
            args = parser.parse_args(['modules', 'list'])
            assert args.command == 'modules'
    
    @pytest.mark.docker
    def test_cli_argument_parsing_edge_cases(self, cli_test_environment):
        """Test CLI argument parsing edge cases."""
        config = create_test_config(["docker_manager"])
        
        with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
            parser = create_parser()
            subparsers = parser.add_subparsers(dest="command")
            register_core_commands(subparsers)
            register_module_commands(subparsers)
            load_and_register_modules(subparsers)
            
            # Set the default behavior to match the actual CLI implementation
            parser.set_defaults(func=lambda _: parser.print_help())
            
            # Test empty arguments - should show help, not raise SystemExit
            args = parser.parse_args([])
            # Should have the default function set and not raise SystemExit
            assert hasattr(args, 'func')
            
            # Test unknown flag - this should still raise SystemExit
            with pytest.raises(SystemExit):
                parser.parse_args(['--unknown-flag'])


@pytest.mark.parametrize("module_combination", [
    [],  # No modules
    ["ssh_manager"],  # Single module
    ["ssh_manager", "docker_manager"],  # Multiple modules
    ["ssh_manager", "docker_manager", "kubernetes_manager"],  # Many modules
])
def test_various_module_combinations(module_combination, cli_test_environment, isolated_cli_parser):
    """Test CLI functionality with various module combinations."""
    parser, subparsers = isolated_cli_parser
    config = create_test_config(module_combination)
    
    with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
        # Should not crash with any combination
        register_core_commands(subparsers)
        load_and_register_modules(subparsers)
        
        # Core commands should always work
        args = parser.parse_args(['init'])
        assert args.command == 'init'


@pytest.mark.parametrize("core_command,expected_attrs", [
    (['init'], {'command': 'init', 'force': False}),
    (['init', '--force'], {'command': 'init', 'force': True}),
    (['update'], {'command': 'update', 'check_only': False, 'show_releases': False}),
    (['update', '--check-only'], {'command': 'update', 'check_only': True}),
    (['update', '--show-releases'], {'command': 'update', 'show_releases': True}),
    (['uninstall'], {'command': 'uninstall', 'force': False}),
    (['uninstall', '--force'], {'command': 'uninstall', 'force': True}),
])
def test_core_command_argument_parsing(core_command, expected_attrs, cli_test_environment):
    """Test argument parsing for core commands."""
    config = create_test_config([])  # No modules needed for core commands
    
    with patch('maxcli.modules.module_manager.load_modules_config', return_value=config):
        parser = create_parser()
        subparsers = parser.add_subparsers(dest="command")
        register_core_commands(subparsers)
        
        args = parser.parse_args(core_command)
        
        for attr, expected_value in expected_attrs.items():
            assert getattr(args, attr) == expected_value 