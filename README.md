# MaxCLI - A Modular Personal Development CLI

MaxCLI is a powerful, modular command-line interface designed for developers and DevOps engineers. It provides a collection of useful tools and utilities organized into modules that can be enabled or disabled based on your needs.

## 🚀 Key Features

- **Modular Architecture**: Enable only the functionality you need
- **Dynamic Loading**: Modules are loaded based on your configuration
- **Personal Configuration**: Customizable settings stored in `~/.config/maxcli/`
- **Comprehensive Tools**: SSH management, Docker utilities, Kubernetes helpers, GCP tools, and more
- **Smart Bootstrap**: Intelligent installation supporting both standalone and local modes

## 📦 Available Modules

| Module               | Description                          | Key Commands                                                |
| -------------------- | ------------------------------------ | ----------------------------------------------------------- |
| `ssh_manager`        | SSH connection and target management | `ssh list-targets`, `ssh add-target`, `ssh connect`         |
| `ssh_backup`         | SSH-key backup operations            | `ssh-backup export`, `ssh-backup import`                    |
| `ssh_rsync`          | SSH backup rsync synchronization     | `ssh-rsync upload-backup`, `ssh-rsync download-backup`      |
| `coolify_manager`    | Coolify instance management          | `coolify status`, `coolify services`, `coolify apps`        |
| `gcp_manager`        | Google Cloud Platform utilities      | `gcp config switch`, `gcp config create`, `gcp config list` |
| `docker_manager`     | Docker system management             | `docker clean --extensive`, `docker clean --minimal`        |
| `kubernetes_manager` | Kubernetes context switching         | `kctx <context>`                                            |
| `setup_manager`      | Development environment setup        | `setup minimal`, `setup dev-full`, `setup apps`             |
| `misc_manager`       | Miscellaneous utilities              | `backup-db`, `deploy-app`                                   |

## 🛠 Installation

MaxCLI supports two installation methods: **Standalone** (recommended for quick setup) and **Local** (recommended for development or customization).

### 🚀 Standalone Installation (Recommended)

The standalone method automatically downloads and installs MaxCLI with a single command:

```bash
# Basic installation with interactive module selection
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash

# Quick installation with preset modules
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,setup_manager,docker_manager"

# Installation with all available modules
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,ssh_backup,ssh_rsync,docker_manager,kubernetes_manager,gcp_manager,coolify_manager,setup_manager,misc_manager"
```

#### Standalone Installation Options

| Option                    | Description                                | Example                                  |
| ------------------------- | ------------------------------------------ | ---------------------------------------- |
| `--modules=LIST`          | Preset modules to enable (comma-separated) | `--modules "ssh_manager,docker_manager"` |
| `--github-repo=USER/REPO` | Install from a different repository/fork   | `--github-repo "yourfork/maxcli"`        |
| `--github-branch=BRANCH`  | Install from a specific branch             | `--github-branch "development"`          |
| `--help`                  | Show detailed help and options             | `--help`                                 |

#### Advanced Standalone Examples

```bash
# Install from a fork
curl -fsSL https://raw.githubusercontent.com/yourfork/maxcli/main/bootstrap.sh | bash -s -- --github-repo "yourfork/maxcli"

# Install from development branch
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/development/bootstrap.sh | bash -s -- --github-branch "development"

# Install specific modules from a fork
curl -fsSL https://raw.githubusercontent.com/yourfork/maxcli/main/bootstrap.sh | bash -s -- --github-repo "yourfork/maxcli" --modules "ssh_manager,custom_module"
```

### 🔧 Local Installation

The local method gives you full control and is ideal for development or customization:

```bash
# Clone the repository
git clone https://github.com/yourusername/maxcli.git
cd maxcli

# Run the bootstrap script
./bootstrap.sh

# Or with preset modules
./bootstrap.sh --modules "ssh_manager,setup_manager,docker_manager"

# Force fresh download even with local files
./bootstrap.sh --force-download
```

#### Local Installation Options

All standalone options plus:

| Option             | Description                                    | Example                           |
| ------------------ | ---------------------------------------------- | --------------------------------- |
| `--force-download` | Download fresh files even if local files exist | `./bootstrap.sh --force-download` |

### 🆘 Bootstrap Help

Get detailed information about all available options:

```bash
# Download and show help
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --help

# Or with local installation
./bootstrap.sh --help
```

### 📋 Module Presets

Here are some common module combinations for different use cases:

```bash
# Frontend Developer
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "setup_manager,ssh_manager,docker_manager"

# DevOps Engineer
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,ssh_backup,ssh_rsync,docker_manager,kubernetes_manager,gcp_manager"

# Full Stack Developer
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,setup_manager,docker_manager,gcp_manager,misc_manager"

# Minimalist Setup
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,setup_manager"

# Power User (All Modules)
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,ssh_backup,ssh_rsync,docker_manager,kubernetes_manager,gcp_manager,coolify_manager,setup_manager,misc_manager"
```

