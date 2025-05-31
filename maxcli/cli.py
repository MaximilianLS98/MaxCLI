"""Main CLI module that handles argument parsing and command routing."""
import argparse

# Import command functions
from .config import init_config
from .commands.gcp import switch_config, create_config, list_configs
from .commands.docker import docker_clean, docker_tidy
from .commands.kubernetes import kctx
from .commands.setup import setup, minimal_setup, dev_full_setup, apps_setup
from .commands.misc import backup_db, deploy_app
from .commands.coolify import (
    coolify_health, coolify_services, coolify_applications, coolify_servers,
    coolify_resources, coolify_start_service, coolify_stop_service,
    coolify_restart_service, coolify_status, coolify_start_application,
    coolify_stop_application, coolify_restart_application, coolify_deploy_application
)

def add_setup_subcommands(subparsers):
    """Add setup subcommands to the argument parser."""
    setup_parser = subparsers.add_parser(
        'setup', 
        help='Setup a new laptop or development environment',
        description="""
Setup utilities for configuring a new laptop or development environment.

This command provides different setup profiles:
- minimal: Basic terminal and git configuration
- dev-full: Complete development environment with tools and languages
- apps: GUI applications for productivity and development

Each setup profile is idempotent - you can run them multiple times safely.
They will skip items that are already installed.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max setup minimal               # Basic terminal setup
  max setup dev-full              # Full development environment
  max setup apps                  # Install GUI applications
        """
    )
    setup_subparsers = setup_parser.add_subparsers(
        title="Setup Profiles", 
        dest="setup_command",
        description="Choose a setup profile based on your needs",
        metavar="<profile>"
    )
    setup_parser.set_defaults(func=setup)

    minimal_parser = setup_subparsers.add_parser(
        'minimal', 
        help='Minimal terminal and git setup for basic development',
        description="""
Install and configure basic development tools for terminal usage.

This lightweight setup includes:
- Homebrew package manager (if not installed)
- Essential command-line tools: git, zsh, wget, htop
- Oh My Zsh for enhanced terminal experience
- Basic git configuration setup

Perfect for:
- Setting up a basic development environment
- Servers or minimal installations
- Users who prefer to manually install additional tools
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max setup minimal              # Install basic development tools
        """
    )
    minimal_parser.set_defaults(func=minimal_setup)

    dev_full_parser = setup_subparsers.add_parser(
        'dev-full', 
        help='Complete development environment with languages and tools',
        description="""
Install a comprehensive development environment with popular tools and languages.

This full setup includes everything from 'minimal' plus:
- Programming languages: Node.js (via nvm), Python
- Container tools: Docker, kubectl  
- Cloud tools: AWS CLI, Google Cloud SDK, Terraform
- Development tools: tmux for terminal multiplexing
- pipx for Python CLI tool management
- Dotfiles cloning and configuration

Perfect for:
- New developer laptops
- Setting up a complete coding environment
- Full-stack development work
- DevOps and cloud development

NOTE: You'll need to update the dotfiles repository URL in the configuration.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max setup dev-full             # Install complete development environment
        """
    )
    dev_full_parser.set_defaults(func=dev_full_setup)

    apps_parser = setup_subparsers.add_parser(
        'apps', 
        help='Install essential GUI applications for development and productivity',
        description="""
Install popular GUI applications using Homebrew Cask.

By default, this installs all applications:
- Development: Visual Studio Code, Cursor AI Editor, Docker Desktop
- Communication: Slack  
- Browsers: Google Chrome, Arc Browser
- API Testing: Postman
- Terminal: Ghostty (modern GPU-accelerated terminal)

INTERACTIVE MODE: Use --interactive flag to choose specific applications to install.
You can select individual apps, install all, or skip installation entirely.

All applications are installed via Homebrew Cask, making them easy to manage
and update. The installation will skip apps that are already installed.

Perfect for:
- Setting up GUI applications on a new Mac
- Standardizing application installs across team members
- Customizing which productivity applications to install
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max setup apps                 # Install all GUI applications (default)
  max setup apps --interactive   # Choose specific apps to install
  
Interactive mode provides:
- Checkbox selection with Space/Enter (if questionary available)
- Numbered selection with fallback mode
- Options to install all, none, or specific applications
        """
    )
    apps_parser.add_argument('--interactive', action='store_true', help='Interactive app selection')
    apps_parser.set_defaults(func=apps_setup)

