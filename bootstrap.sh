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

# Function to show usage information (defined early)
show_help() {
    cat << "EOF"
🚀 MaxCLI Bootstrap Script - Personal Development CLI Setup

USAGE:
    ./bootstrap.sh [OPTIONS]

INSTALLATION MODES:
    Standalone (download files automatically):
        curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash

    Local (use files in current directory):
        git clone https://github.com/maximilianls98/maxcli.git
        cd maxcli
        ./bootstrap.sh

OPTIONS:
    --modules=MODULE1,MODULE2    Preset modules to enable (comma-separated)
    --modules MODULE1,MODULE2    Alternative syntax for modules
    --force-download            Force download files even if local files exist
    --github-repo=USER/REPO     Use a different GitHub repository
    --github-branch=BRANCH      Use a different branch (default: main)
    --help, -h                  Show this help message

AVAILABLE MODULES:
    ssh_manager       SSH connection and key management
    ssh_backup        SSH key backup/restore with GPG encryption  
    ssh_rsync         SSH-based rsync operations
    docker_manager    Docker system cleanup and management
    kubernetes_manager Kubernetes context switching
    gcp_manager       Google Cloud Platform configuration
    coolify_manager   Coolify instance management
    setup_manager     Development environment setup
    misc_manager      Database backup and deployment utilities

EXAMPLES:
    # Install with specific modules
    ./bootstrap.sh --modules=ssh_manager,docker_manager,setup_manager
    
    # Force fresh download
    ./bootstrap.sh --force-download
    
    # Use a fork
    ./bootstrap.sh --github-repo=yourfork/maxcli
    
    # Standalone with modules
    curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash -s -- --modules=ssh_manager,setup_manager

EOF
}

# CRITICAL FIX: Parse command line arguments FIRST, before any file operations or traps
# This ensures --help exits immediately without triggering any cleanup or file operations
PRESET_MODULES=""
FORCE_DOWNLOAD=false
GITHUB_REPO="maximilianls98/maxcli"
GITHUB_BRANCH="main"

for arg in "$@"; do
    case $arg in
        --help|-h)
            show_help
            exit 0
            ;;
        --modules=*)
            PRESET_MODULES="${arg#*=}"
            shift
            ;;
        --modules)
            PRESET_MODULES="$2"
            shift 2
            ;;
        --force-download)
            FORCE_DOWNLOAD=true
            shift
            ;;
        --github-repo=*)
            GITHUB_REPO="${arg#*=}"
            shift
            ;;
        --github-branch=*)
            GITHUB_BRANCH="${arg#*=}"
            shift
            ;;
        *)
            if [[ "$arg" != "" ]]; then
                echo "⚠️  Unknown option: $arg"
                echo "💡 Use --help to see available options"
                exit 1
            fi
            ;;
    esac
done

# NOW it's safe to set up file operations and traps
# Configuration for standalone mode
TEMP_DIR=""
CLEANUP_REQUIRED=false

# Function to detect if we're running in standalone mode
is_standalone_mode() {
    local script_dir="$1"
    [[ ! -f "$script_dir/requirements.txt" ]] || [[ ! -f "$script_dir/main.py" ]] || [[ ! -d "$script_dir/maxcli" ]]
}

