"""System utility functions."""
import subprocess
import shutil
from typing import List

def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command with logging."""
    print(f"🔧 Running: {cmd}")
    return subprocess.run(cmd, shell=True, check=check)

def is_installed(binary_name: str) -> bool:
    """Check if a binary is installed and available in PATH."""
    return shutil.which(binary_name) is not None

def install_homebrew():
    """Install Homebrew if not already installed."""
    if not is_installed("brew"):
        print("🍺 Homebrew not found. Installing Homebrew...")
        run('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
    else:
        print("✅ Homebrew is already installed.")

def install_brew_packages(packages: List[str]):
    """Install Homebrew packages if they're not already installed."""
    for package in packages:
        print(f"📦 Checking {package}...")
        if subprocess.run(f"brew list {package}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            run(f"brew install {package}")
        else:
            print(f"✅ {package} already installed.")

def install_cask_apps(apps: List[str]):
    """Install Homebrew Cask applications if they're not already installed."""
    from pathlib import Path
    
    # Map cask names to actual application names in /Applications/
    app_name_mapping = {
        "visual-studio-code": "Visual Studio Code.app",
        "cursor": "Cursor.app", 
        "ghostty": "Ghostty.app",
        "slack": "Slack.app",
        "google-chrome": "Google Chrome.app",
        "arc": "Arc.app",
        "postman": "Postman.app",
        "docker": "Docker.app"
    }
    
    for app in apps:
        print(f"🖥️ Checking {app}...")
        
        # Check if app exists in /Applications/ (regardless of install method)
        app_name = app_name_mapping.get(app, f"{app.title()}.app")
        app_path = Path("/Applications").joinpath(app_name)
        
        if app_path.exists():
            print(f"✅ {app} already installed (found at {app_path}).")
            continue
            
        # Check if installed via Homebrew cask
        brew_check = subprocess.run(
            f"brew list --cask {app}", 
            shell=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        if brew_check.returncode == 0:
            print(f"✅ {app} already installed via Homebrew.")
            continue
            
        # App not found, install via Homebrew
        try:
            run(f"brew install --cask {app}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to install {app}: {e}")
            print(f"💡 You may need to install {app} manually if Homebrew cask is not available.")

def install_ohmyzsh():
    """Install Oh My Zsh if not already installed."""
    from pathlib import Path
    
    if not Path.home().joinpath(".oh-my-zsh").exists():
        print("🧰 Installing Oh My Zsh...")
        run('sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"', check=False)
    else:
        print("✅ Oh My Zsh already installed.")

def install_pipx_tools():
    """Install pipx and essential tools."""
    if not is_installed("pipx"):
        run("brew install pipx")
        run("pipx ensurepath")
    else:
        print("✅ pipx already installed.")
    run("pipx install argcomplete")
    run("pipx install questionary", check=False)  # Optional, for interactive CLI experience 