def add_coolify_subcommands(subparsers):
    """Add Coolify management subcommands to the argument parser."""
    coolify_parser = subparsers.add_parser(
        'coolify', 
        help='Manage Coolify instance through API',
        description="""
Manage your Coolify instance through its REST API.

This command provides comprehensive management of your Coolify resources including:
- Health monitoring and status overview
- Services, applications, and databases management
- Server monitoring and resource viewing
- Service lifecycle operations (start/stop/restart)

All commands use the API key and instance URL configured during 'max init'.
The API provides real-time information about your deployments and infrastructure.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify status              # Overall status overview
  max coolify health              # Check instance health
  max coolify services            # List all services
  max coolify applications        # List all applications  
  max coolify servers             # List all servers
  max coolify start-service <uuid> # Start a specific service
  max coolify stop-service <uuid>  # Stop a specific service
        """
    )
    coolify_subparsers = coolify_parser.add_subparsers(
        title="Coolify Commands", 
        dest="coolify_command",
        description="Choose a Coolify management operation",
        metavar="<command>"
    )
    coolify_parser.set_defaults(func=coolify_status)

    # Health check command
    health_parser = coolify_subparsers.add_parser(
        'health', 
        help='Check Coolify instance health',
        description="""
Check the health status of your Coolify instance.

This command calls the /health endpoint to verify that your Coolify instance
is running and accessible. It's useful for monitoring and troubleshooting
connectivity issues.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify health              # Check if Coolify is healthy
        """
    )
    health_parser.set_defaults(func=coolify_health)

    # Status overview command  
    status_parser = coolify_subparsers.add_parser(
        'status', 
        help='Show overall Coolify status with resource summary',
        description="""
Display a comprehensive status overview of your Coolify instance.

This command provides a high-level summary including:
- Instance health status
- Count of applications by status (running/stopped/other)
- Count of services by status
- Count of servers and their reachability
- Count of databases by status

Perfect for getting a quick overview of your entire infrastructure.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify status              # Show status overview (default command)
        """
    )
    status_parser.set_defaults(func=coolify_status)

    # Services command
    services_parser = coolify_subparsers.add_parser(
        'services', 
        help='List all services and their status',
        description="""
List all services deployed in your Coolify instance.

This command shows:
- Service names and current status
- Which server each service is deployed to
- Service UUIDs (needed for start/stop/restart operations)
- Detailed status information with visual indicators

Services include one-click services like databases, monitoring tools,
and other containerized applications managed by Coolify.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify services            # List all services with status
        """
    )
    services_parser.set_defaults(func=coolify_services)

    # Applications command
    apps_parser = coolify_subparsers.add_parser(
        'applications', 
        help='List all applications and their status', 
        description="""
List all applications deployed in your Coolify instance.

This command shows:
- Application names and current status
- Which server each application is deployed to
- Git repository information
- Application UUIDs for management operations
- Detailed status information with visual indicators

Applications include web apps, APIs, static sites, and other
custom deployments managed through Coolify.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify applications        # List all applications with status
        """
    )
    apps_parser.set_defaults(func=coolify_applications)

    # Servers command
    servers_parser = coolify_subparsers.add_parser(
        'servers', 
        help='List all servers and their status',
        description="""
List all servers connected to your Coolify instance.

This command shows:
- Server names and reachability status
- IP addresses and connection information
- Server UUIDs for management operations
- Visual indicators for server health

Servers are the physical or virtual machines where your applications
and services are deployed. Monitoring their status is crucial for
maintaining a healthy infrastructure.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify servers             # List all servers with status
        """
    )
    servers_parser.set_defaults(func=coolify_servers)

    # Resources command
    resources_parser = coolify_subparsers.add_parser(
        'resources', 
        help='List all resources (combined view)',
        description="""
List all resources in your Coolify instance with a combined view.

This command provides a unified view of all resources grouped by type:
- Applications (web apps, APIs, static sites)
- Services (databases, monitoring tools, etc.)
- Servers (physical/virtual machines)
- Other resource types

Perfect for getting an organized overview of your entire infrastructure
with resources categorized for easy management.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify resources           # Show all resources grouped by type
        """
    )
    resources_parser.set_defaults(func=coolify_resources)

    # Start service command
    start_parser = coolify_subparsers.add_parser(
        'start-service', 
        help='Start a service by UUID',
        description="""
Start a stopped service using its UUID.

This command sends a start request to the specified service. The service
must be in a stopped or exited state to be started. You can get the UUID
from the 'max coolify services' command.

The command will send the start request and confirm receipt, but the actual
startup process may take some time depending on the service.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify start-service abc123-def456-ghi789  # Start service by UUID
  max coolify services                            # Get UUIDs first
        """
    )
    start_parser.add_argument('uuid', help='Service UUID to start')
    start_parser.set_defaults(func=coolify_start_service)

    # Stop service command
    stop_parser = coolify_subparsers.add_parser(
        'stop-service', 
        help='Stop a service by UUID',
        description="""
Stop a running service using its UUID.

This command sends a stop request to the specified service. The service
must be in a running state to be stopped. You can get the UUID from the
'max coolify services' command.

The command will send the stop request and confirm receipt, but the actual
shutdown process may take some time depending on the service.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify stop-service abc123-def456-ghi789   # Stop service by UUID
  max coolify services                            # Get UUIDs first
        """
    )
    stop_parser.add_argument('uuid', help='Service UUID to stop')
    stop_parser.set_defaults(func=coolify_stop_service)

    # Restart service command
    restart_parser = coolify_subparsers.add_parser(
        'restart-service', 
        help='Restart a service by UUID',
        description="""
Restart a service using its UUID.

This command sends a restart request to the specified service. This is
equivalent to stopping and then starting the service. You can get the UUID
from the 'max coolify services' command.

The command will send the restart request and confirm receipt, but the actual
restart process may take some time depending on the service.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify restart-service abc123-def456-ghi789 # Restart service by UUID
  max coolify services                             # Get UUIDs first
        """
    )
    restart_parser.add_argument('uuid', help='Service UUID to restart')
    restart_parser.set_defaults(func=coolify_restart_service)

    # Start application command
    start_app_parser = coolify_subparsers.add_parser(
        'start-application', 
        help='Start an application by UUID',
        description="""
Start a stopped application using its UUID.

This command sends a start request to the specified application. The application
must be in a stopped or exited state to be started. You can get the UUID
from the 'max coolify applications' command.

The command will send the start request and confirm receipt, but the actual
startup process may take some time depending on the application.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify start-application abc123-def456-ghi789  # Start application by UUID
  max coolify applications                            # Get UUIDs first
        """
    )
    start_app_parser.add_argument('uuid', help='Application UUID to start')
    start_app_parser.set_defaults(func=coolify_start_application)

    # Stop application command
    stop_app_parser = coolify_subparsers.add_parser(
        'stop-application', 
        help='Stop an application by UUID',
        description="""
Stop a running application using its UUID.

This command sends a stop request to the specified application. The application
must be in a running state to be stopped. You can get the UUID from the
'max coolify applications' command.

The command will send the stop request and confirm receipt, but the actual
shutdown process may take some time depending on the application.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify stop-application abc123-def456-ghi789   # Stop application by UUID
  max coolify applications                            # Get UUIDs first
        """
    )
    stop_app_parser.add_argument('uuid', help='Application UUID to stop')
    stop_app_parser.set_defaults(func=coolify_stop_application)

    # Restart application command
    restart_app_parser = coolify_subparsers.add_parser(
        'restart-application', 
        help='Restart an application by UUID',
        description="""
Restart an application using its UUID.

This command sends a restart request to the specified application. This is
equivalent to stopping and then starting the application. You can get the UUID
from the 'max coolify applications' command.

The command will send the restart request and confirm receipt, but the actual
restart process may take some time depending on the application.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify restart-application abc123-def456-ghi789 # Restart application by UUID
  max coolify applications                             # Get UUIDs first
        """
    )
    restart_app_parser.add_argument('uuid', help='Application UUID to restart')
    restart_app_parser.set_defaults(func=coolify_restart_application)

    # Deploy application command
    deploy_app_parser = coolify_subparsers.add_parser(
        'deploy-application', 
        help='Deploy an application by UUID',
        description="""
Deploy an application using its UUID.

This command triggers a new deployment of the specified application. This will
pull the latest code from the configured repository, build the application,
and deploy it. You can get the UUID from the 'max coolify applications' command.

The command will send the deployment request and confirm receipt, but the actual
deployment process may take several minutes depending on the application complexity.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify deploy-application abc123-def456-ghi789  # Deploy application by UUID
  max coolify applications                             # Get UUIDs first
        """
    )
    deploy_app_parser.add_argument('uuid', help='Application UUID to deploy')
    deploy_app_parser.set_defaults(func=coolify_deploy_application)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='max', 
        description="Max's Personal CLI - A collection of useful development and operations commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max init                        # Initialize CLI with your personal configuration
  max create-config myproject     # Create new gcloud config with full setup
  max switch-config altekai       # Switch to existing gcloud config
  max list-configs                # Show all available configurations
  max kctx my-k8s-context         # Switch Kubernetes context
  max docker-clean                # Clean up Docker system
  max docker-tidy                 # Gentle Docker cleanup
  max setup minimal               # Basic development environment setup
  max setup dev-full              # Complete development environment
  max setup apps                  # Install GUI applications
  max coolify status              # Check Coolify instance status overview
  max coolify services            # List all services and their status
  max coolify applications        # List all applications and their status
        """
    )
    subparsers = parser.add_subparsers(
        title="Available Commands", 
        dest="command",
        description="Choose a command to run. Use 'max <command> --help' for detailed help on each command.",
        metavar="<command>"
    )
    parser.set_defaults(func=lambda _: parser.print_help())

    # Initialize configuration command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize or update personal configuration',
        description="""
