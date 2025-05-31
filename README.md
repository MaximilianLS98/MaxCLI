# MaxCLI - Max's Personal Development CLI

A modular command-line utility for development operations, environment setup, and productivity tasks. Built with Python using functional programming principles and designed for extensibility.

## Features

- **Google Cloud Platform Management**: Switch between gcloud configurations with ADC support
- **Docker Operations**: Clean up Docker resources with both aggressive and gentle options
- **SSH Management**: Add, remove, list and connect to SSH targets with key-based authentication and saved profiles
- **SSH import/export**: Import and export SSH keys and target profiles
- **Coolify Management**: Get status of your coolify instance and start/stop resources
- **Kubernetes**: Quick context switching
- **Development Environment Setup**: Automated setup for new machines with different profiles
- **App Installation**: Pick and choose GUI applications to install, like Cursor, slack etc.
- **Interactive Prompts**: User-friendly menus and confirmations
- **Configuration Management**: Personal settings with JSON-based storage
- **Extensible Architecture**: Easy to add new commands and modules

## Quick Start

1. **Clone and install**:

    ```bash
    git clone <your-repo-url>
    cd maxcli
    chmod +x bootstrap.sh
    ./bootstrap.sh
    ```

    The bootstrap script automatically handles:

    - Installing system dependencies (Homebrew, Python, pipx, GPG)
    - Creating a python virtual environment
    - Installing Python dependencies
    - Setting up the MaxCLI package
    - Creating the `max` command in your PATH

2. **Restart your terminal** (or run `source ~/.zshrc`)

3. **Initialize your configuration**:

    ```bash
    max init
    ```

4. **Start using the CLI**:

    ```bash
    max --help
    ```

    ```

    ```

## Commands Overview

### Configuration & Setup

- `max init` - Initialize personal configuration
- `max setup minimal` - Basic development environment setup
- `max setup dev-full` - Complete development environment
- `max setup apps` - Install GUI applications

### Google Cloud Platform

- `max create-config <name>` - Create new gcloud config with full auth setup
- `max switch-config [name]` - Switch gcloud config and ADC (interactive if no name)
- `max list-configs` - Show all available configurations

### SSH Management

- `max ssh list-targets` - List all saved SSH connection profiles
- `max ssh add-target <name> <user> <host>` - Add new SSH target profile
- `max ssh connect [name]` - Connect to SSH target (interactive if no name)
- `max ssh generate-keypair <name> <path>` - Generate new SSH keypair
- `max ssh copy-public-key <name>` - Copy public key to target server
- `max ssh remove-target <name>` - Remove SSH target profile
- `max ssh export-keys` - Export SSH keys and profiles to encrypted backup
- `max ssh import-keys` - Import SSH keys and profiles from encrypted backup

### Docker & Kubernetes

- `max docker-clean` - Aggressive Docker cleanup (removes everything unused)
- `max docker-tidy` - Gentle Docker cleanup (preserves recent items)
- `max kctx <context>` - Switch Kubernetes context WIP (not working)

### Database & Deployment

- `max backup-db` - Backup PostgreSQL database WIP (not working)
- `max deploy-app` - Deploy application WIP (not working)

## Detailed Usage

### Environment Setup

The setup commands are designed for bootstrapping new development machines:

**Minimal Setup** - Essential tools only:

```bash
max setup minimal
```

Installs: Homebrew, git, zsh, Oh My Zsh, and basic CLI tools.

**Full Development Setup** - Complete environment:

```bash
max setup dev-full
```

Includes everything from minimal plus: Node.js, Python, Docker, kubectl, AWS CLI, gcloud, Terraform, and your dotfiles.

**GUI Applications**:

```bash
max setup apps                 # Install all apps
max setup apps --interactive   # Choose specific apps
```

Installs: VS Code, Cursor, Docker Desktop, Chrome, Slack, Postman, etc.

### GCP Configuration Management

Create a new gcloud configuration with complete setup:

```bash
max create-config myproject
```

This will:

1. Create the gcloud configuration
2. Authenticate with your Google account
3. Set up Application Default Credentials
4. Configure quota project
5. Save ADC file for future switching

Switch between configurations:

```bash
max switch-config altekai       # Switch to specific config
max switch-config               # Interactive menu
```

### Docker Management

For regular cleanup:

```bash
max docker-tidy
```

Removes containers stopped >24h, dangling images, unused networks, and old build cache.

For aggressive cleanup:

```bash
max docker-clean
```

⚠️ Removes ALL unused Docker resources.

### SSH Management

The SSH manager provides secure storage and management of SSH connection profiles with key-based authentication.

**Add SSH targets for quick connections**:

