"""Configuration management for MaxCLI."""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .utils.interactive import prompt_for_config_value

# Configuration constants
CONFIG_DIR = Path.home() / ".config" / "maxcli"
CONFIG_FILE = CONFIG_DIR / "config.json"

def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> Dict[str, Any]:
    """Load configuration from file, return empty dict if file doesn't exist."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Warning: Could not load config file: {e}")
            return {}
    return {}

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f"❌ Error saving config: {e}")
        return False

def is_initialized() -> bool:
    """Check if the CLI has been initialized with user configuration."""
    config = load_config()
    required_fields = ['git_name', 'git_email']
    return all(field in config and config[field] for field in required_fields)

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    config = load_config()
    return config.get(key, default)

def get_quota_project_mappings() -> Dict[str, str]:
    """Get the quota project mappings from config."""
    config = load_config()
    return config.get('quota_project_mappings', {})

def check_initialization():
    """Check if CLI is initialized, prompt user if not."""
    if not is_initialized():
        print("🔧 MaxCLI needs to be initialized with your personal configuration.")
        print("This is a one-time setup to personalize the tool for your use.")
        print()
        
        if input("Initialize now? (y/n): ").lower().startswith('y'):
            print()
            # Import here to avoid circular import
            from .commands.config_management import init_config
            # Create a mock args object for init_config
            class MockArgs:
                force = False
            init_config(MockArgs())
        else:
            print("❌ Initialization cancelled. Some features may not work correctly.")
            print("💡 Run 'max init' when you're ready to configure the tool.")
            sys.exit(1)

def init_config(args):
    """Initialize or update user configuration."""
    print("🚀 MaxCLI Configuration Setup")
    print("=" * 40)
    
    # Load existing config if it exists
    config = load_config()
    
    if config and not args.force:
        print("✅ Configuration already exists!")
        print(f"📁 Config location: {CONFIG_FILE}")
        print("\nCurrent configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        update = input("\nDo you want to update your configuration? (y/n): ").lower().startswith('y')
        if not update:
            print("Configuration unchanged.")
            return
        print()
    
    print("Please provide your personal details for git configuration and dotfiles:")
    print()
    
    # Git configuration
    config['git_name'] = prompt_for_config_value(
        "Git username (for git config --global user.name) Hint: This is the name you want to use for your git commits",
        config.get('git_name')
    )
    
    config['git_email'] = prompt_for_config_value(
        "Git email (for git config --global user.email) Hint: This is the email you want to use for your git commits",
        config.get('git_email')
    )
    
    # Dotfiles repository (optional)
    print("\nDotfiles repository (optional):")
    config['dotfiles_repo'] = prompt_for_config_value(
        "Dotfiles git repository URL (leave empty to skip)",
        config.get('dotfiles_repo'),
        required=False
    )
    
    # GCP project mappings (optional)
    print("\nGoogle Cloud Platform project mappings (optional):")
    print("You can configure custom project mappings for different gcloud configs.")
    print("Hint: This is useful if you have multiple GCP projects and want to switch between them easily. It then changes the quota project for the given config.")
    # Load existing quota project mappings or create new ones
    if 'quota_project_mappings' not in config:
        config['quota_project_mappings'] = {}
    
    manage_mappings = input("Do you want to configure GCP project mappings now? (y/n): ").lower().startswith('y')
    if manage_mappings:
        print("\nEnter your GCP project mappings (config_name -> project_id):")
        print("Press Enter with empty config name to finish.")
        
        while True:
            config_name = input("Config name (empty to finish): ").strip()
            if not config_name:
                break
                
            project_id = prompt_for_config_value(
                f"Project ID for '{config_name}'",
                config['quota_project_mappings'].get(config_name)
            )
            config['quota_project_mappings'][config_name] = project_id
    
    # Save configuration
    if save_config(config):
        print(f"\n✅ Configuration saved to: {CONFIG_FILE}")
        
        # ASCII Art for successful configuration
        print("\n" + "="*60)
        print("""
   ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗ 
  ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝ 
  ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗
  ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║
  ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝
   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝ 
                                                   
     ██████╗ ██████╗ ███╗   ███╗██████╗ ██╗     ███████╗████████╗███████╗██╗
    ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██║     ██╔════╝╚══██╔══╝██╔════╝██║
    ██║     ██║   ██║██╔████╔██║██████╔╝██║     █████╗     ██║   █████╗  ██║
    ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝     ██║   ██╔══╝  ╚═╝
    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ███████╗███████╗   ██║   ███████╗██╗
     ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝
        """)
        print("="*60)
        print("\n🎉 MaxCLI is now personalized and ready to use!")
        print("🚀 Your development workflow just got supercharged!")
        print(f"\n📁 Configuration saved to: {CONFIG_FILE}")
        print("\n💡 You can update/rewrite this configuration anytime with: max init --force")
        print("\n🎯 Next steps:")
        print("   • Try: max setup apps --interactive")
        print("   • Or:  max create-config")
        print("   • Or:  max --help")
        
        # Footer box
        print("\n" + "┌" + "─"*58 + "┐")
        print("│" + " "*20 + "Happy coding! 🎉" + " "*20 + "│")
        print("└" + "─"*58 + "┘")
        
    else:
        print("\n❌ Failed to save configuration.")
        sys.exit(1) 