# Function to download files from GitHub
download_required_files() {
    echo "📥 Downloading required files from GitHub..."
    TEMP_DIR=$(mktemp -d)
    CLEANUP_REQUIRED=true
    
    echo "📁 Created temporary directory: $TEMP_DIR"
    
    # Download individual files with error checking
    echo "⬇️  Downloading requirements.txt..."
    if ! curl -fsSL "https://raw.githubusercontent.com/$GITHUB_REPO/$GITHUB_BRANCH/requirements.txt" -o "$TEMP_DIR/requirements.txt"; then
        echo "❌ Error: Failed to download requirements.txt"
        exit 1
    fi
    
    echo "⬇️  Downloading main.py..."
    if ! curl -fsSL "https://raw.githubusercontent.com/$GITHUB_REPO/$GITHUB_BRANCH/main.py" -o "$TEMP_DIR/main.py"; then
        echo "❌ Error: Failed to download main.py"
        exit 1
    fi
    
    # Download and extract the entire repository to get the maxcli package
    echo "📦 Downloading and extracting maxcli package..."
    if ! curl -fsSL "https://github.com/$GITHUB_REPO/archive/$GITHUB_BRANCH.tar.gz" | tar -xz -C "$TEMP_DIR" --strip-components=1; then
        echo "❌ Error: Failed to download and extract repository"
        exit 1
    fi
    
    # Verify the maxcli directory was extracted
    if [[ ! -d "$TEMP_DIR/maxcli" ]]; then
        echo "❌ Error: maxcli package directory not found in downloaded files"
        exit 1
    fi
    
    echo "✅ Successfully downloaded all required files"
}

# Function to cleanup temporary files
cleanup() {
    if [[ "$CLEANUP_REQUIRED" == "true" ]] && [[ -n "$TEMP_DIR" ]] && [[ -d "$TEMP_DIR" ]]; then
        echo "🧹 Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Set trap for cleanup on script exit (ONLY after argument parsing)
trap cleanup EXIT

echo "🔍 Proceeding with installation (arguments parsed safely)..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Script directory: $SCRIPT_DIR"

# Check if we need to download files (standalone mode or force download)
if [[ "$FORCE_DOWNLOAD" == "true" ]] || is_standalone_mode "$SCRIPT_DIR"; then
    if [[ "$FORCE_DOWNLOAD" == "true" ]]; then
        echo "🔄 Force download requested - downloading fresh files..."
    else
        echo "🔍 Running in standalone mode - required files not found locally"
    fi
    
    download_required_files
    SCRIPT_DIR="$TEMP_DIR"
    echo "📁 Using downloaded files from: $SCRIPT_DIR"
else
    echo "📁 Using local files from: $SCRIPT_DIR"
fi

# Verify all required files are now available
if [[ ! -f "$SCRIPT_DIR/requirements.txt" ]]; then
    echo "❌ Error: requirements.txt not found in $SCRIPT_DIR"
    echo "💡 Make sure you're running this script from the MaxCLI directory or that the download succeeded"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/main.py" ]]; then
    echo "❌ Error: main.py not found in $SCRIPT_DIR"
    echo "💡 Make sure you're running this script from the MaxCLI directory or that the download succeeded"
    exit 1
fi

if [[ ! -d "$SCRIPT_DIR/maxcli" ]]; then
    echo "❌ Error: maxcli package directory not found in $SCRIPT_DIR"
    echo "💡 Make sure you're running this script from the MaxCLI directory or that the download succeeded"
    exit 1
fi

echo "✅ All required files found successfully"

# Install Xcode command line tools
echo ""
echo "📱 Installing Xcode command line tools..."
xcode-select --install 2>/dev/null || echo "✅ Xcode tools already installed"

# Function to check if we have admin privileges
check_admin_privileges() {
    if sudo -n true 2>/dev/null; then
        return 0  # Has admin access
    else
        return 1  # No admin access
    fi
}

# Function to install Homebrew with fallback for non-admin users
install_homebrew() {
    echo ""
    echo "🍺 Installing Homebrew..."
    
    if command -v brew &> /dev/null; then
        echo "✅ Homebrew already installed"
        return 0
    fi
    
    if check_admin_privileges; then
        echo "🔑 Admin privileges detected - installing Homebrew system-wide"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        return $?
    else
        echo "⚠️  No admin privileges detected"
        echo "📁 Installing Homebrew to user directory (~/.homebrew)"
        
        # Create user homebrew directory
        mkdir -p ~/.homebrew
        
        # Download and extract Homebrew
        if curl -L https://github.com/Homebrew/brew/tarball/master | tar xz --strip 1 -C ~/.homebrew; then
            # Add to PATH for this session
            export PATH="$HOME/.homebrew/bin:$PATH"
            
            # Add to shell configuration
            if ! grep -q 'export PATH="$HOME/.homebrew/bin:$PATH"' ~/.zshrc 2>/dev/null; then
                echo 'export PATH="$HOME/.homebrew/bin:$PATH"' >> ~/.zshrc
                echo "✅ Added user Homebrew to PATH in ~/.zshrc"
            fi
            
            echo "✅ Homebrew installed successfully in user directory"
            return 0
        else
            echo "❌ Failed to install Homebrew in user directory"
            return 1
        fi
    fi
}

# Function to check Python availability and install if needed
setup_python() {
    echo ""
    echo "🐍 Setting up Python environment..."
    
    # Check if python3 is available
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d ' ' -f 2 | cut -d '.' -f 1-2)
        echo "✅ Found Python $PYTHON_VERSION"
        
        # Check if it's a suitable version (3.8+)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            echo "✅ Python version is suitable for MaxCLI"
            return 0
        else
            echo "⚠️  Python version is too old (need 3.8+)"
        fi
    else
        echo "❌ Python 3 not found"
    fi
    
    # Try to install Python via Homebrew
    if command -v brew &> /dev/null; then
        echo "📦 Installing Python via Homebrew..."
        if brew install python; then
            echo "✅ Python installed successfully"
            return 0
        else
            echo "❌ Failed to install Python via Homebrew"
        fi
    fi
    
    # If we get here, we need to suggest manual installation
    echo ""
    echo "❌ Unable to install Python automatically"
    echo "💡 Please install Python 3.8+ manually using one of these methods:"
    echo ""
    echo "Option 1 - Official Python installer:"
    echo "   https://www.python.org/downloads/macos/"
    echo ""
    echo "Option 2 - Pyenv (if available):"
    echo "   pyenv install 3.11.0"
    echo "   pyenv global 3.11.0"
    echo ""
    echo "Option 3 - Conda/Miniconda:"
    echo "   conda create -n maxcli python=3.11"
    echo "   conda activate maxcli"
    echo ""
    echo "After installing Python, re-run this script."
    exit 1
}