```bash
# Basic target with default port and key
max ssh add-target prod ubuntu 192.168.1.100

# Custom port and key file
max ssh add-target staging deploy server.example.com -p 2222 -k ~/.ssh/staging_key

# Add target with all options
max ssh add-target dev root 10.0.0.5 --port 22 --key ~/.ssh/dev_rsa
```

**Connect to targets**:

```bash
max ssh connect prod           # Connect to 'prod' target directly
max ssh connect               # Show interactive menu to choose target
```

**Generate and deploy SSH keys**:

```bash
# Generate a new ED25519 keypair (recommended)
max ssh generate-keypair prod ~/.ssh/prod_key --type ed25519

# Generate RSA keypair
max ssh generate-keypair backup ~/.ssh/backup_rsa --type rsa

# Copy public key to server (enables passwordless login)
max ssh copy-public-key prod
```

**Manage targets**:

```bash
max ssh list-targets           # Show all saved targets in table format
max ssh remove-target old-server  # Remove a target
```

**Complete workflow example**:

```bash
# 1. Generate keypair
max ssh generate-keypair prod ~/.ssh/prod_key

# 2. Add target with the new key
max ssh add-target prod ubuntu 192.168.1.100 -k ~/.ssh/prod_key

# 3. Copy public key to server (enter password when prompted)
max ssh copy-public-key prod

# 4. Connect without password
max ssh connect prod
```

**Security features**:

- SSH targets stored in `~/.config/maxcli/ssh_targets.json` with 600 permissions
- Private keys validated before adding targets
- Keys generated with secure permissions (600 for private, 644 for public)
- Interactive target selection with fallback modes

### SSH Key Backup & Restore

MaxCLI provides secure backup and restore capabilities for your SSH keys and target configurations using GPG encryption.

**Export SSH keys to encrypted backup**:

```bash
# Interactive selection and backup
max ssh export-keys
```

The export process:

1. **Interactive Selection**: Choose which SSH private keys to backup from `~/.ssh/`
2. **Automatic Inclusion**: Corresponding public keys (.pub) are included automatically
3. **Configuration Backup**: SSH target profiles from MaxCLI are included
4. **Secure Encryption**: GPG symmetric encryption with AES256 cipher
5. **Safe Cleanup**: Unencrypted temporary files are automatically removed

**Import SSH keys from encrypted backup**:

```bash
# Interactive backup file selection and restore
max ssh import-keys
```

The import process:

1. **File Selection**: Choose backup file from home directory or enter custom path
2. **Secure Decryption**: GPG decryption with interactive password prompt
3. **Validation**: Backup contents are validated before extraction
4. **Proper Permissions**: Private keys get 600, public keys get 644 permissions
5. **Directory Creation**: Creates `~/.ssh/` and `~/.config/maxcli/` if needed

**Complete backup workflow example**:

```bash
# 1. Export current SSH setup
max ssh export-keys
# Select keys: id_rsa, id_ed25519, work_key
# GPG prompts for encryption password
# ✅ Backup saved to ~/ssh_keys_backup.tar.gz.gpg

# 2. On new machine, import the backup
max ssh import-keys
# Select backup file: ssh_keys_backup.tar.gz.gpg
# GPG prompts for decryption password
# Confirm extraction: y
# ✅ SSH keys restored to ~/.ssh/
```

**Security features**:

- **AES256 Encryption**: Strong symmetric encryption via GPG
- **Secure Password Handling**: GPG handles all password prompting directly
- **Secure Permissions**: Automatic 600/644 permission setting
- **Clean Temporary Files**: No unencrypted data left on disk
- **Fail-Safe Cleanup**: Unencrypted tarballs are always deleted, even if encryption fails
- **Backup Validation**: Contents verified before extraction

**Backup contents**:

- Selected SSH private keys from `~/.ssh/`
- Corresponding public keys (.pub files) if they exist
- SSH target profiles from `~/.config/maxcli/ssh_targets.json`
- Compressed and encrypted in a single portable file

### SSH Backup Upload and Download

MaxCLI provides secure remote backup capabilities for your encrypted SSH key backups using rsync over SSH.

**Upload Backup**

Upload your encrypted SSH backup to a remote server:

```bash
max ssh rsync-upload-backup <target-name>
```

This will securely upload your backup to the selected SSH target.

**Download Backup**

Download your encrypted SSH backup from a remote server:

```bash
max ssh rsync-download-backup <target-name>
```

This will securely download the backup from your server back to your machine.

⚠️ **Note**: Only encrypted backups (.tar.gz.gpg) are transferred to ensure security.

**Complete remote backup workflow example**:

