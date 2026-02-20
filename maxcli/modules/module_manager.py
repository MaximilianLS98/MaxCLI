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
        "description": "Complete SSH management: connections, keys, backups, and file transfers with GPG encryption and rsync",
        "commands": ["ssh"]
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
    "config_manager": {
        "description": "Personal configuration management with init, backup, and restore functionality",
        "commands": ["config"]
    },
    "git_manager": {
        "description": "Simplified Git operations with safety checks: WIP commits, branch cleanup, safe force push, and sync workflows",
        "commands": ["git"],
        "dependencies": ["GitPython"]
    },
    "devtools_manager": {
        "description": "Developer utilities: JWT decoding, base64 operations, and other common development tools",
        "commands": ["decode"]
    }
}

# Default enabled modules (safe defaults)
DEFAULT_ENABLED_MODULES = ["ssh_manager", "setup_manager", "config_manager", "git_manager", "devtools_manager"]


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
    
    # Handle legacy module consolidation
    legacy_ssh_modules_found = []
    ssh_manager_enabled = False
    
    for module_name in enabled_modules:
        # Check for legacy SSH modules that have been consolidated
        if module_name in ['ssh_backup', 'ssh_rsync']:
            legacy_ssh_modules_found.append(module_name)
            continue
        elif module_name == 'ssh_manager':
            ssh_manager_enabled = True
        
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
    
    # Handle legacy SSH module consolidation
    if legacy_ssh_modules_found:
        print(f"📋 Legacy SSH modules detected: {', '.join(legacy_ssh_modules_found)}")
        if ssh_manager_enabled:
            print("✅ ssh_manager is enabled and provides all SSH functionality (backup, rsync, etc.)")
            print("💡 Run 'max modules list' to see current module status")
        else:
            print("💡 These modules have been consolidated into 'ssh_manager'")
            print("🔧 To get SSH functionality, enable ssh_manager: max modules enable ssh_manager")
            print("🧹 Clean up old modules: max modules disable ssh_backup ssh_rsync")


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


def check_and_install_python_dependencies(module_name: str) -> bool:
    """Check and install Python dependencies for a module.
    
    Args:
        module_name: Name of the module to check dependencies for.
        
    Returns:
        True if dependencies are satisfied, False otherwise.
    """
    import subprocess
    import sys
    from pathlib import Path
    
    # Define Python dependencies for modules
    python_dependencies = {
        "git_manager": ["GitPython>=3.1.0"]
    }
    
    if module_name not in python_dependencies:
        return True  # No Python dependencies to check
    
    deps = python_dependencies[module_name]
    missing_deps = []
    
    # Check which dependencies are missing
    for dep in deps:
        dep_name = dep.split(">=")[0].split("==")[0]  # Extract package name
        try:
            __import__(dep_name.lower())  # Try to import (GitPython imports as 'git')
            if dep_name == "GitPython":
                __import__("git")  # GitPython imports as 'git'
        except ImportError:
            missing_deps.append(dep)
    
    if not missing_deps:
        return True  # All dependencies satisfied
    
    # Try to install missing dependencies
    print(f"🔧 Installing Python dependencies for {module_name}...")
    
    # Find MaxCLI virtual environment
    venv_path = Path.home() / ".venvs" / "maxcli"
    pip_path = venv_path / "bin" / "pip"
    
    if not pip_path.exists():
        print(f"❌ MaxCLI virtual environment not found at {venv_path}")
        print("💡 Dependencies cannot be automatically installed.")
        print(f"🔧 Please install manually: pip install {' '.join(missing_deps)}")
        return False
    
    # Install dependencies using MaxCLI's pip
    for dep in missing_deps:
        print(f"📦 Installing {dep}...")
        try:
            result = subprocess.run(
                [str(pip_path), "install", dep],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e.stderr}")
            print(f"🔧 You can install it manually with:")
            print(f"   source ~/.venvs/maxcli/bin/activate")
            print(f"   pip install {dep}")
            return False
    
    return True


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
    
    # Check and install Python dependencies before enabling
    if not check_and_install_python_dependencies(module_name):
        print(f"❌ Failed to install dependencies for '{module_name}'. Module not enabled.")
        print("💡 Please resolve dependency issues and try again.")
        return False
    
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
    
    # Handle legacy SSH modules that have been consolidated
    if module_name in ['ssh_backup', 'ssh_rsync']:
        config = load_modules_config()
        enabled_modules = config.get("enabled_modules", [])
        
        if module_name in enabled_modules:
            # Remove from enabled_modules list
            enabled_modules.remove(module_name)
            config["enabled_modules"] = enabled_modules
            
            # Also update the enabled field in module_info if it exists
            if "module_info" in config and module_name in config["module_info"]:
                config["module_info"][module_name]["enabled"] = False
            
            if save_modules_config(config):
                print(f"✅ Legacy module '{module_name}' disabled successfully.")
                print(f"💡 This functionality is now available in 'ssh_manager' module")
                return True
            else:
                return False
        else:
            print(f"✅ Legacy module '{module_name}' is already disabled.")
            print(f"💡 This functionality is now available in 'ssh_manager' module")
            return True
    
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
    if hasattr(args, 'module_names') and args.module_names:
        # Handle multiple modules
        for module_name in args.module_names:
            disable_module(module_name)
    else:
        # Handle single module (legacy compatibility)
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
        help='Disable one or more modules',
        description="""
Disable specific modules to remove their commands from the CLI.

You can disable multiple modules at once by providing multiple names.
This helps keep the CLI clean by hiding functionality you don't use.

Changes take effect after restarting your CLI session.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max modules disable docker_manager   # Disable Docker cleanup commands
  max modules disable misc_manager     # Disable miscellaneous commands
  max modules disable ssh_backup ssh_rsync  # Disable multiple legacy modules
        """
    )
    disable_parser.add_argument('module_names', nargs='+', help='Name(s) of the module(s) to disable')
    disable_parser.set_defaults(func=handle_disable_module) 