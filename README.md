# MaxCLI - A Modular Personal Development CLI

MaxCLI is a powerful, modular command-line interface designed for developers and DevOps engineers. It provides a collection of useful tools and utilities organized into modules that can be enabled or disabled based on your needs.

## 🚀 Key Features

- **Modular Architecture**: Enable only the functionality you need
- **Dynamic Loading**: Modules are loaded based on your configuration
- **Personal Configuration**: Customizable settings stored in `~/.config/maxcli/`
- **Comprehensive Tools**: SSH management, Docker utilities, Kubernetes helpers, GCP tools, and more
- **Smart Bootstrap**: Intelligent installation supporting both standalone and local modes

## 📦 Available Modules

| Module               | Description                                                                                 | Key Commands                                                                                                                         |
| -------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `ssh_manager`        | Complete SSH management: connections, keys, backups, and file transfers with GPG encryption | `ssh targets add/list`, `ssh connect`, `ssh generate-keypair`, `ssh backup export/import`, `ssh rsync upload-backup/download-backup` |
| `docker_manager`     | Docker container management, image operations, and development environments                 | `docker clean --extensive`, `docker clean --minimal`                                                                                 |
| `kubernetes_manager` | Kubernetes context switching and cluster management                                         | `kctx <context>`, `kubectl`, `k8s`                                                                                                   |
| `gcp_manager`        | Google Cloud Platform configuration and authentication management                           | `gcp config switch/create/list`, `gcloud`                                                                                            |
| `coolify_manager`    | Coolify instance management through REST API                                                | `coolify health`, `coolify status`, `coolify services`, `coolify apps`                                                               |
| `setup_manager`      | Development environment setup and configuration profiles                                    | `setup minimal`, `setup dev-full`, `setup apps`                                                                                      |
| `misc_manager`       | Database backup utilities, CSV data processing, and application deployment tools            | `backup-db`, `deploy-app`, `process-csv`                                                                                             |
| `config_manager`     | Personal configuration management with init, backup, and restore functionality              | `config init`, `config backup`, `config restore`                                                                                     |

## 🛠 Installation

MaxCLI supports two installation methods: **Standalone** (recommended for quick setup) and **Local** (recommended for development or customization).

### 🚀 Standalone Installation (Recommended)

The standalone method automatically downloads and installs MaxCLI with a single command:

```bash
# Basic installation with interactive module selection
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash

# Quick installation with preset modules
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,setup_manager,docker_manager"

# Installation with all available modules
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,docker_manager,kubernetes_manager,gcp_manager,coolify_manager,setup_manager,misc_manager,config_manager"
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
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/development/bootstrap.sh | bash -s -- --github-branch "development"

# Install specific modules from a fork
curl -fsSL https://raw.githubusercontent.com/yourfork/maxcli/main/bootstrap.sh | bash -s -- --github-repo "yourfork/maxcli" --modules "ssh_manager,custom_module"
```

### 🔧 Local Installation

The local method gives you full control and is ideal for development or customization:

```bash
# Clone the repository
git clone https://github.com/maximilianls98/maxcli.git
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
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --help

# Or with local installation
./bootstrap.sh --help
```

### 📋 Module Presets

Here are some common module combinations for different use cases:

```bash
# Frontend Developer
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "setup_manager,ssh_manager,docker_manager"

# DevOps Engineer
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,docker_manager,kubernetes_manager,gcp_manager,config_manager"

# Full Stack Developer
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,setup_manager,docker_manager,gcp_manager,misc_manager"

# Minimalist Setup
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,setup_manager"

# Power User (All Modules)
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,docker_manager,kubernetes_manager,gcp_manager,coolify_manager,setup_manager,misc_manager,config_manager"
```

### ✅ Post-Installation

After installation, follow these steps:

