# MaxCLI - Max's Personal Development CLI

A modular command-line utility for development operations, environment setup, and productivity tasks. Built with Python using functional programming principles and designed for extensibility.

## Features

- **Google Cloud Platform Management**: Switch between gcloud configurations with ADC support
- **Docker Operations**: Clean up Docker resources with both aggressive and gentle options
- **Kubernetes**: Quick context switching
- **Development Environment Setup**: Automated setup for new machines with different profiles
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
    - Installing system dependencies (Homebrew, Python, pipx)
    - Creating a virtual environment
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

### Docker & Kubernetes

- `max docker-clean` - Aggressive Docker cleanup (removes everything unused)
- `max docker-tidy` - Gentle Docker cleanup (preserves recent items)
- `max kctx <context>` - Switch Kubernetes context

### Database & Deployment

- `max backup-db` - Backup PostgreSQL database
- `max deploy-app` - Deploy application (placeholder for your logic)

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

## Configuration

Configuration is stored in `~/.config/maxcli/config.json` and includes:

```json
{
	"git": {
		"name": "Your Name",
		"email": "your.email@example.com"
	},
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