# Function to install additional dependencies
install_dependencies() {
    echo ""
    echo "📦 Installing additional dependencies..."
    
    # Try to install via Homebrew if available
    if command -v brew &> /dev/null; then
        echo "🔧 Installing pipx and GPG via Homebrew..."
        brew install pipx gnupg gnupg2 2>/dev/null || {
            echo "⚠️  Some Homebrew packages failed to install"
            echo "💡 GPG encryption features may not be available"
        }
        
        # Ensure pipx is in PATH
        pipx ensurepath 2>/dev/null || echo "⚠️  pipx not available"
    else
        echo "⚠️  Homebrew not available - skipping optional dependencies"
        echo "💡 GPG encryption features will not be available"
        echo "💡 You can install them manually later if needed"
    fi
}

# Main installation flow
install_homebrew
setup_python
install_dependencies

# Create virtual environment for maxcli
echo ""
echo "📦 Setting up MaxCLI virtual environment..."

# Ensure the .venvs directory exists
mkdir -p ~/.venvs

# Create virtual environment with error checking
if python3 -m venv ~/.venvs/maxcli; then
    echo "✅ Virtual environment created successfully"
else
    echo "❌ Failed to create virtual environment"
    echo "💡 This might be due to:"
    echo "   • Python venv module not available (try: python3 -m pip install --user virtualenv)"
    echo "   • Insufficient disk space"
    echo "   • Permission issues with ~/.venvs directory"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "   1. Check Python installation: python3 --version"
    echo "   2. Check venv availability: python3 -m venv --help"
    echo "   3. Try manual creation: python3 -m venv ~/.venvs/maxcli"
    exit 1
fi

# Activate virtual environment with error checking
if source ~/.venvs/maxcli/bin/activate; then
    echo "✅ Virtual environment activated"
else
    echo "❌ Failed to activate virtual environment"
    echo "💡 The virtual environment was created but can't be activated"
    echo "🔧 Please check ~/.venvs/maxcli/bin/activate exists and is readable"
    exit 1
fi

