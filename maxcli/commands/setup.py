"""Development environment setup commands."""
from pathlib import Path
import os
import shutil
import uuid

from ..runtime import CommandError

from ..config import check_initialization, get_config_value
from ..utils.system import (
    run, install_homebrew, install_brew_packages, install_cask_apps,
    install_ohmyzsh, install_pipx_tools
)
from ..utils.interactive import interactive_checkbox

def setup_git_config():
    """Setup git configuration using values from config file."""
    check_initialization()
    
    git_name = get_config_value('git_name')
    git_email = get_config_value('git_email')
    
    if git_name and git_email:
        run(['git', 'config', '--global', 'user.name', git_name])
        run(['git', 'config', '--global', 'user.email', git_email])
        print(f"✅ Git configured for {git_name} <{git_email}>")
    else:
        print("⚠️ Git name/email not configured. Run 'max init' to set up.")

def clone_dotfiles(dry_run=False):
    """Clone dotfiles repository if configured."""
    dotfiles_repo = get_config_value('dotfiles_repo')
    
    if not dotfiles_repo:
        print("💡 No dotfiles repository configured. Skipping...")
        print("   You can add one with: max init --force")
        return
    
    dotfiles_path = Path.home().joinpath("dotfiles")
    if dry_run:
        print('Would clone configured dotfiles if missing and back up .zshrc/.gitconfig before replacement.')
        return
    if not dotfiles_path.exists():
        print(f"📂 Cloning dotfiles from {dotfiles_repo}...")
        run(["git", "clone", "--", dotfiles_repo, str(dotfiles_path)])
    else:
        print("✅ Dotfiles already cloned.")
        
    # Copy common dotfiles if they exist
    for dotfile in ['.zshrc', '.gitconfig']:
        source = dotfiles_path / dotfile
        dest = Path.home() / dotfile
        if source.exists():
            if source.is_symlink():
                raise CommandError('Refusing dotfile source symlink: {}'.format(source))
            backup = None
            if dest.exists() or dest.is_symlink():
                backup = dest.with_name(dest.name + '.maxcli-backup-' + uuid.uuid4().hex[:8])
                os.replace(dest, backup)
                print('Preserved existing {} at {}'.format(dest, backup))
            try:
                shutil.copy2(source, dest)
            except BaseException:
                if backup:
                    os.replace(backup, dest)
                raise

def minimal_setup(_args):
    """Minimal terminal and git setup for basic development."""
    if getattr(_args, 'dry_run', False):
        print('Would install the profile tools and configure Git. Full setup also backs up and replaces configured dotfiles.')
        return
    install_homebrew()
    install_brew_packages(["git", "zsh", "wget", "htop", "stow"])
    install_ohmyzsh()
    setup_git_config()
    print("✅ Minimal setup completed.")

def dev_full_setup(_args):
    """Complete development environment with languages and tools."""
    if getattr(_args, 'dry_run', False):
        print('Would install the profile tools and configure Git. Full setup also backs up and replaces configured dotfiles.')
        return
    check_initialization()
    install_homebrew()
    install_brew_packages([
        "git", "node", "nvm", "python", "docker", "kubectl",
        "awscli", "terraform", "google-cloud-sdk", "tmux", "stow"
    ])
    
    # Install essential GUI applications for development
    dev_gui_apps = ["rectangle", "shottr"]
    install_cask_apps(dev_gui_apps)
    
    install_ohmyzsh()
    install_pipx_tools()
    setup_git_config()
    clone_dotfiles()
    print("✅ Dev Full setup completed.")

def interactive_app_selection():
    """Show interactive menu for app selection."""
    # Available apps with descriptions
    available_apps = [
        ("visual-studio-code", "Visual Studio Code - Popular code editor"),
        ("cursor", "Cursor - AI-powered code editor"),
        ("ghostty", "Ghostty - Modern GPU-accelerated terminal"),
        ("slack", "Slack - Team communication"),
        ("google-chrome", "Google Chrome - Web browser"),
        ("arc", "Arc Browser - Modern web browser"),
        ("postman", "Postman - API testing tool"),
        ("docker", "Docker Desktop - Container platform"),
        ("orbstack", "OrbStack - Fast, light, simple Docker & Linux on macOS")
    ]
    
    return interactive_checkbox("What would you like to install?", available_apps)

def apps_setup(args):
    """Install essential GUI applications for development and productivity."""
    if getattr(args, 'dry_run', False):
        print('Would install selected GUI applications through Homebrew Cask.')
        return
    install_homebrew()
    
    # Check if user wants to install all apps without interaction
    if hasattr(args, 'all') and args.all:
        # Install all apps without prompting
        default_apps = [
            "visual-studio-code", "cursor", "ghostty", "slack", "google-chrome",
            "arc", "postman", "docker", "orbstack"
        ]
        print("📦 Installing all GUI applications...")
        install_cask_apps(default_apps)
    else:
        # Default behavior - interactive selection
        selected_apps = interactive_app_selection()
        
        if not selected_apps:
            print("✅ No applications selected for installation.")
            return
            
        print(f"\n📦 Installing {len(selected_apps)} selected applications...")
        install_cask_apps(selected_apps)
    
    print("✅ Apps setup completed.")

def setup(_args):
    """Main setup command - shows help for subcommands."""
    print("✨ Use one of the subcommands: minimal, dev-full, apps")
    print("\nAvailable setup profiles:")
    print("  minimal   - Basic terminal and git configuration")
    print("  dev-full  - Complete development environment")
    print("  apps      - GUI applications for productivity")
    print("\nExamples:")
    print("  max setup minimal")
    print("  max setup dev-full")
    print("  max setup apps --interactive") 