```bash
# 1. Restart your terminal or reload your shell
source ~/.zshrc

# 2. Initialize your personal configuration
max config init

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
git clone https://github.com/maximilianls98/maxcli.git
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

Run `max config init` to set up your personal configuration:

```bash
max config init
```

This creates `~/.config/maxcli/config.json` with your:

- Git username and email
- Dotfiles repository URL
- GCP project mappings
- Coolify instance details

### Module Configuration

Modules are configured in `~/.config/maxcli/modules_config.json`:

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
kubernetes_manager ❌ Disabled
gcp_manager        ✅ Enabled
coolify_manager    ❌ Disabled
setup_manager      ✅ Enabled
misc_manager       ❌ Disabled
config_manager     ✅ Enabled
```

### Enable/Disable Modules

```bash
# Enable a module
max modules enable kubernetes_manager

# Disable a module
max modules disable ssh_backup

# Enable multiple modules
max modules enable kubernetes_manager gcp_manager misc_manager
```

## 🗑️ Uninstalling MaxCLI

⚠️ **WARNING: Complete System Removal**

MaxCLI provides a built-in uninstall command that completely removes all traces of the CLI from your system. This operation is **IRREVERSIBLE** and will permanently delete all your configurations, settings, and customizations.

### What Gets Removed

The uninstall command removes:

🗂️ **Configuration Files:**

- `~/.config/maxcli/` (entire directory)
- All module configurations and settings
- SSH target profiles and connections
- Personal git settings and API keys
- Coolify instance configurations
- GCP project mappings

📁 **Installation Files:**

- `~/.local/lib/python/maxcli/` (MaxCLI library)
- `~/bin/max` (main executable)

🔧 **Shell Configuration:**

- PATH modification in `~/.zshrc` (if added by MaxCLI)
- PATH modification in `~/.bashrc` (if exists)
- PATH modification in `~/.bash_profile` (if exists)

💾 **Backup Files (if they exist):**

- SSH backup files created by ssh_backup module (`~/ssh_keys_backup.tar.gz*`)
- Temporary files in home directory

### Usage

```bash
# Standard uninstall with double confirmation
max uninstall

# Skip confirmations (NOT RECOMMENDED - dangerous)
max uninstall --force
```

### Confirmation Process

The uninstall command requires **double confirmation** to prevent accidental deletion:

1. **First confirmation**: Type `yes` when prompted
2. **Second confirmation**: Type `DELETE EVERYTHING` exactly as shown

Example interaction:

```bash
$ max uninstall

🗑️  MaxCLI Uninstaller
==================================================
🚨 WARNING: This will completely remove MaxCLI from your system!
📋 The following will be permanently deleted:
   • Configuration directory (~/.config/maxcli/)
   • MaxCLI library (~/.local/lib/python/maxcli/)
   • MaxCLI executable (~/bin/max)

💡 This includes:
   • All your personal configurations
   • SSH target profiles and connections
   • API keys and authentication settings
   • Module configurations and preferences

============================================================
⚡ Are you absolutely sure you want to uninstall MaxCLI? (type 'yes' to confirm): yes

🔥 FINAL WARNING: This action is IRREVERSIBLE!
📝 You will need to re-run the bootstrap script to reinstall MaxCLI.
🗑️  Type 'DELETE EVERYTHING' to proceed with uninstallation: DELETE EVERYTHING

🚀 Beginning MaxCLI uninstallation...
```

### Force Mode

**⚠️ DANGER: Use with extreme caution**

The `--force` flag skips all confirmations and immediately removes MaxCLI:

```bash
max uninstall --force
```

This is intended for automated scripts only. **Never use this flag interactively** unless you are absolutely certain you want to remove MaxCLI without any safety checks.

### After Uninstallation

After uninstalling MaxCLI:

1. **Restart your terminal** or run `source ~/.zshrc` to update your PATH
2. The `max` command will no longer be available
3. All your configurations and customizations are permanently lost

### Reinstalling After Uninstall

To reinstall MaxCLI after uninstalling:

```bash
# Reinstall with the bootstrap script
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash

# Or with your preferred modules
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules "ssh_manager,docker_manager"
```

You will need to reconfigure everything using `max init` and re-enable your preferred modules.

## 📚 Module Documentation

### SSH Manager (`ssh_manager`)

Complete SSH management including connections, key generation, backups, and file transfers.

