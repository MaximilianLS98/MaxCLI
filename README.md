# MaxCLI - A Modular Personal Development CLI

MaxCLI is a powerful, modular command-line interface designed for developers and DevOps engineers. It provides a collection of useful tools and utilities organized into modules that can be enabled or disabled based on your needs.

## 🚀 Key Features

- **Modular Architecture**: Enable only the functionality you need
- **Dynamic Loading**: Modules are loaded based on your configuration
- **Personal Configuration**: Customizable settings stored in `~/.config/maxcli/`
- **Comprehensive Tools**: SSH management, Docker utilities, Kubernetes helpers, GCP tools, and more
- **Bootstrap Integration**: Easy setup and installation via bootstrap script

## 📦 Available Modules

| Module               | Description                          | Key Commands                                         |
| -------------------- | ------------------------------------ | ---------------------------------------------------- |
| `ssh_manager`        | SSH connection and target management | `ssh list-targets`, `ssh add-target`, `ssh connect`  |
| `ssh_backup`         | SSH-based backup operations          | `ssh-backup`, `ssh-restore`                          |
| `ssh_rsync`          | SSH rsync synchronization            | `ssh-rsync-push`, `ssh-rsync-pull`                   |
| `coolify_manager`    | Coolify instance management          | `coolify status`, `coolify services`, `coolify apps` |
| `gcp_manager`        | Google Cloud Platform utilities      | `switch-config`, `create-config`, `list-configs`     |
| `docker_manager`     | Docker system management             | `docker clean --extensive`, `docker clean --minimal` |
| `kubernetes_manager` | Kubernetes context switching         | `kctx <context>`                                     |
| `setup_manager`      | Development environment setup        | `setup minimal`, `setup dev-full`, `setup apps`      |
| `misc_manager`       | Miscellaneous utilities              | `backup-db`, `deploy-app`                            |

## 🛠 Installation

### Bootstrap Installation (Recommended)

```bash
# Download and run the bootstrap script
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash

# Or with custom options
curl -fsSL https://raw.githubusercontent.com/yourusername/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,setup_manager,docker_manager"
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/maxcli.git
cd maxcli

# Install dependencies
pip install -r requirements.txt

# Install MaxCLI
pip install -e .

# Initialize configuration
max init

# Configure modules
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

Manage Google Cloud Platform configurations.

```bash
# List available configurations
max list-configs

# Switch configurations
max switch-config production

# Create new configuration
max create-config development
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

### Check Module Status

```bash
# List all modules and their status
max modules list

# Check configuration file
cat ~/.config/maxcli/max_modules.json
```

### Reset Configuration

```bash
# Reinitialize personal configuration
max init --force

# Reset module configuration (re-run bootstrap)
rm ~/.config/maxcli/max_modules.json
max modules list  # This will recreate with defaults
```

### Common Issues

1. **Command not found**: The module providing the command is disabled

    ```bash
    max modules list
    max modules enable <module_name>
    ```

2. **Import errors**: Missing dependencies for a module

    ```bash
    pip install -r requirements.txt
    ```

3. **Configuration issues**: Reset configuration files
    ```bash
    rm -rf ~/.config/maxcli/
    max init
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
