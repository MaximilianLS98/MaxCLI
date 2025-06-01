"""
Module management system for MaxCLI.

This module provides functionality to:
- Dynamically load and register CLI modules based on configuration
- Manage module enable/disable state
- Provide CLI commands for module management
"""

import json
import importlib
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone

# Configuration constants
CONFIG_DIR = Path.home() / ".config" / "maxcli"
MODULES_CONFIG_FILE = CONFIG_DIR / "modules_config.json"

# Available modules and their metadata
AVAILABLE_MODULES = {
    "ssh_manager": {
        "description": "SSH connection and target management with key generation and profiles",
        "commands": ["ssh", "ssh-key", "ssh-config"]
    },
    "docker_manager": {
        "description": "Docker container management, image operations, and development environments",
        "commands": ["docker"]
    },
    "kubernetes_manager": {
        "description": "Kubernetes context switching and cluster management",
        "commands": ["kctx", "kubectl", "k8s"]
    },
    "gcp_manager": {
        "description": "Google Cloud Platform configuration and authentication management",
        "commands": ["gcp", "gcloud"]
    },
    "coolify_manager": {
        "description": "Coolify instance management through REST API",
        "commands": ["coolify"]
    },
    "setup_manager": {
        "description": "Development environment setup and configuration profiles",
        "commands": ["setup"]
    },
    "misc_manager": {
        "description": "Database backup utilities, CSV data processing, and application deployment tools",
        "commands": ["backup-db", "deploy-app", "process-csv"]
    },
    "ssh_backup": {
        "description": "SSH key backup and restore with GPG encryption",
        "commands": ["ssh-backup"]
    },
    "ssh_rsync": {
        "description": "Remote backup synchronization using rsync over SSH",
        "commands": ["rsync-backup"]
    },
    "terraform_manager": {
        "description": "Terraform infrastructure management and automation",
        "commands": ["terraform", "tf"]
    },
    "aws_manager": {
        "description": "Amazon Web Services resource management and utilities",
        "commands": ["aws"]
    },
    "database_manager": {
        "description": "Database connection management and backup utilities",
        "commands": ["db", "database"]
    },
    "monitoring": {
        "description": "System monitoring, alerting, and health check utilities",
        "commands": ["monitor", "health"]
    },
    "deployment": {
        "description": "Application deployment automation and CI/CD integration",
        "commands": ["deploy"]
    }
}

# Default enabled modules (safe defaults)
DEFAULT_ENABLED_MODULES = ["ssh_manager", "setup_manager"]


def ensure_config_directory() -> None:
    """Ensure the maxcli config directory exists with proper permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def update_module_info_if_needed(config: Dict[str, Any]) -> bool:
    """Update module_info with any missing modules or fields while preserving existing data.
    
    Args:
        config: The configuration dictionary to update.
        
    Returns:
        True if config was modified, False otherwise.
    """
    modified = False
    
    if "module_info" not in config:
        # No module_info exists, create from scratch using bootstrap-compatible format
        config["module_info"] = {}
        modified = True
    
    enabled_modules = set(config.get("enabled_modules", []))
    
    # Update or add missing modules
    for module_name, module_data in AVAILABLE_MODULES.items():
        if module_name not in config["module_info"]:
            # Add missing module with bootstrap-compatible format
            config["module_info"][module_name] = {
                "enabled": module_name in enabled_modules,
                "description": module_data["description"],
                "commands": module_data["commands"],
                "dependencies": []  # Default empty dependencies, bootstrap may override
            }
            modified = True
        else:
            # Update existing module if fields are missing or outdated
            existing = config["module_info"][module_name]
            
            # Ensure enabled field matches enabled_modules list
            should_be_enabled = module_name in enabled_modules
            if existing.get("enabled") != should_be_enabled:
                existing["enabled"] = should_be_enabled
                modified = True
            
            # Update description and commands if they've changed
            if existing.get("description") != module_data["description"]:
                existing["description"] = module_data["description"]
                modified = True
            
            if existing.get("commands") != module_data["commands"]:
                existing["commands"] = module_data["commands"]
                modified = True
            
            # Ensure dependencies field exists (don't overwrite if it exists)
            if "dependencies" not in existing:
                existing["dependencies"] = []
                modified = True
    
    return modified


def load_modules_config() -> Dict[str, Any]:
    """Load module configuration from JSON file.
    
    Returns:
        Dictionary with enabled_modules and module_info.
        Creates default config if file doesn't exist.
    """
    if not MODULES_CONFIG_FILE.exists():
        return create_default_config()
    
    try:
        with open(MODULES_CONFIG_FILE, 'r') as f:
            config: Dict[str, Any] = json.load(f)
        
        # Handle legacy format (boolean flags) - convert to new format
        if "enabled_modules" not in config:
            print("📦 Converting legacy module configuration to new format...")
            legacy_enabled = [name for name, enabled in config.items() 
                            if isinstance(enabled, bool) and enabled and name in AVAILABLE_MODULES]
            return create_config_with_modules(legacy_enabled)
        
        # Clean up any legacy boolean flags that might coexist with new format
        legacy_flags_found = False
        for module_name in list(config.keys()):
            if module_name in AVAILABLE_MODULES and isinstance(config[module_name], bool):
                del config[module_name]
                legacy_flags_found = True
        
        if legacy_flags_found:
            print("🧹 Cleaned up legacy module flags from configuration.")
        
        # Only update module_info if it's completely missing
        # This preserves existing configurations for roundtrip compatibility
        needs_update = False
        if "module_info" not in config:
            needs_update = True
        
        config_modified = False
        if needs_update:
            config_modified = update_module_info_if_needed(config)
        
        # Save if we cleaned up legacy flags or updated module_info
        if legacy_flags_found or config_modified:
            save_modules_config(config)
        
        return config
        
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load modules config: {e}")
        print("Creating default configuration.")
        return create_default_config()


def create_default_config() -> Dict[str, Any]:
    """Create default module configuration."""
    config = create_config_with_modules(DEFAULT_ENABLED_MODULES)
    save_modules_config(config)
    return config


def create_config_with_modules(enabled_modules: List[str]) -> Dict[str, Any]:
    """Create configuration with specified enabled modules using bootstrap-compatible format."""
    from datetime import datetime
    
    # Create module_info in bootstrap-compatible format
    module_info = {}
    for module_name, module_data in AVAILABLE_MODULES.items():
        module_info[module_name] = {
            "enabled": module_name in enabled_modules,
            "description": module_data["description"],
            "commands": module_data["commands"],
            "dependencies": []  # Default empty, can be customized
        }
    
    return {
        "enabled_modules": enabled_modules,
        "module_info": module_info,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bootstrap_version": "1.0.0"
    }


def save_modules_config(config: Dict[str, Any]) -> bool:
    """Save module configuration to JSON file.
    
    Args:
        config: Dictionary with enabled_modules and module_info.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        ensure_config_directory()
        
        with open(MODULES_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)
        
        return True
        
    except (IOError, OSError) as e:
        print(f"Error: Could not save modules config: {e}")
        return False


