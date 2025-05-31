"""Google Cloud Platform related commands."""
import os
import sys
import subprocess
from typing import List

from ..config import get_quota_project_mappings, load_config, save_config
from ..utils.interactive import interactive_selection

def get_available_configs() -> List[str]:
    """Get list of available gcloud configurations with ADC files."""
    configs = []
    adc_dir = os.path.expanduser("~/.config/gcloud")
    if os.path.exists(adc_dir):
        for f in os.listdir(adc_dir):
            if f.startswith("adc_") and f.endswith(".json"):
                configs.append(f[4:-5])  # Remove "adc_" prefix and ".json" suffix
    return sorted(configs)

def interactive_config_selection() -> str:
    """Show interactive menu for config selection."""
    configs = get_available_configs()
    
    if not configs:
        print("❌ No configurations with ADC files found.")
        print("💡 Create a new configuration with: max create-config <name>")
        sys.exit(1)
    
    selected = interactive_selection("Select a gcloud configuration:", configs)
    
    if selected is None:
        print("\n❌ Configuration switch cancelled.")
        sys.exit(0)
        
    return selected

def switch_config(args):
    """Switch gcloud config and application default credentials."""
    config_name = args.name
    
    if not config_name:
        config_name = interactive_config_selection()
    
    print(f"Switching gcloud config to '{config_name}'...")
    subprocess.run(["gcloud", "config", "configurations", "activate", config_name], check=True)

    adc_file = os.path.expanduser(f"~/.config/gcloud/adc_{config_name}.json")
    dest_adc = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")

    if os.path.exists(adc_file):
        subprocess.run(["cp", adc_file, dest_adc], check=True)
        print(f"Switched ADC credentials for config '{config_name}'.")

        quota_project_mappings = get_quota_project_mappings()
        quota_project = quota_project_mappings.get(config_name)

        if quota_project:
            print(f"Setting quota project to '{quota_project}'...")
            subprocess.run(["gcloud", "auth", "application-default", "set-quota-project", quota_project], check=True)
        else:
            print(f"No quota project mapping for '{config_name}'.")
    else:
        print(f"ADC file for '{config_name}' not found.", file=sys.stderr)
        sys.exit(1)

def create_config(args):
    """Create a new gcloud configuration with proper authentication and ADC setup."""
    config_name = args.name
    print(f"Creating new gcloud configuration '{config_name}'...")
    
    try:
        # Step 1: Create new configuration
        print("Creating gcloud configuration...")
        subprocess.run(["gcloud", "config", "configurations", "create", config_name], check=True)
        
        # Step 2: Activate the new configuration
        print(f"Activating configuration '{config_name}'...")
        subprocess.run(["gcloud", "config", "configurations", "activate", config_name], check=True)
        
        # Step 3: Authenticate with Google account
        print("Please authenticate with your Google account...")
        subprocess.run(["gcloud", "auth", "login"], check=True)
        
        # Step 4: Set up application default credentials
        print("Setting up application default credentials...")
        subprocess.run(["gcloud", "auth", "application-default", "login"], check=True)
        
        # Step 5: Copy ADC file for future switching
        source_adc = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
        dest_adc = os.path.expanduser(f"~/.config/gcloud/adc_{config_name}.json")
        
        if os.path.exists(source_adc):
            subprocess.run(["cp", source_adc, dest_adc], check=True)
            print(f"ADC credentials saved for config '{config_name}'.")
        else:
            print("Warning: ADC file not found after authentication.", file=sys.stderr)
            return
        
        # Step 6: Handle quota project setup
        setup_quota_project(config_name)
        
        print(f"✅ Configuration '{config_name}' created successfully!")
        print(f"You can now switch to this config using: max switch-config {config_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating configuration: {e}", file=sys.stderr)
        sys.exit(1)

def setup_quota_project(config_name: str):
    """Set up quota project for the given configuration."""
    quota_project_mappings = get_quota_project_mappings()
    quota_project = quota_project_mappings.get(config_name)
    
    if quota_project:
        print(f"Found existing quota project mapping: '{quota_project}'")
        confirm = input(f"Use '{quota_project}' as quota project? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            quota_project = None
    
    if not quota_project:
        print("No existing quota project mapping found.")
        quota_project = input("Enter quota project ID (or press Enter to skip): ").strip()
    
    if quota_project:
        try:
            print(f"Setting quota project to '{quota_project}'...")
            subprocess.run([
                "gcloud", "auth", "application-default", 
                "set-quota-project", quota_project
            ], check=True)
            print(f"Quota project set to '{quota_project}'.")
            
            if config_name not in quota_project_mappings:
                save_mapping = input(f"Save mapping '{config_name}' -> '{quota_project}' for future use? (y/n): ").strip().lower()
                if save_mapping in ['y', 'yes']:
                    config = load_config()
                    if 'quota_project_mappings' not in config:
                        config['quota_project_mappings'] = {}
                    config['quota_project_mappings'][config_name] = quota_project
                    if save_config(config):
                        print(f"✅ Mapping saved to configuration.")
                    else:
                        print(f"⚠️ Failed to save mapping to configuration.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to set quota project: {e}", file=sys.stderr)
    else:
        print("Skipping quota project setup.")

def list_configs(_args):
    """List all available gcloud configurations with ADC files."""
    print("Available configs with ADC files:")
    configs = get_available_configs()
    
    if not configs:
        print("  (No configurations found)")
        print("💡 Create a new configuration with: max create-config <name>")
    else:
        for config in configs:
            print(f"  {config}") 