Initialize MaxCLI with your personal configuration settings.

This is a one-time setup (or update) process that collects:
- Git username and email for repository configuration
- Dotfiles repository URL (optional)
- Google Cloud Platform project mappings (optional)

The configuration is saved to ~/.config/maxcli/config.json and used by
other commands to personalize their behavior.

After initialization, commands like 'max setup dev-full' will use your
personal git settings and dotfiles repository automatically.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max init                        # First-time setup or update existing config
  max init --force                # Force reconfiguration (skip confirmation)
        """
    )
    init_parser.add_argument('--force', action='store_true', help='Force reconfiguration without confirmation')
    init_parser.set_defaults(func=init_config)

    # Switch gcloud configuration command
    sc_parser = subparsers.add_parser(
        'switch-config', 
        help='Switch gcloud config and application default credentials',
        description="""
Switch to an existing gcloud configuration and its associated Application Default Credentials (ADC).

This command will:
1. Activate the specified gcloud configuration
2. Copy the saved ADC file for this configuration to the active ADC location
3. Set the appropriate quota project if a mapping exists

The configuration must have been previously created using 'max create-config' or manually set up
with a corresponding ADC file at ~/.config/gcloud/adc_<name>.json

INTERACTIVE MODE: If no configuration name is provided, you'll see an interactive menu
with arrow key navigation to select from available configurations.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max switch-config altekai       # Switch to 'altekai' configuration
  max switch-config               # Interactive mode - choose from menu
  max switch-config urbansharing  # Switch to 'urbansharing' configuration
        """
    )
    sc_parser.add_argument('name', nargs='?', help='Configuration name (optional - if not provided, shows interactive menu)')
    sc_parser.set_defaults(func=switch_config)

    # Create new gcloud configuration command
    cc_parser = subparsers.add_parser(
        'create-config', 
        help='Create new gcloud config with full authentication setup',
        description="""
