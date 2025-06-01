"""
Coolify Manager Module for MaxCLI.

This module provides Coolify instance management functionality including:
- Health monitoring and status overview
- Services, applications, and databases management  
- Server monitoring and resource viewing
- Service lifecycle operations (start/stop/restart)
"""

import argparse
from maxcli.commands.coolify import (
    coolify_health, coolify_services, coolify_applications, coolify_servers,
    coolify_resources, coolify_start_service, coolify_stop_service,
    coolify_restart_service, coolify_status, coolify_start_application,
    coolify_stop_application, coolify_restart_application, coolify_deploy_application
)


def register_commands(subparsers) -> None:
    """Register Coolify management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Coolify management command group
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
  max coolify health              # Check instance health
        """
    )
    health_parser.set_defaults(func=coolify_health)

    # Status overview command
    status_parser = coolify_subparsers.add_parser(
        'status', 
        help='Show overall Coolify status overview',
        description="""
Display a comprehensive status overview of your Coolify instance.

This provides a summary view including:
- Instance health status
- Number of running services and applications
- Server status and resource usage
- Recent activity and alerts

This is the default command when running 'max coolify' without arguments.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify status              # Show status overview
        """
    )
    status_parser.set_defaults(func=coolify_status)

    # Services management
    services_parser = coolify_subparsers.add_parser(
        'services', 
        help='List and manage Coolify services',
        description="""
List all services managed by your Coolify instance.

Shows detailed information about each service including:
- Service name and type
- Current running status
- Resource usage
- Service UUID for management operations

Use the service UUID with start-service, stop-service, or restart-service commands.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify services            # List all services
  max coolify start-service <uuid>  # Start specific service
        """
    )
    services_parser.set_defaults(func=coolify_services)

    # Applications management
    applications_parser = coolify_subparsers.add_parser(
        'applications', 
        help='List and manage Coolify applications',
        description="""
List all applications deployed through your Coolify instance.

Shows detailed information about each application including:
- Application name and repository
- Current deployment status
- Build and deployment history
- Application UUID for management operations

Use the application UUID with start-application, stop-application, 
restart-application, or deploy-application commands.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max coolify applications        # List all applications
  max coolify deploy-application <uuid>  # Deploy specific application
        """
    )
    applications_parser.set_defaults(func=coolify_applications)

    # Servers monitoring
    servers_parser = coolify_subparsers.add_parser(
        'servers', 
        help='List and monitor Coolify servers',
        description="""
List all servers managed by your Coolify instance.

Shows detailed information about each server including:
- Server name and hostname
- System resource usage (CPU, memory, disk)
- Connection status
- Running services count

This helps monitor your infrastructure health and capacity.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify servers             # List all servers
        """
    )
    servers_parser.set_defaults(func=coolify_servers)

    # Resources overview
    resources_parser = coolify_subparsers.add_parser(
        'resources', 
        help='Show all Coolify resources overview',
        description="""
Display a comprehensive overview of all resources in your Coolify instance.

This provides a unified view of:
- All services and their status
- All applications and their deployment status
- All servers and their resource usage
- Summary statistics

Useful for getting a complete picture of your Coolify infrastructure.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify resources           # Show resources overview
        """
    )
    resources_parser.set_defaults(func=coolify_resources)

    # Service lifecycle operations
    start_service_parser = coolify_subparsers.add_parser(
        'start-service', 
        help='Start a Coolify service',
        description="""
Start a specific Coolify service by its UUID.

Use 'max coolify services' to get the UUID of the service you want to start.
The service must be in a stopped state to be started.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify start-service abc123-def456-789  # Start service with UUID
        """
    )
    start_service_parser.add_argument('uuid', help='Service UUID to start')
    start_service_parser.set_defaults(func=coolify_start_service)

    stop_service_parser = coolify_subparsers.add_parser(
        'stop-service', 
        help='Stop a Coolify service',
        description="""
Stop a specific Coolify service by its UUID.

Use 'max coolify services' to get the UUID of the service you want to stop.
The service must be in a running state to be stopped.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify stop-service abc123-def456-789  # Stop service with UUID
        """
    )
    stop_service_parser.add_argument('uuid', help='Service UUID to stop')
    stop_service_parser.set_defaults(func=coolify_stop_service)

    restart_service_parser = coolify_subparsers.add_parser(
        'restart-service', 
        help='Restart a Coolify service',
        description="""
Restart a specific Coolify service by its UUID.

Use 'max coolify services' to get the UUID of the service you want to restart.
This will stop and then start the service, useful for applying configuration changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify restart-service abc123-def456-789  # Restart service with UUID
        """
    )
    restart_service_parser.add_argument('uuid', help='Service UUID to restart')
    restart_service_parser.set_defaults(func=coolify_restart_service)

    # Application lifecycle operations
    start_app_parser = coolify_subparsers.add_parser(
        'start-application', 
        help='Start a Coolify application',
        description="""
Start a specific Coolify application by its UUID.

Use 'max coolify applications' to get the UUID of the application you want to start.
The application must be in a stopped state to be started.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify start-application abc123-def456-789  # Start application with UUID
        """
    )
    start_app_parser.add_argument('uuid', help='Application UUID to start')
    start_app_parser.set_defaults(func=coolify_start_application)

    stop_app_parser = coolify_subparsers.add_parser(
        'stop-application', 
        help='Stop a Coolify application',
        description="""
Stop a specific Coolify application by its UUID.

Use 'max coolify applications' to get the UUID of the application you want to stop.
The application must be in a running state to be stopped.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify stop-application abc123-def456-789  # Stop application with UUID
        """
    )
    stop_app_parser.add_argument('uuid', help='Application UUID to stop')
    stop_app_parser.set_defaults(func=coolify_stop_application)

    restart_app_parser = coolify_subparsers.add_parser(
        'restart-application', 
        help='Restart a Coolify application',
        description="""
Restart a specific Coolify application by its UUID.

Use 'max coolify applications' to get the UUID of the application you want to restart.
This will stop and then start the application.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify restart-application abc123-def456-789  # Restart application with UUID
        """
    )
    restart_app_parser.add_argument('uuid', help='Application UUID to restart')
    restart_app_parser.set_defaults(func=coolify_restart_application)

    deploy_app_parser = coolify_subparsers.add_parser(
        'deploy-application', 
        help='Deploy a Coolify application',
        description="""
Deploy a specific Coolify application by its UUID.

Use 'max coolify applications' to get the UUID of the application you want to deploy.
This will trigger a new deployment of the application from its configured source.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max coolify deploy-application abc123-def456-789  # Deploy application with UUID
        """
    )
    deploy_app_parser.add_argument('uuid', help='Application UUID to deploy')
    deploy_app_parser.set_defaults(func=coolify_deploy_application) 