# Verify Python in virtual environment
if [[ -f ~/.venvs/maxcli/bin/python ]]; then
    echo "✅ Python available in virtual environment: $(~/.venvs/maxcli/bin/python --version)"
else
    echo "❌ Python not found in virtual environment"
    echo "💡 Virtual environment creation may have failed silently"
    exit 1
fi

# Install dependencies (using absolute path)
echo ""
echo "📚 Installing dependencies..."
if pip install -r "$SCRIPT_DIR/requirements.txt"; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    echo "💡 This might be due to:"
    echo "   • Network connectivity issues"
    echo "   • Missing build tools for some packages"
    echo "   • Pip not available in virtual environment"
    echo ""
    echo "🔧 You can try installing manually:"
    echo "   source ~/.venvs/maxcli/bin/activate"
    echo "   pip install --upgrade pip"
    echo "   pip install questionary colorama requests pynacl"
    exit 1
fi

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."
FAILED_IMPORTS=""

for package in questionary colorama requests; do
    if ! ~/.venvs/maxcli/bin/python -c "import $package" 2>/dev/null; then
        FAILED_IMPORTS="$FAILED_IMPORTS $package"
    fi
done

if [[ -n "$FAILED_IMPORTS" ]]; then
    echo "❌ Some critical packages failed to import:$FAILED_IMPORTS"
    echo "💡 Trying to install them individually..."
    
    for package in $FAILED_IMPORTS; do
        echo "📦 Installing $package..."
        pip install "$package" || echo "⚠️  Failed to install $package"
    done
else
    echo "✅ All critical dependencies verified"
fi

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
MAXCLI_ACTIVATE="$MAXCLI_VENV/bin/activate"

# Function to show detailed troubleshooting information
show_troubleshooting() {
    echo ""
    echo "🔧 MaxCLI Troubleshooting Guide:"
    echo "================================="
    echo ""
    echo "📋 Environment Status:"
    echo "   Virtual environment: $MAXCLI_VENV"
    echo "   Python executable: $MAXCLI_PYTHON"
    echo "   Activation script: $MAXCLI_ACTIVATE"
    echo ""
    
    # Check what exists
    if [[ -d "$MAXCLI_VENV" ]]; then
        echo "   ✅ Virtual environment directory exists"
    else
        echo "   ❌ Virtual environment directory missing"
    fi
    
    if [[ -f "$MAXCLI_PYTHON" ]]; then
        echo "   ✅ Python executable exists"
        echo "   📊 Python version: $("$MAXCLI_PYTHON" --version 2>/dev/null || echo 'Failed to get version')"
    else
        echo "   ❌ Python executable missing"
    fi
    
    if [[ -f "$MAXCLI_ACTIVATE" ]]; then
        echo "   ✅ Activation script exists"
    else
        echo "   ❌ Activation script missing"
    fi
    
    # Check for MaxCLI package
    if [[ -d "$HOME/.local/lib/python/maxcli" ]]; then
        echo "   ✅ MaxCLI package directory exists"
    else
        echo "   ❌ MaxCLI package directory missing"
    fi
    
    echo ""
    echo "🚀 Possible Solutions:"
    echo ""
    echo "1️⃣  Re-run the bootstrap script:"
    echo "   curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash"
    echo ""
    echo "2️⃣  Manual virtual environment recreation:"
    echo "   rm -rf ~/.venvs/maxcli"
    echo "   python3 -m venv ~/.venvs/maxcli"
    echo "   source ~/.venvs/maxcli/bin/activate"
    echo "   pip install questionary colorama requests pynacl"
    echo ""
    echo "3️⃣  Check system Python:"
    echo "   python3 --version"
    echo "   python3 -m venv --help"
    echo ""
    echo "4️⃣  Alternative installation (if you have Homebrew):"
    echo "   brew install python"
    echo "   python3 -m venv ~/.venvs/maxcli"
    echo "   # Then re-run bootstrap"
    echo ""
    echo "💡 For more help, visit: https://github.com/maximilianls98/maxcli/issues"
}