### ✅ Post-Installation

After installation, follow these steps:

```bash
# 1. Restart your terminal or reload your shell
source ~/.zshrc

# 2. Initialize your personal configuration
max init

# 3. Verify installation
max --help

# 4. Check enabled modules
max modules list

# 5. Test a command (if ssh_manager is enabled)
max ssh list-targets
```

### 🔄 Manual Installation (Alternative)

If you prefer manual control over the installation process:

```bash
# Clone the repository
git clone https://github.com/yourusername/maxcli.git
cd maxcli

# Create virtual environment
python3 -m venv ~/.venvs/maxcli
source ~/.venvs/maxcli/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install MaxCLI
pip install -e .

# Initialize configuration
max init

# Configure modules manually
max modules list
max modules enable ssh_manager
max modules enable docker_manager
```

## ⚙️ Configuration

### Personal Configuration

Run `max init` to set up your personal configuration:

```bash
max init
```

This creates `~/.config/maxcli/config.json` with your:

- Git username and email
- Dotfiles repository URL
- GCP project mappings
- Coolify instance details

### Module Configuration

Modules are configured in `~/.config/maxcli/max_modules.json`:

```json
{
	"enabled_modules": [
		"ssh_manager",
		"setup_manager",
		"docker_manager",
		"gcp_manager",
		"coolify_manager"
	],
	"module_info": {
		"ssh_manager": {
			"enabled": true,
			"description": "SSH connection and target management",
			"commands": ["ssh"],
			"dependencies": []
		},
		"docker_manager": {
			"enabled": true,
			"description": "Docker system management and cleanup",
			"commands": ["docker"],
			"dependencies": ["docker"]
		}
	},
	"bootstrap_version": "1.0.0",
	"created_at": "2024-01-20T10:30:00Z"
}
```

## 🔧 Module Management

### List Available Modules

```bash
max modules list
```

Output example:

```
📦 Available CLI Modules:
==================================================
ssh_manager        ✅ Enabled
docker_manager     ✅ Enabled
coolify_manager    ❌ Disabled
gcp_manager        ✅ Enabled
kubernetes_manager ❌ Disabled
setup_manager      ✅ Enabled
ssh_backup         ❌ Disabled
ssh_rsync          ❌ Disabled
misc_manager       ❌ Disabled
```

### Enable/Disable Modules

```bash
# Enable a module
max modules enable kubernetes_manager

# Disable a module
max modules disable ssh_backup

# Enable multiple modules
max modules enable ssh_backup ssh_rsync misc_manager
```

## 📚 Module Documentation

### SSH Manager (`ssh_manager`)

Manage SSH connections and targets efficiently.

```bash
# Add SSH targets
max ssh add-target prod ubuntu 192.168.1.100
max ssh add-target staging deploy 10.0.0.50 --port 2222

# List all targets
max ssh list-targets

# Connect to targets
max ssh connect prod
max ssh connect staging
```

### Docker Manager (`docker_manager`)

Manage Docker system resources and perform cleanup operations.

```bash
# Extensive cleanup (removes all unused resources)
max docker clean --extensive

# Minimal cleanup (preserves recent items)
max docker clean --minimal

# Default cleanup (defaults to minimal for safety)
max docker clean
```

### Setup Manager (`setup_manager`)

Set up development environments with different profiles.

```bash
# Basic terminal and git setup
max setup minimal

# Full development environment
max setup dev-full

# GUI applications
max setup apps
```

### GCP Manager (`gcp_manager`)

Manage Google Cloud Platform configurations and authentication with seamless switching.

```bash
# List available configurations
max gcp config list

# Switch configurations (with automatic ADC and quota project switching)
max gcp config switch production

# Create new configuration (with full authentication setup)
max gcp config create development

# Interactive mode - choose from menu
max gcp config switch
```

### Coolify Manager (`coolify_manager`)

Manage Coolify instances and applications.

```bash
# Check instance health
max coolify health

# View status overview
max coolify status

# Manage services
max coolify services list
max coolify services restart my-service

# Manage applications
max coolify apps list
max coolify apps deploy my-app
```

## 🏗 Creating Custom Modules

### Module Structure

Create a new module in `maxcli/modules/`:

```python
# maxcli/modules/my_module.py
"""
My Custom Module

This module provides custom functionality for my specific needs.
"""

import argparse


def register_commands(subparsers) -> None:
    """Register commands for this module."""
    parser = subparsers.add_parser(
        'my-command',
        help='Description of my command',
        description='Detailed description of what this command does.'
    )

    parser.add_argument('--option', help='Command option')
    parser.set_defaults(func=my_command_function)


def my_command_function(args):
    """Implementation of my command."""
    print(f"Running my command with option: {args.option}")
```

