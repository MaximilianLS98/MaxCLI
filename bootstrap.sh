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
echo "   2. Initialize the CLI: max init"
echo "   3. Start using the tool: max --help"
echo ""
echo "💡 The 'max init' command will guide you through setting up your personal configuration."
echo ""

# Footer art
cat << "EOF"
    ┌─────────────────────────────────────────┐
    │  Ready to supercharge your workflow! 🚀 │
    └─────────────────────────────────────────┘
EOF