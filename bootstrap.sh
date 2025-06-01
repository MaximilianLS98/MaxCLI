#!/bin/bash

# ASCII Art Header
cat << "EOF"
███╗   ███╗ █████╗ ██╗  ██╗ ██████╗██╗     ██╗
████╗ ████║██╔══██╗╚██╗██╔╝██╔════╝██║     ██║
██╔████╔██║███████║ ╚███╔╝ ██║     ██║     ██║
██║╚██╔╝██║██╔══██║ ██╔██╗ ██║     ██║     ██║
██║ ╚═╝ ██║██║  ██║██╔╝ ██╗╚██████╗███████╗██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝
                                                
    🚀 Personal Development CLI Bootstrap       
EOF

echo ""
echo "🔧 Setting up your personalized development toolkit..."
echo "=================================================="

# Parse command line arguments
PRESET_MODULES=""
for arg in "$@"; do
    case $arg in
        --modules=*)
            PRESET_MODULES="${arg#*=}"
            shift
            ;;
        --modules)
            PRESET_MODULES="$2"
            shift 2
            ;;
    esac
done

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Script directory: $SCRIPT_DIR"

# Check if required files exist
if [[ ! -f "$SCRIPT_DIR/requirements.txt" ]]; then
    echo "❌ Error: requirements.txt not found in $SCRIPT_DIR"
    echo "💡 Make sure you're running this script from the MaxCLI directory"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/main.py" ]]; then
    echo "❌ Error: main.py not found in $SCRIPT_DIR"
    echo "💡 Make sure you're running this script from the MaxCLI directory"
    exit 1
fi

if [[ ! -d "$SCRIPT_DIR/maxcli" ]]; then
    echo "❌ Error: maxcli package directory not found in $SCRIPT_DIR"
    echo "💡 Make sure you're running this script from the MaxCLI directory"
    exit 1
fi

# Install Xcode command line tools
echo ""
echo "📱 Installing Xcode command line tools..."
xcode-select --install 2>/dev/null || echo "✅ Xcode tools already installed"

# Install Homebrew
echo ""
echo "🍺 Installing Homebrew..."
if ! command -v brew &> /dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew already installed"
fi

# Install Python and pipx
echo ""
echo "🐍 Installing Python, pipx, and GPG..."
brew install python pipx gnupg gnupg2

# Ensure pipx is in PATH
pipx ensurepath

# Create virtual environment for maxcli
echo ""
echo "📦 Setting up MaxCLI virtual environment..."
python3 -m venv ~/.venvs/maxcli
source ~/.venvs/maxcli/bin/activate

# Install dependencies (using absolute path)
echo ""
echo "📚 Installing dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Install the CLI tool (copy the entire package structure)
echo ""
echo "🔧 Installing MaxCLI package..."
mkdir -p ~/bin

# Copy the main entry point and make it executable
cp "$SCRIPT_DIR/main.py" ~/bin/max
chmod +x ~/bin/max

# Copy the entire maxcli package to the user's site-packages or a local directory
# We'll put it in ~/.local/lib/python/maxcli for easy access
mkdir -p ~/.local/lib/python
cp -r "$SCRIPT_DIR/maxcli" ~/.local/lib/python/

# Create a wrapper script that always uses the maxcli virtual environment
cat > ~/bin/max << 'EOF'
#!/bin/bash
# MaxCLI wrapper script that ensures the correct Python environment is used.
# This script always uses the maxcli virtual environment created during bootstrap.

# Path to the maxcli virtual environment
MAXCLI_VENV="$HOME/.venvs/maxcli"
MAXCLI_PYTHON="$MAXCLI_VENV/bin/python"

# Check if the maxcli virtual environment exists
if [[ ! -f "$MAXCLI_PYTHON" ]]; then
    echo "❌ Error: MaxCLI virtual environment not found at $MAXCLI_VENV"
    echo "💡 Please run the bootstrap script to set up the environment:"
    echo "   ./bootstrap.sh"
    exit 1
fi

# Check if questionary is installed in the virtual environment
if ! "$MAXCLI_PYTHON" -c "import questionary" 2>/dev/null; then
    echo "⚠️  Warning: questionary not found in maxcli environment"
    echo "💡 Please run the bootstrap script again to reinstall dependencies:"
    echo "   ./bootstrap.sh"
fi

# Set up the Python path for maxcli package
export PYTHONPATH="$HOME/.local/lib/python:$PYTHONPATH"

# Execute the main CLI with the maxcli virtual environment Python
exec "$MAXCLI_PYTHON" -c "
import sys
import os

# Ensure maxcli package can be found
maxcli_path = os.path.expanduser('~/.local/lib/python')
if maxcli_path not in sys.path:
    sys.path.insert(0, maxcli_path)