def get_enabled_modules() -> List[str]:
    """Get list of enabled module names.
    
    Returns:
        List of module names that are enabled.
    """
    config = load_modules_config()
    enabled_modules: List[str] = config.get("enabled_modules", [])
    return enabled_modules


def get_available_modules() -> Set[str]:
    """Get set of all available module names.
    
    Returns:
        Set of all known module names (both enabled and disabled).
    """
    return set(AVAILABLE_MODULES.keys())


def load_and_register_modules(subparsers) -> None:
    """Dynamically load and register enabled modules.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    enabled_modules = get_enabled_modules()
    
    if not enabled_modules:
        print("ℹ️  No modules are currently enabled.")
        print("Use 'max modules list' to see available modules.")
        print("Use 'max modules enable <module_name>' to enable modules.")
        return
    
    for module_name in enabled_modules:
        try:
            # Import the module
            module = importlib.import_module(f"maxcli.modules.{module_name}")
            
            # Register commands if the module has the register_commands function
            if hasattr(module, 'register_commands'):
                module.register_commands(subparsers)
            else:
                print(f"⚠️  Module {module_name} does not have a register_commands function.")
                
        except ModuleNotFoundError:
            print(f"⚠️  Module {module_name} not found. It may not be implemented yet.")
        except Exception as e:
            print(f"⚠️  Error loading module {module_name}: {e}")


def list_modules() -> None:
    """List all available modules and their enabled status."""
    config = load_modules_config()
    enabled_modules = set(config.get("enabled_modules", []))
    available = get_available_modules()
    module_info = config.get("module_info", AVAILABLE_MODULES)
    
    print("📦 Available CLI Modules:")
    print("=" * 70)
    
    # Calculate column width for alignment
    max_name_len = max(len(name) for name in available)
    
    for module_name in sorted(available):
        enabled = module_name in enabled_modules
        status = "✅ Enabled " if enabled else "❌ Disabled"
        description = module_info.get(module_name, {}).get("description", "No description available")
        commands = module_info.get(module_name, {}).get("commands", [])
        
        print(f"{module_name:<{max_name_len}} {status}")
        print(f"{'':>{max_name_len}} 📝 {description}")
        if commands:
            commands_str = ", ".join(commands)
            print(f"{'':>{max_name_len}} 🔧 Commands: {commands_str}")
        print()
    
    enabled_count = len(enabled_modules)
    total_count = len(available)
    print(f"📊 Status: {enabled_count}/{total_count} modules enabled")
    print("\nUse 'max modules enable <module>' or 'max modules disable <module>' to change status.")


def enable_module(module_name: str) -> bool:
    """Enable a module by name.
    
    Args:
        module_name: Name of the module to enable.
        
    Returns:
        True if module was enabled successfully, False otherwise.
    """
    available = get_available_modules()
    
    if module_name not in available:
        print(f"❌ Error: Module '{module_name}' is not available.")
        print(f"Available modules: {', '.join(sorted(available))}")
        return False
    
    config = load_modules_config()
    enabled_modules = config.get("enabled_modules", [])
    
    if module_name in enabled_modules:
        print(f"✅ Module '{module_name}' is already enabled.")
        return True
    
    # Add to enabled_modules list
    enabled_modules.append(module_name)
    config["enabled_modules"] = enabled_modules
    
    # Also update the enabled field in module_info if it exists
    if "module_info" in config and module_name in config["module_info"]:
        config["module_info"][module_name]["enabled"] = True
    
    if save_modules_config(config):
        print(f"✅ Module '{module_name}' enabled successfully.")
        
        # Show what commands are now available
        module_info = config.get("module_info", AVAILABLE_MODULES)
        commands = module_info.get(module_name, {}).get("commands", [])
        if commands:
            commands_str = ", ".join(commands)
            print(f"🔧 New commands available: {commands_str}")
        
        print("💡 Restart your CLI session or run the command again to use the new module.")
        return True
    else:
        return False


def disable_module(module_name: str) -> bool:
    """Disable a module by name.
    
    Args:
        module_name: Name of the module to disable.
        
    Returns:
        True if module was disabled successfully, False otherwise.
    """
    available = get_available_modules()
    
    if module_name not in available:
        print(f"❌ Error: Module '{module_name}' is not available.")
        print(f"Available modules: {', '.join(sorted(available))}")
        return False
    
    config = load_modules_config()
    enabled_modules = config.get("enabled_modules", [])
    
    if module_name not in enabled_modules:
        print(f"✅ Module '{module_name}' is already disabled.")
        return True
    
    # Remove from enabled_modules list
    enabled_modules.remove(module_name)
    config["enabled_modules"] = enabled_modules
    
    # Also update the enabled field in module_info if it exists
    if "module_info" in config and module_name in config["module_info"]:
        config["module_info"][module_name]["enabled"] = False
    
    if save_modules_config(config):
        print(f"✅ Module '{module_name}' disabled successfully.")
        
        # Show what commands are no longer available
        module_info = config.get("module_info", AVAILABLE_MODULES)
        commands = module_info.get(module_name, {}).get("commands", [])
        if commands:
            commands_str = ", ".join(commands)
            print(f"🚫 Commands no longer available: {commands_str}")
        
        print("💡 Restart your CLI session to complete the change.")
        return True
    else:
        return False


# CLI command handlers
def handle_list_modules(args) -> None:
    """Handle the 'modules list' command."""
    list_modules()


def handle_enable_module(args) -> None:
    """Handle the 'modules enable' command."""
    enable_module(args.module_name)


def handle_disable_module(args) -> None:
    """Handle the 'modules disable' command."""
    disable_module(args.module_name)


def register_commands(subparsers) -> None:
    """Register module management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Modules management command
    modules_parser = subparsers.add_parser(
        'modules',
        help='Manage CLI modules (enable/disable functionality)',
        description="""
Manage MaxCLI modules to customize which functionality is available.

Each module provides a specific set of commands and functionality.
You can enable or disable modules based on your needs to keep
the CLI clean and focused on what you actually use.

Module changes take effect after restarting your CLI session.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max modules list                # Show all available modules
  max modules enable docker_manager   # Enable Docker cleanup commands
  max modules disable coolify_manager # Disable Coolify commands
        """
    )
    
    modules_subparsers = modules_parser.add_subparsers(
        title="Module Management Commands",
        dest="modules_command",
        description="Choose a module management operation",
        metavar="<command>"
    )
    modules_parser.set_defaults(func=handle_list_modules)
    
    # List modules command
    list_parser = modules_subparsers.add_parser(
        'list',
        help='List all available modules and their status',
        description="""
Display all available CLI modules and whether they are currently enabled or disabled.

This shows:
- All known modules in the system
- Their current enabled/disabled status
- Description of each module's functionality
- Commands provided by each module
- Instructions for enabling/disabling modules
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max modules list                # Show detailed module status
        """
    )
    list_parser.set_defaults(func=handle_list_modules)
    
    # Enable module command
    enable_parser = modules_subparsers.add_parser(
        'enable',
        help='Enable a module',
        description="""
Enable a specific module to make its commands available in the CLI.

The module must be available in the system. Use 'max modules list'
to see all available modules.

Changes take effect after restarting your CLI session.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max modules enable docker_manager    # Enable Docker cleanup commands
  max modules enable coolify_manager   # Enable Coolify management
        """
    )
    enable_parser.add_argument('module_name', help='Name of the module to enable')
    enable_parser.set_defaults(func=handle_enable_module)
    
    # Disable module command
    disable_parser = modules_subparsers.add_parser(
        'disable',
        help='Disable a module',
        description="""
Disable a specific module to remove its commands from the CLI.

This helps keep the CLI clean by hiding functionality you don't use.

Changes take effect after restarting your CLI session.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max modules disable docker_manager   # Disable Docker cleanup commands
  max modules disable misc_manager     # Disable miscellaneous commands
        """
    )
    disable_parser.add_argument('module_name', help='Name of the module to disable')
    disable_parser.set_defaults(func=handle_disable_module) 