Create a new gcloud configuration with complete authentication and ADC setup.

This command will guide you through:
1. Creating a new gcloud configuration
2. Authenticating with your Google account
3. Setting up Application Default Credentials (ADC)
4. Saving the ADC file for future switching
5. Configuring quota project (with smart mapping or manual input)

After completion, you can switch to this configuration using 'max switch-config <name>'.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max create-config myproject     # Create config named 'myproject'
  max create-config altekai       # Create config with existing quota mapping
        """
    )
    cc_parser.add_argument('name', help='Configuration name to create (required)')
    cc_parser.set_defaults(func=create_config)

    # List available configurations command
    lc_parser = subparsers.add_parser(
        'list-configs', 
        help='List all available gcloud configurations with ADC files',
        description="""
Display all gcloud configurations that have associated Application Default Credentials (ADC) files.

This shows configurations that can be used with 'max switch-config' command.
Only configurations with saved ADC files in ~/.config/gcloud/adc_*.json are listed.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max list-configs                # Show all available configurations
        """
    )
    lc_parser.set_defaults(func=list_configs)

    # Docker cleanup command
    dc_parser = subparsers.add_parser(
        'docker-clean', 
        help='Clean up Docker system (containers, images, volumes, networks)',
        description="""
Perform a comprehensive Docker system cleanup.