# Import and run the CLI
from maxcli.cli import main
main()
" "$@"
EOF

chmod +x ~/bin/max

# Add to PATH if not already there
if ! grep -q 'export PATH="$HOME/bin:$PATH"' ~/.zshrc; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
    echo "✅ Added ~/bin to PATH in ~/.zshrc"
fi

# Create the configuration directory
echo ""
echo "📁 Setting up configuration directory..."
mkdir -p ~/.config/maxcli

# Module selection logic
enabled_modules=()

if [[ -n "$PRESET_MODULES" ]]; then
    echo ""
    echo "🎯 Using preset modules: $PRESET_MODULES"
    IFS=',' read -ra modules_array <<< "$PRESET_MODULES"
    for module in "${modules_array[@]}"; do
        # Trim whitespace
        module=$(echo "$module" | xargs)
        enabled_modules+=("$module")
    done
else
    # Interactive module selection
    echo ""
    cat << "EOF"
🎯 Module Selection
==================
MaxCLI uses a modular architecture. You can enable the modules you need
and keep the CLI clean and focused. You can always change this later
using 'max modules enable/disable <module>' commands.

Available modules:

📱 ssh_manager      - SSH connection management and key handling
🔐 ssh_backup       - SSH key backup and restore with GPG encryption
📁 ssh_rsync        - SSH-based rsync operations and remote backup
🐳 docker_manager   - Docker system cleanup and management
☸️  kubernetes_manager - Kubernetes context switching
☁️  gcp_manager      - Google Cloud Platform configuration management  
🚀 coolify_manager  - Coolify instance management via API
⚙️  setup_manager    - Development environment setup profiles
🔧 misc_manager     - Database backup and deployment utilities

EOF

    # Function to ask yes/no questions
    ask_yes_no() {
        local prompt="$1"
        local default="$2"
        
        if [[ "$default" == "y" ]]; then
            prompt="$prompt [Y/n]"
        else
            prompt="$prompt [y/N]"
        fi
        
        echo -n "$prompt: "
        read -r answer
        
        # Use default if empty
        if [[ -z "$answer" ]]; then
            answer="$default"
        fi
        
        case "$answer" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            *) return 1 ;;
        esac
    }

    echo "Select which modules to enable (press Enter for default recommendation):"
    echo ""

    # Core modules (recommended by default)
    if ask_yes_no "📱 Enable ssh_manager (SSH connection and key management)" "y"; then
        enabled_modules+=("ssh_manager")
    fi

    if ask_yes_no "⚙️  Enable setup_manager (development environment setup)" "y"; then
        enabled_modules+=("setup_manager")
    fi

    # SSH-related modules (ask if ssh_manager is enabled)
    if [[ " ${enabled_modules[*]} " =~ " ssh_manager " ]]; then
        if ask_yes_no "🔐 Enable ssh_backup (SSH key backup/restore with GPG)" "n"; then
            enabled_modules+=("ssh_backup")
        fi

        if ask_yes_no "📁 Enable ssh_rsync (SSH-based rsync operations)" "n"; then
            enabled_modules+=("ssh_rsync")
        fi
    fi

    # Optional modules (disabled by default but commonly useful)
    if ask_yes_no "🐳 Enable docker_manager (Docker cleanup utilities)" "n"; then
        enabled_modules+=("docker_manager")
    fi

    if ask_yes_no "☸️  Enable kubernetes_manager (Kubernetes context switching)" "n"; then
        enabled_modules+=("kubernetes_manager")
    fi

    if ask_yes_no "☁️  Enable gcp_manager (Google Cloud Platform tools)" "n"; then
        enabled_modules+=("gcp_manager")
    fi

    if ask_yes_no "🚀 Enable coolify_manager (Coolify instance management)" "n"; then
        enabled_modules+=("coolify_manager")
    fi

    if ask_yes_no "🔧 Enable misc_manager (database backup and deployment)" "n"; then
        enabled_modules+=("misc_manager")
    fi
fi

# Create the modules configuration file using the new format
echo ""
echo "💾 Creating module configuration..."

# Create modules JSON array for enabled_modules
enabled_modules_json="["
for i in "${!enabled_modules[@]}"; do
    if [[ $i -gt 0 ]]; then
        enabled_modules_json+=", "
    fi
    enabled_modules_json+="\"${enabled_modules[$i]}\""
done
enabled_modules_json+="]"