```bash
# Manage SSH targets
max ssh targets add prod ubuntu 192.168.1.100 --port 2222 --key ~/.ssh/prod_key
max ssh targets list
max ssh targets remove old-server

# Connect to targets
max ssh connect prod
max ssh connect                    # Interactive selection

# Generate SSH keypairs
max ssh generate-keypair dev ~/.ssh/dev_key --type ed25519
max ssh copy-public-key prod       # Copy public key to target

# SSH key backup and restore with GPG encryption
max ssh backup export              # Create encrypted backup
max ssh backup import              # Restore from backup

# File transfers using rsync over SSH
max ssh rsync upload-backup hetzner    # Upload backup to target
max ssh rsync download-backup hetzner  # Download backup from target
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

### Misc Manager (`misc_manager`)

Database backup utilities, CSV data processing, and application deployment tools.

```bash
# Database backup operations
max backup-db                     # Backup PostgreSQL database to ~/backups

# Application deployment (placeholder)
max deploy-app                    # Custom deployment logic

# CSV data processing with Python functions
max process-csv --csv-file data.csv --function-file analysis.py
max process-csv --csv-file sales.csv --function-file stats.py --save-as sales_analysis
max process-csv --list-saved      # List saved processing functions
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

### Config Manager (`config_manager`)

Personal configuration management with backup and restore capabilities.

```bash
# Initialize or update personal configuration
max config init
max config init --force            # Force reconfiguration

# Backup configuration locally or to remote SSH target
max config backup                  # Create local backup
max config backup --target hetzner # Upload to SSH target

# Restore configuration from backup
max config restore --backup-file ~/backups/maxcli_backup.tar.gz
max config restore --target hetzner  # Download and restore from SSH target
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

Or manually edit `~/.config/maxcli/modules_config.json`:

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

#### Bootstrap Script Issues

##### Race Condition and Output Mixing (Fixed in Latest Version)

**Problem**: During fresh installation, the bootstrap script would sometimes:

- Output raw file content instead of executing code
- Mix Homebrew output with script output
- Fail to complete wrapper script creation
- Have Homebrew processes running in parallel causing conflicts

**Root Causes**:

1. **Homebrew Background Processes**: Homebrew's auto-update and cask installation processes would continue running while the bootstrap script proceeded
2. **Output Stream Mixing**: Multiple processes writing to stdout/stderr simultaneously caused corruption
3. **Heredoc Race Conditions**: Large heredoc blocks (like wrapper script creation) could be interrupted by background processes
4. **No Process Synchronization**: The script didn't wait for Homebrew installation to complete before proceeding

**Fixed in Latest Version**:

```bash
# The latest bootstrap script includes these fixes:

# 1. Homebrew Process Synchronization
- Explicit wait for Homebrew installation completion (up to 60s timeout)
- Background process suppression with output redirection
- Environment variables to prevent auto-updates during installation
- Process cleanup to kill lingering brew processes

# 2. Robust Wrapper Script Creation
- Uses temporary files instead of direct heredoc output
- Atomic file operations to prevent corruption
- Proper error handling and cleanup

# 3. Output Isolation
- Suppresses verbose Homebrew output that can interfere
- Explicit sleep delays to ensure process synchronization
- Background process cleanup before critical sections
```

**To Get the Fixed Version**:

```bash
# Always use the latest version from main branch
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash

# Or force download even if you have local files
./bootstrap.sh --force-download
```

**If You Experience Issues**:

```bash
# 1. Clear any partial installations
rm -rf ~/.venvs/maxcli ~/bin/max ~/.config/maxcli

# 2. Kill any lingering Homebrew processes
pkill -f brew || true

# 3. Use the fixed bootstrap script
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash

# 4. If problems persist, run with explicit homebrew suppression
export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_INSTALL_CLEANUP=1
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash
```

#### Installation Timeouts

```bash
# If installation times out waiting for Homebrew
export HOMEBREW_NO_AUTO_UPDATE=1
curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash --modules "ssh_manager"
```

#### Bootstrap Errors

## 🔧 Development

### Requirements

- Python 3.8+
- pip or pipenv for dependency management

### Development Setup

```bash
# Clone and install in development mode
git clone https://github.com/maximilianls98/maxcli.git
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
