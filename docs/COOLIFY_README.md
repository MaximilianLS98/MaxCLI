# Coolify API Management

This document describes the Coolify API management functionality added to MaxCLI.

## Overview

The Coolify commands allow you to manage your Coolify instance through its REST API. You can monitor services, applications, servers, and perform lifecycle operations like starting, stopping, and deploying resources.

## Prerequisites

1. **Coolify Instance**: You need a running Coolify instance (self-hosted or Coolify Cloud)
2. **API Key**: Generate an API key from your Coolify instance dashboard
3. **API Permissions**: Ensure your API key has the required permissions:
    - `read` - For listing resources (applications, services, servers, etc.)
    - `deploy` - For deployment operations (optional, for deploy commands)
    - `manage` - For start/stop/restart operations (optional, for lifecycle commands)
    - `root` - Many commands require root permissions unfortunately, but test with other permissions first to see if it suits your needs
4. **Configuration**: Run `max init` to configure your API credentials and instance URL

## Configuration

During `max init`, you'll be prompted to configure:

- **Coolify API Key**: Your personal API token from Coolify
- **Coolify Instance URL**: The base URL of your Coolify instance (e.g., `https://coolify.example.com`, do not include `/api/v1` or `/api/v2` in the URL)

The configuration is stored in `~/.config/maxcli/config.json`.

**Note**: All API calls use the `/api/v1` endpoint structure automatically.

## Available Commands

### Health & Status

```bash
# Check instance health
max coolify health

# Overall status overview with resource counts
max coolify status
```

### Resource Listing

```bash
# List all services with status and server information
max coolify services

# List all applications with status and repository info
max coolify applications

# List all servers with reachability status
max coolify servers

# List all resources grouped by type (services, applications, etc.)
max coolify resources
```

### Service Management

```bash
# Start a service
max coolify start-service <service-uuid>

# Stop a service
max coolify stop-service <service-uuid>

# Restart a service
max coolify restart-service <service-uuid>
```

### Application Management

```bash
# Start an application
max coolify start-application <app-uuid>

# Stop an application
max coolify stop-application <app-uuid>

# Restart an application
max coolify restart-application <app-uuid>

# Deploy an application (pull latest code and redeploy)
max coolify deploy-application <app-uuid>
```

## Getting UUIDs

To get the UUIDs needed for management operations:

```bash
# For services
max coolify services

# For applications
max coolify applications
```

Each listing command shows the UUID that you can use for start/stop/restart operations.

## Status Indicators

The commands use visual indicators for status:

- 🟢 Running/Healthy
- 🟢 Running (⚠️ health check failing) - Application is running but health checks aren't configured or failing
- 🔴 Stopped/Exited/Unhealthy
- 🔴 Exited (stopped manually) - Application was manually stopped
- 🟡 Starting/Stopping/Restarting
- ⚪ Unknown/Other states

**Note**: "Running (health check failing)" typically indicates that your application is working fine, but Coolify's health check configuration needs attention. This is common when health check endpoints aren't configured in the Coolify dashboard.

## Authentication

All API calls use Bearer token authentication with the API key you configured. If authentication fails, you'll see helpful error messages guiding you to:

1. Check if your API key is valid
2. Verify the instance URL is correct
3. Ensure your API key has sufficient permissions

## Error Handling

The CLI provides clear error messages for common issues:

- **Authentication failures**: Detected when receiving HTML redirects instead of JSON
- **Network issues**: Connection problems or timeouts
- **Invalid responses**: Malformed JSON or unexpected response formats
- **Missing configuration**: Prompts to run `max init`

## Examples

### Quick Status Check

```bash
# Get overview of your entire infrastructure
max coolify status
```

### Managing a Service

```bash
# List services to find UUID
max coolify services

# Restart a specific service
max coolify restart-service abc123-def456
```

### Application Deployment

```bash
# List applications to find UUID and see which server they're on
max coolify applications

# Example output:
# 🚀 My Web App
#    Status: 🟢 Running
#    Server: production-server-1
#    FQDN: myapp.example.com
#    Repository: github.com/user/myapp
#    Branch: main
#    UUID: abc123-def456-ghi789

# Deploy latest changes
max coolify deploy-application xyz789-abc123-def456
```

## API Compatibility

This implementation is based on the Coolify v4 REST API. The commands use standard HTTP methods:

- `GET` for listing and status operations
- `POST` for start/deploy operations
- Other methods as appropriate for lifecycle operations

For the most up-to-date API documentation, visit: https://coolify.io/docs/api-reference

## Troubleshooting

### Common Issues

1. **Authentication Error**:

    - Verify your API key is correct and active
    - Check that the instance URL doesn't have a trailing slash
    - Ensure your API key has the required permissions

2. **Connection Issues**:

    - Verify your Coolify instance is accessible
    - Check network connectivity
    - Confirm the instance URL is correct

3. **Permission Denied**:
    - Your API key may not have sufficient permissions
    - Contact your Coolify administrator for proper access

### Getting Help

```bash
# General help
max coolify --help

# Help for specific commands
max coolify services --help
max coolify start-service --help
```

## Implementation Details

- **HTTP Client**: Uses `curl` via subprocess for reliability and transparency
- **Authentication**: Bearer token in Authorization header
- **Content Type**: JSON for both requests and responses
- **Error Handling**: Comprehensive error detection and user-friendly messages
- **Status Formatting**: Visual indicators with emojis for better UX

The implementation follows functional programming principles and provides well-structured, commented code that's easy to maintain and extend.