This command runs 'docker system prune -af' which removes:
- All stopped containers
- All networks not used by at least one container
- All dangling images
- All build cache
- All unused volumes

WARNING: This will remove ALL unused Docker resources. Make sure you don't need any
stopped containers or unused images before running this command.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max docker-clean                # Clean up Docker system
        """
    )
    dc_parser.set_defaults(func=docker_clean)

    # Gentle Docker cleanup command
    dt_parser = subparsers.add_parser(
        'docker-tidy', 
        help='Gentle Docker cleanup (removes only old/unused items)',
        description="""
Perform a conservative Docker cleanup that only removes truly unused items.

This safer alternative to 'docker-clean' removes:
- Containers stopped for more than 24 hours
- Dangling images only (untagged/unreferenced)
- Unused networks
- Build cache older than 7 days

This command preserves:
- All tagged images (even if not currently used)
- Recently stopped containers (stopped <24h ago)
- All volumes (never touches data)
- Recent build cache
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max docker-tidy                 # Safe Docker cleanup
  max docker-clean                # Aggressive cleanup (if needed)
        """
    )
    dt_parser.set_defaults(func=docker_tidy)

    # Kubernetes context switching command
    kctx_parser = subparsers.add_parser(
        'kctx', 
        help='Switch Kubernetes context',
        description="""
Switch the current Kubernetes context using kubectl.

This is equivalent to running 'kubectl config use-context <context>' but with a shorter command.
The context must already exist in your kubectl configuration.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max kctx minikube               # Switch to minikube context
  max kctx production-cluster     # Switch to production cluster context
  
To see available contexts, run: kubectl config get-contexts
        """
    )
    kctx_parser.add_argument('context', help='Kubernetes context name (required)')
    kctx_parser.set_defaults(func=kctx)

    # Database backup command
    bkp_parser = subparsers.add_parser(
        'backup-db', 
        help='Backup PostgreSQL database to timestamped file',
        description="""
Create a backup of the PostgreSQL database 'mydb' using pg_dump.

The backup file will be saved to ~/backups/db_<date>.sql where <date> is the current date
in YYYY-MM-DD format. The backup directory will be created if it doesn't exist.

Requirements:
- PostgreSQL client tools (pg_dump) must be installed
- Database 'mydb' must exist and be accessible
- User must have read permissions on the database
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max backup-db                   # Create backup file like ~/backups/db_2024-01-15.sql
        """
    )
    bkp_parser.set_defaults(func=backup_db)

    # Application deployment command
    deploy_parser = subparsers.add_parser(
        'deploy-app', 
        help='Deploy the application (placeholder command)',
        description="""
Deploy the application using predefined deployment logic.

NOTE: This is currently a placeholder command. The actual deployment logic
needs to be implemented based on your specific deployment requirements.

Typical deployment steps might include:
- Building the application
- Running tests
- Pushing to container registry
- Updating Kubernetes deployments
- Running post-deployment checks
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max deploy-app                  # Run deployment process
        """
    )
    deploy_parser.set_defaults(func=deploy_app)

    # Enable autocomplete if argcomplete is installed
    try:
        import argcomplete  # type: ignore # Optional dependency
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    # Add setup subcommands for laptop/dev environment setup
    add_setup_subcommands(subparsers)

    # Add Coolify subcommands
    add_coolify_subcommands(subparsers)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help() 