```bash
# 1. Create and export SSH keys backup
max ssh export-keys
# ✅ Backup saved to ~/ssh_keys_backup.tar.gz.gpg

# 2. Upload backup to your server
max ssh rsync-upload-backup hetzner
# 🔄 Uploading SSH backup to 'hetzner'...
# ✅ Successfully uploaded SSH backup to 'hetzner'
# 📍 Remote location: ~/backups/ssh_keys_backup.tar.gz.gpg

# 3. Later, on a new machine, download and restore
max ssh rsync-download-backup hetzner
# 🔄 Downloading SSH backup from 'hetzner'...
# ✅ Successfully downloaded SSH backup from 'hetzner'
# 💡 Import keys using: max ssh import-keys

# 4. Import the downloaded backup
max ssh import-keys
# ✅ SSH keys restored to ~/.ssh/
```

**Requirements for remote backup**:

- SSH target must exist in your configuration (`max ssh add-target`)
- SSH key-based authentication to the target server
- `rsync` installed on your local system
- Backup file created locally (`max ssh export-keys`) for upload
- Backup file exists on remote server for download

**Security features**:

- **SSH Authentication**: Uses your configured SSH keys for secure transport
- **Encrypted-Only Transfer**: Only transfers GPG-encrypted backup files
- **Progress Feedback**: Real-time transfer progress during upload/download
- **Remote Directory Creation**: Automatically creates `~/backups/` on the server
- **Safe Overwrite**: Local files are safely overwritten during download

## Configuration

Configuration is stored in `~/.config/maxcli/config.json` and includes:

```json
{
	"git": {
		"name": "Your Name",
		"email": "your.email@example.com"
	},
	"coolify_api_key": "your_coolify_api_key",
	"coolify_instance_url": "https://coolify.example.com",
	"dotfiles_repo": "https://github.com/yourusername/dotfiles.git",
	"gcp_quota_projects": {
		"altekai": "altekai-project-id",
		"company": "company-project-id"
	}
}
```

## Project Structure

```
maxcli/
├── main.py                 # Entry point
├── maxcli/
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # Main CLI module with argument parsing
│   ├── config.py           # Configuration management
│   ├── interactive.py      # Interactive utilities
│   ├── system.py           # System utilities
│   ├── ssh_manager.py      # SSH connection profile management
│   └── commands/           # Command modules
│       ├── __init__.py
│       ├── gcp.py          # Google Cloud Platform commands
│       ├── docker.py       # Docker cleanup commands
│       ├── kubernetes.py   # Kubernetes context switching
│       ├── setup.py        # Development environment setup
│       └── misc.py         # Miscellaneous commands
├── requirements.txt        # Dependencies (optional enhancements)
└── README.md              # This file
```

## Extending the CLI

### Adding New Commands

1. Create a new function in the appropriate module or create a new module in `maxcli/commands/`
2. Import the function in `maxcli/cli.py`
3. Add argument parser configuration in the `main()` function

Example:

```python
# In maxcli/commands/mymodule.py
def my_command(args):
    """My custom command implementation."""
    print(f"Running command with arg: {args.my_arg}")

# In maxcli/cli.py
from .commands.mymodule import my_command

# Add to main() function:
my_parser = subparsers.add_parser('my-command', help='My custom command')
my_parser.add_argument('my_arg', help='Required argument')
my_parser.set_defaults(func=my_command)
```

### Design Principles

- **Functional Programming**: Functions are pure when possible, with clear inputs and outputs
- **Modularity**: Each command module is independent and focused
- **User Experience**: Clear help text, interactive prompts, and confirmation for destructive operations
- **Error Handling**: Graceful error handling with informative messages
- **Configuration**: Personal settings stored in standard locations

## Dependencies

The CLI uses only Python standard library by default. Optional enhancements:

- `questionary` - Better interactive prompts and menus
- `argcomplete` - Shell autocompletion support

Install optional dependencies:

```bash
pip install questionary argcomplete
```

## Platform Support

Designed for macOS but most commands work on Linux. The setup commands use Homebrew (macOS) for package management.

## License

Personal utility - adapt as needed for your own use.

## Contributing

This is a personal CLI tool, but the modular structure makes it easy to adapt for your own needs. Feel free to fork and customize!

## Troubleshooting

**Command not found**: Ensure the script is executable and linked to your PATH:

```bash
chmod +x main.py
ln -sf $(pwd)/main.py /usr/local/bin/max
```

**Permission denied**: The script may need executable permissions:

```bash
chmod +x main.py
```

**Missing dependencies**: Some features require external tools:

- GCP commands: `gcloud` CLI
- Docker commands: `docker` CLI
- Kubernetes commands: `kubectl` CLI
- Setup commands: `brew` (macOS) or equivalent package manager
- SSH commands: `ssh`, `ssh-keygen`, `ssh-copy-id` (OpenSSH client tools)