### Module Registration

Add your module to the configuration:

```bash
max modules enable my_module
```

Or manually edit `~/.config/maxcli/max_modules.json`:

```json
{
	"enabled_modules": ["my_module"],
	"module_info": {
		"my_module": {
			"enabled": true,
			"description": "My custom functionality",
			"commands": ["my-command"],
			"dependencies": []
		}
	}
}
```

## 🔍 Troubleshooting

### Installation Issues

#### Bootstrap Script Problems

```bash
# Get help with bootstrap options
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --help

# Test standalone download capability
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager"

# Force fresh download (clears any cached/problematic files)
./bootstrap.sh --force-download

# Use a different repository/fork
curl -fsSL https://raw.githubusercontent.com/yourfork/maxcli/main/bootstrap.sh | bash -s -- --github-repo "yourfork/maxcli"
```

#### Network/Download Issues

```bash
# Manual verification of download URLs
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/requirements.txt
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/main.py

# Check if repository archive is accessible
curl -fsSL https://github.com/yourusername/maxcli/archive/main.tar.gz | tar -tz | head -10
```

#### PATH and Shell Issues

```bash
# Verify max command is in PATH
which max

# Manually add to PATH if needed
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Check virtual environment
ls -la ~/.venvs/maxcli/bin/python

# Test the wrapper script directly
~/bin/max --help
```

### Runtime Issues

#### Check Module Status

```bash
# List all modules and their status
max modules list

# Check configuration file
cat ~/.config/maxcli/max_modules.json

# Verify Python environment
~/.venvs/maxcli/bin/python -c "import questionary; print('Dependencies OK')"
```

#### Reset Configuration

```bash
# Reinitialize personal configuration
max init --force

# Reset module configuration (re-run bootstrap)
rm ~/.config/maxcli/max_modules.json
max modules list  # This will recreate with defaults

# Complete reinstallation
rm -rf ~/.venvs/maxcli ~/.config/maxcli ~/bin/max
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash
```

### Common Issues

1. **Command not found**: The module providing the command is disabled

    ```bash
    max modules list
    max modules enable <module_name>
    ```

2. **Bootstrap fails with "files not found"**: You're running standalone but network issues prevent download

    ```bash
    # Try with explicit repo and branch
    curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --github-repo "yourusername/maxcli" --github-branch "main"

    # Or clone locally first
    git clone https://github.com/yourusername/maxcli.git
    cd maxcli
    ./bootstrap.sh
    ```

3. **Import errors**: Missing dependencies for a module

    ```bash
    # Reinstall in virtual environment
    source ~/.venvs/maxcli/bin/activate
    pip install -r requirements.txt

    # Or force fresh installation
    ./bootstrap.sh --force-download
    ```

4. **Permission errors**: Installation directory not writable

    ```bash
    # Ensure directories are writable
    mkdir -p ~/bin ~/.config/maxcli ~/.venvs
    chmod 755 ~/bin ~/.config/maxcli ~/.venvs

    # Re-run installation
    ./bootstrap.sh --force-download
    ```

5. **Virtual environment issues**: Python environment corrupted

    ```bash
    # Remove and recreate virtual environment
    rm -rf ~/.venvs/maxcli
    python3 -m venv ~/.venvs/maxcli
    source ~/.venvs/maxcli/bin/activate
    pip install -r requirements.txt

    # Or use bootstrap to recreate everything
    ./bootstrap.sh --force-download
    ```

6. **Configuration issues**: Reset configuration files

    ```bash
    rm -rf ~/.config/maxcli/
    max init
    ```

7. **Module not loading**: Check if module is enabled and dependencies are met

    ```bash
    max modules list
    max modules enable <module_name>

    # Check specific module dependencies
    cat ~/.config/maxcli/max_modules.json | grep -A 5 "<module_name>"
    ```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Add debug output to bootstrap
bash -x ./bootstrap.sh --modules "ssh_manager"

# Check Python import paths
~/.venvs/maxcli/bin/python -c "import sys; print('\n'.join(sys.path))"

# Verify maxcli package location
~/.venvs/maxcli/bin/python -c "import maxcli; print(maxcli.__file__)"
```

## 🔧 Development

### Requirements

- Python 3.8+
- pip or pipenv for dependency management

### Development Setup

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/maxcli.git
cd maxcli
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 maxcli/
mypy maxcli/
```

### Adding Dependencies

For modules with external dependencies, add them to `requirements.txt` and document them in the module's docstring.

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your module or improvements
4. Write tests
5. Submit a pull request

## 📞 Support

- Create an issue on GitHub
- Check the troubleshooting section
- Review module documentation

if for some reason the max command only responds with mock responses after running the test_bootstrap.sh script, you can run the following command to reset the max command to the original state:

```bash
cp -r maxcli ~/.local/lib/python/
```