# Create the complete module configuration with the new format
cat > ~/.config/maxcli/max_modules.json << EOF
{
  "bootstrap_version": "1.0.0",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "enabled_modules": $enabled_modules_json,
  "module_info": {
    "ssh_manager": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " ssh_manager " ]]; then echo "true"; else echo "false"; fi),
      "description": "SSH connection and target management",
      "commands": ["ssh"],
      "dependencies": []
    },
    "ssh_backup": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " ssh_backup " ]]; then echo "true"; else echo "false"; fi),
      "description": "SSH key backup and restore with GPG encryption",
      "commands": ["ssh-backup", "ssh-restore"],
      "dependencies": ["gpg"]
    },
    "ssh_rsync": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " ssh_rsync " ]]; then echo "true"; else echo "false"; fi),
      "description": "SSH-based rsync operations and remote backup",
      "commands": ["ssh-rsync-push", "ssh-rsync-pull"],
      "dependencies": ["rsync"]
    },
    "docker_manager": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " docker_manager " ]]; then echo "true"; else echo "false"; fi),
      "description": "Docker system management and cleanup",
      "commands": ["docker"],
      "dependencies": ["docker"]
    },
    "kubernetes_manager": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " kubernetes_manager " ]]; then echo "true"; else echo "false"; fi),
      "description": "Kubernetes context switching and cluster management",
      "commands": ["kctx"],
      "dependencies": ["kubectl"]
    },
    "gcp_manager": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " gcp_manager " ]]; then echo "true"; else echo "false"; fi),
      "description": "Google Cloud Platform configuration and authentication management",
      "commands": ["switch-config", "create-config", "list-configs"],
      "dependencies": ["gcloud"]
    },
    "coolify_manager": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " coolify_manager " ]]; then echo "true"; else echo "false"; fi),
      "description": "Coolify instance management through REST API",
      "commands": ["coolify"],
      "dependencies": []
    },
    "setup_manager": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " setup_manager " ]]; then echo "true"; else echo "false"; fi),
      "description": "Development environment setup and configuration profiles",
      "commands": ["setup"],
      "dependencies": []
    },
    "misc_manager": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " misc_manager " ]]; then echo "true"; else echo "false"; fi),
      "description": "Database backup utilities and application deployment tools",
      "commands": ["backup-db", "deploy-app"],
      "dependencies": ["pg_dump"]
    }
  }
}
EOF

echo "✅ Module configuration created with ${#enabled_modules[@]} modules enabled"

# Show summary of enabled modules
if [[ ${#enabled_modules[@]} -gt 0 ]]; then
    echo ""
    echo "🎯 Enabled modules:"
    for module in "${enabled_modules[@]}"; do
        echo "   ✓ $module"
    done
else
    echo ""
    echo "⚠️  No modules enabled - you can enable them later with 'max modules enable <module>'"
fi

# Source the updated profile
source ~/.zshrc 2>/dev/null || true

# Success ASCII Art
echo ""
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║  🎉 INSTALLATION COMPLETE! 🎉                           ║
║                                                          ║
║  MaxCLI is now ready to rock your development workflow!  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF

echo ""
echo "🎯 Next steps:"
echo "   1. Restart your terminal or run: source ~/.zshrc"
echo "   2. Initialize personal config: max init"
echo "   3. Explore available commands: max --help"
echo "   4. See your enabled modules: max modules list"
echo ""
echo "💡 Module Management:"
echo "   • View modules: max modules list"
echo "   • Enable more: max modules enable <module>"
echo "   • Disable modules: max modules disable <module>"
echo ""

# Show enabled command examples
if [[ ${#enabled_modules[@]} -gt 0 ]]; then
    echo "🚀 Try these commands based on your enabled modules:"
    for module in "${enabled_modules[@]}"; do
        case "$module" in
            "ssh_manager")
                echo "   max ssh list-targets            # Manage SSH connections"
                ;;
            "ssh_backup")
                echo "   max ssh-backup                  # Backup SSH keys with GPG"
                ;;
            "ssh_rsync")
                echo "   max ssh-rsync-push <target>     # Upload files via rsync"
                ;;
            "setup_manager")
                echo "   max setup minimal               # Basic dev environment setup"
                ;;
            "docker_manager")
                echo "   max docker clean --extensive    # Clean up Docker system"
                ;;
            "kubernetes_manager")
                echo "   max kctx <context>              # Switch Kubernetes context"
                ;;
            "gcp_manager")
                echo "   max list-configs                # Show GCP configurations"
                ;;
            "coolify_manager")
                echo "   max coolify status              # Check Coolify status"
                ;;
            "misc_manager")
                echo "   max backup-db                   # Backup database"
                ;;
        esac
    done
fi

echo ""

# Footer art
cat << "EOF"
    ┌─────────────────────────────────────────┐
    │  Ready to supercharge your workflow! 🚀 │
    └─────────────────────────────────────────┘
EOF