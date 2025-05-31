# MaxCLI - Personal Development CLI Tool

A universal CLI tool for development and operations tasks, featuring automatic personal configuration and setup utilities.

## 🚀 Quick Start

### Installation

1. **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd maxcli
    ```

2. **Run the bootstrap script:**

    ```bash
    chmod +x bootstrap.sh
    ./bootstrap.sh
    ```

3. **Initialize your personal configuration:**
    ```bash
    max init
    ```

The initialization will prompt you for:

- Git username and email
- Dotfiles repository URL (optional)
- Google Cloud Platform project mappings (optional)

### Basic Usage

```bash
# Show all available commands
max --help

# Switch gcloud configurations with interactive selection
max switch-config

# Create a new gcloud configuration
max create-config myproject

# Set up development environment
max setup dev-full

# Clean up Docker
max docker-tidy
```

## 📋 Available Commands

### Configuration Management

- `max init` - Initialize or update personal configuration
- `max init --force` - Force reconfiguration

### Google Cloud Platform

- `max create-config <name>` - Create new gcloud config with authentication
- `max switch-config [name]` - Switch gcloud config (interactive if no name provided)
- `max list-configs` - List available configurations

### Docker Management

- `max docker-clean` - Aggressive Docker cleanup (removes everything unused)
- `max docker-tidy` - Gentle Docker cleanup (preserves recent items)

### Kubernetes

- `max kctx <context>` - Switch Kubernetes context

### Development Environment Setup

- `max setup minimal` - Basic terminal and git setup
- `max setup dev-full` - Complete development environment
- `max setup apps` - Install GUI applications
- `max setup apps --interactive` - Choose specific apps to install

### Other

- `max backup-db` - Backup database (placeholder)
- `max deploy-app` - Deploy application (placeholder)

## ⚙️ Configuration System

MaxCLI uses a personal configuration file stored at `~/.config/maxcli/config.json`. This eliminates the need to modify code for personal use.

### Configuration Structure

```json
{
	"git_name": "Your Name",
	"git_email": "your.email@example.com",
	"dotfiles_repo": "git@github.com:yourusername/dotfiles.git",
	"quota_project_mappings": {
		"project-dev": "my-gcp-project-dev",
		"project-prod": "my-gcp-project-prod"
	}
}
```

### Updating Configuration

```bash
# Update existing configuration
max init

# Force complete reconfiguration
max init --force
```

## 🛠️ Setup Profiles

### Minimal Setup

Basic development tools and terminal configuration:

- Homebrew package manager
- Essential CLI tools: git, zsh, wget, htop
- Oh My Zsh terminal enhancement
- Git configuration using your personal details

### Dev Full Setup

Complete development environment including:

- Everything from minimal setup
- Programming languages: Node.js, Python
- Container tools: Docker, kubectl
- Cloud tools: AWS CLI, Google Cloud SDK, Terraform
- Development tools: tmux
- Dotfiles cloning and setup

### Apps Setup

GUI applications for productivity and development:

- **Development:** Visual Studio Code, Cursor, Docker Desktop
- **Communication:** Slack
- **Browsers:** Google Chrome, Arc Browser
- **Tools:** Postman, Ghostty terminal

Use `--interactive` flag for custom app selection.

## 🔐 Google Cloud Platform Integration

### Creating GCP Configurations

```bash
# Create a new configuration with guided setup
max create-config myproject
```

This will:

1. Create a new gcloud configuration
2. Authenticate with your Google account
3. Set up Application Default Credentials (ADC)
4. Configure quota project
5. Save ADC for future switching

### Switching Between Configurations

```bash
# Interactive selection
max switch-config

# Direct switch
max switch-config myproject
```

### Project Mappings

Configure quota project mappings during `max init`:

- Maps configuration names to GCP project IDs
- Automatically applies quota projects when switching
- Can be updated anytime

## 🧹 Docker Management

### Gentle Cleanup (`docker-tidy`)

Safe cleanup that preserves:

- All tagged images
- Recently stopped containers (<24h)
- All volumes
- Recent build cache

### Aggressive Cleanup (`docker-clean`)

Removes all unused Docker resources:

- All stopped containers
- All unused images
- All unused volumes
- All build cache

## 📁 File Structure

```
maxcli/
├── max                 # Main CLI script
├── bootstrap.sh        # Installation script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔧 Requirements

- macOS (tested on macOS Sonoma)
- Python 3.8+
- Homebrew (installed by bootstrap script)

### Optional Dependencies

- `questionary` - Enhanced interactive prompts
- `argcomplete` - Tab completion

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `max init` to ensure configuration works
5. Submit a pull request

## 💡 Tips

- Run `max init` after major updates to refresh configuration
- Use `max setup apps --interactive` to selectively install applications
- The tool is idempotent - you can run setup commands multiple times safely
- Configuration is stored locally and never shared

## 📝 License

MIT License - feel free to adapt for your own use!

## 🆘 Troubleshooting

### Configuration Issues

```bash
# Reset configuration
max init --force

# Check configuration location
ls -la ~/.config/maxcli/
```

### PATH Issues

```bash
# Ensure ~/bin is in PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Permission Issues

```bash
# Make script executable
chmod +x ~/bin/max
```

For more help, run any command with `--help` flag for detailed information.
