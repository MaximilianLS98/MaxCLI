# Extending MaxCLI

This guide explains how to create new modules and extend MaxCLI functionality using the modular architecture.

## Module Architecture

MaxCLI uses a plugin-based modular system where each module is a self-contained Python file that registers its commands with the main CLI.

### Module Structure

Every module follows this basic structure:

```python
"""
Module docstring describing functionality.
"""

import argparse
from typing import Any

def register_commands(subparsers) -> None:
    """Register commands for this module.

    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Command registration logic here
    pass

# Command implementation functions
def my_command(args) -> None:
    """Command implementation."""
    pass
```

## Creating a New Module

### 1. Create the Module File

Create a new file in `maxcli/modules/` following the naming convention:

```bash
touch maxcli/modules/my_new_manager.py
```

### 2. Implement the Module

Here's a complete example of a new module for managing Jupyter notebooks:

```python
"""
Jupyter notebook management module.

This module provides utilities for managing Jupyter notebooks and JupyterLab
environments, including server management and notebook operations.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any


def register_commands(subparsers) -> None:
    """Register Jupyter management commands.

    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Main jupyter command parser
    jupyter_parser = subparsers.add_parser(
        'jupyter',
        help='Manage Jupyter notebooks and JupyterLab',
        description="""
Manage Jupyter notebooks and JupyterLab environments.

This module provides utilities for:
- Starting and stopping Jupyter servers
- Managing notebook directories
- Installing and managing kernels
- Notebook file operations

All operations respect virtual environments and project isolation.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max jupyter start               # Start JupyterLab in current directory
  max jupyter start ~/projects    # Start in specific directory
  max jupyter stop                # Stop running Jupyter server
  max jupyter list-kernels        # Show available kernels
  max jupyter install-kernel myenv # Install kernel from virtual environment
        """
    )

    # Subcommands for jupyter operations
    jupyter_subparsers = jupyter_parser.add_subparsers(
        title="Jupyter Commands",
        dest="jupyter_command",
        description="Choose a Jupyter operation",
        metavar="<command>"
    )
    jupyter_parser.set_defaults(func=lambda _: jupyter_parser.print_help())

    # Start command
    start_parser = jupyter_subparsers.add_parser(
        'start',
        help='Start JupyterLab server',
        description="""
Start a JupyterLab server in the specified directory.

If no directory is provided, starts in the current directory.
The server will open in your default browser automatically.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max jupyter start               # Start in current directory
  max jupyter start ~/projects    # Start in specific directory
  max jupyter start . --port 8889 # Start on custom port
        """
    )
    start_parser.add_argument('directory', nargs='?', default='.',
                            help='Directory to start Jupyter in (default: current)')
    start_parser.add_argument('--port', type=int, default=8888,
                            help='Port to run on (default: 8888)')
    start_parser.add_argument('--no-browser', action='store_true',
                            help="Don't open browser automatically")
    start_parser.set_defaults(func=start_jupyter)

    # Stop command
    stop_parser = jupyter_subparsers.add_parser(
        'stop',
        help='Stop running Jupyter server',
        description="""
Stop the currently running Jupyter server.

This will gracefully shut down the server and close any open notebooks.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max jupyter stop                # Stop the running server
        """
    )
    stop_parser.set_defaults(func=stop_jupyter)

    # List kernels command
    kernels_parser = jupyter_subparsers.add_parser(
        'list-kernels',
        help='List available Jupyter kernels',
        description="""
Display all available Jupyter kernels installed on the system.

Shows kernel names, their Python versions, and installation paths.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max jupyter list-kernels        # Show all available kernels
        """
    )
    kernels_parser.set_defaults(func=list_kernels)

    # Install kernel command
    install_parser = jupyter_subparsers.add_parser(
        'install-kernel',
        help='Install kernel from virtual environment',
        description="""
Install a Jupyter kernel from a virtual environment.

This makes the virtual environment available as a kernel in Jupyter,
allowing you to use project-specific dependencies in notebooks.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max jupyter install-kernel myproject    # Install kernel named 'myproject'
  max jupyter install-kernel myproject --env ~/venvs/myproject # Custom env path
        """
    )
    install_parser.add_argument('name', help='Name for the kernel')
    install_parser.add_argument('--env', help='Path to virtual environment (default: activate current)')
    install_parser.set_defaults(func=install_kernel)


def start_jupyter(args) -> None:
    """Start JupyterLab server."""
    directory = Path(args.directory).expanduser().resolve()

    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return

    if not directory.is_dir():
        print(f"❌ Path is not a directory: {directory}")
        return

    print(f"🚀 Starting JupyterLab in {directory}")
    print(f"📡 Port: {args.port}")

    # Build command
    cmd = [
        'jupyter', 'lab',
        '--port', str(args.port),
        '--notebook-dir', str(directory)
    ]

    if args.no_browser:
        cmd.append('--no-browser')

    try:
        # Run in the specified directory
        subprocess.run(cmd, cwd=directory, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start JupyterLab: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ JupyterLab not found. Install with: pip install jupyterlab")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 JupyterLab stopped")


def stop_jupyter(args) -> None:
    """Stop running Jupyter server."""
    try:
        result = subprocess.run(['jupyter', 'lab', 'stop'],
                              capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print("✅ Jupyter server stopped")
        else:
            print("❌ No running Jupyter server found or failed to stop")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
    except FileNotFoundError:
        print("❌ Jupyter command not found")
        sys.exit(1)


def list_kernels(args) -> None:
    """List available Jupyter kernels."""
    try:
        result = subprocess.run(['jupyter', 'kernelspec', 'list'],
                              capture_output=True, text=True, check=True)

        print("📋 Available Jupyter kernels:")
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to list kernels: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Jupyter command not found")
        sys.exit(1)


def install_kernel(args) -> None:
    """Install kernel from virtual environment."""
    kernel_name = args.name

    # Determine virtual environment path
    if args.env:
        venv_path = Path(args.env).expanduser().resolve()
        python_path = venv_path / 'bin' / 'python'
    else:
        # Use current environment
        python_path = sys.executable
        venv_path = Path(python_path).parent.parent

    if not python_path.exists():
        print(f"❌ Python not found at: {python_path}")
        return

    print(f"📦 Installing kernel '{kernel_name}' from {venv_path}")

    try:
        # Install ipykernel in the target environment
        subprocess.run([str(python_path), '-m', 'pip', 'install', 'ipykernel'],
                      check=True, capture_output=True)

        # Install the kernel
        subprocess.run([
            str(python_path), '-m', 'ipykernel', 'install',
            '--user', '--name', kernel_name,
            '--display-name', f'Python ({kernel_name})'
        ], check=True, capture_output=True)

        print(f"✅ Kernel '{kernel_name}' installed successfully")
        print(f"🎯 Available in Jupyter as 'Python ({kernel_name})'")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install kernel: {e}")
        sys.exit(1)
```