# Check if the maxcli virtual environment exists
if [[ ! -f "$MAXCLI_PYTHON" ]]; then
    echo "❌ Error: MaxCLI virtual environment not found"
    echo "📍 Expected location: $MAXCLI_VENV"
    echo ""
    echo "💡 This usually means the bootstrap script didn't complete successfully."
    echo "   The virtual environment creation may have failed due to:"
    echo "   • Missing Python 3.8+ installation"
    echo "   • No admin privileges to install dependencies"
    echo "   • Network issues during package downloads"
    echo "   • Insufficient disk space"
    echo ""
    
    # Show basic environment info
    echo "🔍 Current environment:"
    if command -v python3 &> /dev/null; then
        echo "   Python: $(python3 --version 2>/dev/null || echo 'Available but version check failed')"
    else
        echo "   Python: ❌ Not found in PATH"
    fi
    
    if command -v brew &> /dev/null; then
        echo "   Homebrew: ✅ Available"
    else
        echo "   Homebrew: ❌ Not available"
    fi
    
    show_troubleshooting
    exit 1
fi

# Check if questionary is installed in the virtual environment
if ! "$MAXCLI_PYTHON" -c "import questionary" 2>/dev/null; then
    echo "⚠️  Warning: Dependencies missing in MaxCLI environment"
    echo "📦 Questionary package not found - MaxCLI may not work properly"
    echo ""
    echo "🔧 Quick fix - install dependencies:"
    echo "   source $MAXCLI_ACTIVATE"
    echo "   pip install questionary colorama requests pynacl"
    echo ""
    echo "💡 Or re-run the bootstrap script to fix all dependencies:"
    echo "   curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash"
    echo ""
    
    # Still try to run MaxCLI in case some functionality works
    echo "🚀 Attempting to run MaxCLI anyway..."
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
try:
    from maxcli.cli import main
    main()
except ImportError as e:
    print('❌ Error: Failed to import MaxCLI')
    print(f'📍 Import error: {e}')
    print('')
    print('💡 This usually means:')
    print('   • MaxCLI package not properly installed')
    print('   • Missing dependencies in virtual environment')
    print('   • Corrupted installation')
    print('')
    print('🔧 To fix this, re-run the bootstrap script:')
    print('   curl -fsSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error: MaxCLI crashed: {e}')
    print('')
    print('💡 For help with this error, visit:')
    print('   https://github.com/maximilianls98/maxcli/issues')
    sys.exit(1)
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
cat > ~/.config/maxcli/modules_config.json << EOF
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
      "commands": ["ssh-backup export", "ssh-backup import"],
      "dependencies": ["gpg"]
    },
    "ssh_rsync": {
      "enabled": $(if [[ " ${enabled_modules[*]} " =~ " ssh_rsync " ]]; then echo "true"; else echo "false"; fi),
      "description": "SSH-based rsync operations and remote backup",
      "commands": ["ssh-rsync upload-backup", "ssh-rsync download-backup"],
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
      "commands": ["gcp"],
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
      "description": "Database backup utilities, CSV data processing, and application deployment tools",
      "commands": ["backup-db", "deploy-app", "process-csv"],
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
echo "🔧 Installation Modes:"
echo "   • Standalone: curl -fsSL https://raw.githubusercontent.com/$GITHUB_REPO/$GITHUB_BRANCH/bootstrap.sh | bash"
echo "   • Local: git clone && cd maxcli && ./bootstrap.sh"
echo "   • Force download: ./bootstrap.sh --force-download"
echo "   • Custom repo: ./bootstrap.sh --github-repo=yourfork/maxcli"
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

# Cleanup temporary files before showing completion
if [[ "$CLEANUP_REQUIRED" == "true" ]]; then
    cleanup
    # Reset cleanup flag so trap doesn't run again
    CLEANUP_REQUIRED=false
fi

# Footer art
cat << "EOF"
    ┌─────────────────────────────────────────┐
    │  Ready to supercharge your workflow! 🚀 │
    └─────────────────────────────────────────┘
EOF