### 3. Update Module Configuration

Add your new module to the module information in the bootstrap script or update the existing configuration:

```bash
# Add to ~/.config/maxcli/modules_config.json
{
    "enabled_modules": ["ssh_manager", "setup_manager", "jupyter_manager"],
    "module_info": {
        "jupyter_manager": {
            "description": "Jupyter notebook and JupyterLab management utilities",
            "commands": ["jupyter"]
        }
    }
}
```

### 4. Enable Your Module

Enable your new module:

```bash
max modules enable jupyter_manager
```

### 5. Test Your Module

Test the new functionality:

```bash
max --help                    # Should show jupyter command
max jupyter --help            # Should show jupyter subcommands
max jupyter start             # Test the functionality
```

## Advanced Module Features

### Importing from Existing Command Modules

You can import and reuse functions from the existing command modules:

```python
from maxcli.commands.docker import docker_clean
from maxcli.system import run_command
from maxcli.interactive import confirm
```

### Configuration Integration

Access user configuration in your module:

```python
from maxcli.config import load_config

def my_command(args):
    config = load_config()
    user_name = config.get('git', {}).get('name', 'Unknown')
    print(f"Hello, {user_name}!")
```

### Interactive Features

Use the interactive utilities for better UX:

```python
from maxcli.interactive import confirm, get_user_choice

def dangerous_operation(args):
    if not confirm("This will delete files. Continue?"):
        print("Operation cancelled")
        return

    # Proceed with operation
    run_dangerous_task()
```

### Error Handling

Follow the established error handling patterns:

```python
import sys
from pathlib import Path

def my_command(args):
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    try:
        # Operation that might fail
        result = risky_operation(file_path)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        sys.exit(1)
```

## Best Practices

### 1. Module Naming

- Use descriptive names ending with `_manager`
- Keep names concise but clear
- Examples: `jupyter_manager`, `aws_manager`, `database_manager`

### 2. Command Structure

- Use clear, hierarchical subcommands
- Provide comprehensive help text
- Include usage examples in epilogs
- Use consistent argument naming

### 3. Documentation

- Start with a module docstring explaining purpose
- Document all functions with docstrings
- Include type hints for better code clarity
- Provide examples in help text

### 4. Error Handling

- Use emoji icons for visual feedback (✅ ❌ ⚠️)
- Exit with appropriate codes (0 for success, 1 for error)
- Provide helpful error messages
- Handle missing dependencies gracefully

### 5. User Experience

- Confirm destructive operations
- Show progress for long-running tasks
- Provide meaningful success/failure messages
- Support interactive and non-interactive modes

## Testing Your Module

### Manual Testing

```bash
# Test module loading
max modules list

# Test command structure
max your-command --help
max your-command subcommand --help

# Test functionality
max your-command subcommand
```

### Module Development Workflow

1. Create module file
2. Add basic structure and one command
3. Test with `max modules enable your_module`
4. Iterate on functionality
5. Add comprehensive help and error handling
6. Test edge cases and error conditions
7. Update documentation

## Contributing Modules

When contributing new modules to MaxCLI:

1. Follow the established patterns and conventions
2. Include comprehensive tests and documentation
3. Ensure the module handles errors gracefully
4. Provide clear examples and help text
5. Consider making the module optional by default
6. Update the README with new functionality

## Examples of Extension Ideas

### Potential New Modules

- **aws_manager**: AWS CLI configuration and credential management
- **database_manager**: Database backup, restore, and migration utilities
- **project_manager**: Project scaffolding and template management
- **monitoring_manager**: System monitoring and alerting setup
- **backup_manager**: File and system backup automation
- **network_manager**: Network testing and configuration utilities
- **security_manager**: Security scanning and certificate management

Each module can be developed independently and enabled based on user needs, keeping the CLI lean while providing powerful functionality when required.
