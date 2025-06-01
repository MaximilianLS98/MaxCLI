"""Coolify API management commands."""
import json
import sys
from typing import Dict, List, Optional, Any, Tuple
import subprocess
from ..config import get_config_value

def get_coolify_config() -> Tuple[Optional[str], Optional[str]]:
    """Get Coolify API key and instance URL from config."""
    api_key = get_config_value('coolify_api_key')
    instance_url = get_config_value('coolify_instance_url')
    
    if not api_key or not instance_url:
        print("❌ Coolify API key or instance URL not configured.")
        print("💡 Run 'max init' to configure Coolify settings.")
        return None, None
    
    # Ensure instance URL doesn't end with trailing slash
    instance_url = instance_url.rstrip('/')
    
    return api_key, instance_url

def make_coolify_request(endpoint: str, method: str = 'GET', data: Optional[Dict] = None, expect_json: bool = True) -> Optional[Any]:
    """Make a request to the Coolify API using curl."""
    api_key, instance_url = get_coolify_config()
    if not api_key or not instance_url:
        return None
    
    # Ensure endpoint starts with /api/v1
    if not endpoint.startswith('/api/v1'):
        if endpoint.startswith('/'):
            endpoint = f"/api/v1{endpoint}"
        else:
            endpoint = f"/api/v1/{endpoint}"
    
    url = f"{instance_url}{endpoint}"
    
    # Build curl command
    curl_cmd = [
        'curl', '-s', '-X', method,
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        '-H', 'Accept: application/json'
    ]
    
    # Add data for POST/PATCH requests
    if data and method in ['POST', 'PATCH']:
        curl_cmd.extend(['-d', json.dumps(data)])
    
    curl_cmd.append(url)
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            # Check if response looks like HTML (authentication redirect)
            if result.stdout.strip().startswith('<!DOCTYPE html>') or result.stdout.strip().startswith('<html'):
                print("❌ Authentication failed - received HTML redirect instead of JSON")
                print("💡 This usually means:")
                print("   • Your API key is invalid or expired")
                print("   • Your API key doesn't have sufficient permissions")
                print("   • The Coolify instance URL is incorrect")
                print("💡 Run 'max init' to update your Coolify credentials")
                return None
            
            # If we don't expect JSON, return the raw text
            if not expect_json:
                return result.stdout.strip()
            
            try:
                json_response = json.loads(result.stdout)
                
                # Check for permission errors
                if isinstance(json_response, dict) and 'message' in json_response:
                    message = json_response['message']
                    if 'permission' in message.lower() or 'unauthorized' in message.lower():
                        print(f"❌ Permission denied: {message}")
                        print("💡 Your API key may not have the required permissions for this operation")
                        print("💡 Check your API key permissions in the Coolify dashboard")
                        return None
                    elif 'not found' in message.lower():
                        print(f"❌ Endpoint not found: {message}")
                        print("💡 This endpoint may not be available in your Coolify version")
                        return None
                
                return json_response
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response from Coolify API")
                print(f"Response preview: {result.stdout[:200]}...")
                return None
        return {} if expect_json else ""
    except subprocess.CalledProcessError as e:
        print(f"❌ API request failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def format_status(status: str) -> str:
    """Format status with appropriate emoji and color."""
    status_lower = status.lower()
    
    # Handle composite statuses first (most specific)
    if 'running:unhealthy' in status_lower:
        return '🟢 Running (⚠️  health check failing)'
    elif 'running:healthy' in status_lower:
        return '🟢 Running'
    elif 'exited:unhealthy' in status_lower:
        return '🔴 Exited (stopped manually)'
    # Handle single-word statuses
    elif status_lower == 'running':
        return '🟢 Running'
    elif status_lower == 'stopped':
        return '🔴 Stopped'
    elif status_lower == 'starting':
        return '🟡 Starting'
    elif status_lower == 'stopping':
        return '🟡 Stopping'
    elif status_lower == 'restarting':
        return '🟡 Restarting'
    elif status_lower == 'exited':
        return '🔴 Exited'
    elif status_lower == 'healthy':
        return '🟢 Healthy'
    elif status_lower == 'unhealthy':
        return '🔴 Unhealthy'
    elif status_lower == 'reachable':
        return '🟢 Reachable'
    elif status_lower == 'unreachable':
        return '🔴 Unreachable'
    elif status_lower == 'unknown':
        return '⚪ Unknown'
    # Fallback for partial matches
    elif 'running' in status_lower:
        return f'🟢 Running ({status})'
    elif 'stopped' in status_lower:
        return f'🔴 Stopped ({status})'
    elif 'exited' in status_lower:
        return f'🔴 Exited ({status})'
    elif 'starting' in status_lower:
        return f'🟡 Starting ({status})'
    elif 'stopping' in status_lower:
        return f'🟡 Stopping ({status})'
    else:
        return f"⚪ {status}"

def coolify_health(args) -> None:
    """Check Coolify instance health."""
    print("🔍 Checking Coolify health...")
    
    response = make_coolify_request('/health', expect_json=False)
    if response is None:
        sys.exit(1)
    
    if response and response.lower() == 'ok':
        print("✅ Coolify instance is healthy!")
        print(f"Health status: {response}")
    elif response:
        print("⚠️  Coolify instance responded but with unexpected status:")
        print(f"Response: {response}")
    else:
        print("✅ Coolify instance is responding (empty response)")

def coolify_services(args) -> None:
    """List all services and their status."""
    print("🔍 Fetching services...")
    
    response = make_coolify_request('/services')
    if response is None:
        sys.exit(1)
    
    # Response is directly an array, not wrapped in 'data'
    if not response:
        print("📭 No services found")
        return
    
    if not isinstance(response, list):
        print("❌ Unexpected response format from services endpoint")
        print(f"Response preview: {str(response)[:200]}...")
        return
    
    services = response
    print(f"\n📊 Found {len(services)} service(s):")
    print("=" * 80)
    
    for service in services:
        name = service.get('name', 'Unknown')
        status = service.get('status', 'Unknown')
        uuid = service.get('uuid', 'N/A')
        # Extract server name from nested destination/server/name structure
        server_name = 'Unknown'
        destination = service.get('destination')
        if destination and isinstance(destination, dict):
            server = destination.get('server')
            if server and isinstance(server, dict):
                server_name = server.get('name', 'Unknown')
        
        print(f"📦 {name}")
        print(f"   Status: {format_status(status)}")
        print(f"   Server: {server_name}")
        print(f"   UUID: {uuid}")
        print("-" * 40)

def coolify_applications(args) -> None:
    """List all applications and their status."""
    print("🔍 Fetching applications...")
    
    response = make_coolify_request('/applications')
    if response is None:
        sys.exit(1)
    
    # Response is directly an array, not wrapped in 'data'
    if not response:
        print("📭 No applications found")
        return
    
    if not isinstance(response, list):
        print("❌ Unexpected response format from applications endpoint")
        print(f"Response preview: {str(response)[:200]}...")
        return
    
    applications = response
    print(f"\n📊 Found {len(applications)} application(s):")
    print("=" * 80)
    
    for app in applications:
        name = app.get('name', 'Unknown')
        status = app.get('status', 'Unknown')
        uuid = app.get('uuid', 'N/A')
        # Extract server name from nested destination/server/name structure
        server_name = 'Unknown'
        destination = app.get('destination')
        if destination and isinstance(destination, dict):
            server = destination.get('server')
            if server and isinstance(server, dict):
                server_name = server.get('name', 'Unknown')
        # This might cause issues if other people want to use my script and their coolify is not on hetzner
        if server_name == 'localhost':
            server_name = 'Hetzner'
        repository = app.get('git_repository', 'N/A')
        branch = app.get('git_branch', 'N/A')
        fqdn = app.get('fqdn', 'N/A')
        
        print(f"🚀 {name}")
        print(f"   Status: {format_status(status)}")
        print(f"   Server: {server_name}")
        print(f"   FQDN: {fqdn}")
        print(f"   Repository: {repository}")
        if branch and branch != 'N/A':
            print(f"   Branch: {branch}")
        print(f"   UUID: {uuid}")
        print("-" * 40)

def coolify_servers(args) -> None:
    """List all servers and their status."""
    print("🔍 Fetching servers...")
    
    response = make_coolify_request('/servers')
    if response is None:
        sys.exit(1)
    
    # Response is directly an array, not wrapped in 'data'
    if not response:
        print("📭 No servers found")
        return
    
    if not isinstance(response, list):
        print("❌ Unexpected response format from servers endpoint")
        print(f"Response preview: {str(response)[:200]}...")
        return
    
    servers = response
    print(f"\n📊 Found {len(servers)} server(s):")
    print("=" * 80)
    
    for server in servers:
        name = server.get('name', 'Unknown')
        ip = server.get('ip', 'N/A')
        # Check for reachability status - this might be in different places
        is_reachable = server.get('is_reachable', server.get('settings', {}).get('is_reachable', None))
        uuid = server.get('uuid', 'N/A')
        
        if is_reachable is not None:
            status_text = 'reachable' if is_reachable else 'unreachable'
        else:
            status_text = 'unknown'
        
        print(f"🖥️  {name}")
        print(f"   Status: {format_status(status_text)}")
        print(f"   IP: {ip}")
        print(f"   UUID: {uuid}")
        print("-" * 40)

def coolify_resources(args) -> None:
    """List all resources (combined view)."""
    print("🔍 Fetching all resources...")
    
    response = make_coolify_request('/resources')
    if response is None:
        sys.exit(1)
    
    # Response is directly an array, not wrapped in 'data'
    if not response:
        print("📭 No resources found")
        return
    
    if not isinstance(response, list):
        print("❌ Unexpected response format from resources endpoint")
        print(f"Response preview: {str(response)[:200]}...")
        return
    
    resources = response
    print(f"\n📊 Found {len(resources)} resource(s):")
    print("=" * 80)
    
    # Group resources by type
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for resource in resources:
        resource_type = resource.get('type', resource.get('resource_type', 'unknown'))
        if resource_type not in by_type:
            by_type[resource_type] = []
        by_type[resource_type].append(resource)
    
    for resource_type, items in by_type.items():
        print(f"\n📂 {resource_type.title()} ({len(items)})")
        print("-" * 60)
        
        for item in items:
            name = item.get('name', 'Unknown')
            status = item.get('status', 'Unknown')
            uuid = item.get('uuid', 'N/A')
            
            print(f"   📋 {name}")
            print(f"      Status: {format_status(status)}")
            print(f"      UUID: {uuid}")

def coolify_start_service(args) -> None:
    """Start a service by UUID."""
    if not args.uuid:
        print("❌ Service UUID is required")
        print("💡 Use 'max coolify services' to list available services and their UUIDs")
        sys.exit(1)
    
    print(f"🚀 Starting service {args.uuid}...")
    
    response = make_coolify_request(f'/services/{args.uuid}/start')
    if response is None:
        sys.exit(1)
    
    print("✅ Service start command sent successfully!")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")

def coolify_stop_service(args) -> None:
    """Stop a service by UUID."""
    if not args.uuid:
        print("❌ Service UUID is required")
        print("💡 Use 'max coolify services' to list available services and their UUIDs")
        sys.exit(1)
    
    print(f"🛑 Stopping service {args.uuid}...")
    
    response = make_coolify_request(f'/services/{args.uuid}/stop')
    if response is None:
        sys.exit(1)
    
    print("✅ Service stop command sent successfully!")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")

def coolify_restart_service(args) -> None:
    """Restart a service by UUID."""
    if not args.uuid:
        print("❌ Service UUID is required")
        print("💡 Use 'max coolify services' to list available services and their UUIDs")
        sys.exit(1)
    
    print(f"🔄 Restarting service {args.uuid}...")
    
    response = make_coolify_request(f'/services/{args.uuid}/restart')
    if response is None:
        sys.exit(1)
    
    print("✅ Service restart command sent successfully!")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")

def coolify_status(args) -> None:
    """Show overall Coolify status with summary of all resources."""
    print("🔍 Getting Coolify status overview...")
    
    # Check health first
    health_response = make_coolify_request('/health', expect_json=False)
    if health_response is None:
        print("❌ Could not connect to Coolify instance")
        sys.exit(1)
    
    if health_response and health_response.lower() == 'ok':
        print("✅ Coolify instance is healthy!")
    else:
        print("⚠️  Coolify instance status unclear")
        print(f"Health response: {health_response}")
    
    print("=" * 60)
    
    # Get summary of each resource type
    resource_types = [
        ('applications', '🚀 Applications'),
        ('services', '📦 Services'),
        ('servers', '🖥️  Servers'),
        ('databases', '🗄️  Databases')
    ]
    
    for endpoint, label in resource_types:
        response = make_coolify_request(f'/{endpoint}')
        if response and isinstance(response, list):
            resources = response
            count = len(resources)
            
            # Count by status
            running = sum(1 for r in resources if r.get('status', '').lower() in ['running', 'healthy'] or 'running:' in r.get('status', '').lower())
            stopped = sum(1 for r in resources if r.get('status', '').lower() in ['stopped', 'exited'] or 'exited:' in r.get('status', '').lower())
            other = count - running - stopped
            
            print(f"{label}: {count} total")
            if count > 0:
                print(f"   🟢 Running/Healthy: {running}")
                print(f"   🔴 Stopped/Exited: {stopped}")
                if other > 0:
                    print(f"   🟡 Other states: {other}")
            print()
        else:
            print(f"{label}: Unable to fetch")
            print()

def coolify_start_application(args) -> None:
    """Start an application by UUID."""
    if not args.uuid:
        print("❌ Application UUID is required")
        print("💡 Use 'max coolify applications' to list available applications and their UUIDs")
        sys.exit(1)
    
    print(f"🚀 Starting application {args.uuid}...")
    
    response = make_coolify_request(f'/applications/{args.uuid}/start')
    if response is None:
        sys.exit(1)
    
    print("✅ Application start command sent successfully!")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")

def coolify_stop_application(args) -> None:
    """Stop an application by UUID."""
    if not args.uuid:
        print("❌ Application UUID is required")
        print("💡 Use 'max coolify applications' to list available applications and their UUIDs")
        sys.exit(1)
    
    print(f"🛑 Stopping application {args.uuid}...")
    
    response = make_coolify_request(f'/applications/{args.uuid}/stop')
    if response is None:
        sys.exit(1)
    
    print("✅ Application stop command sent successfully!")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")

def coolify_restart_application(args) -> None:
    """Restart an application by UUID."""
    if not args.uuid:
        print("❌ Application UUID is required")
        print("💡 Use 'max coolify applications' to list available applications and their UUIDs")
        sys.exit(1)
    
    print(f"🔄 Restarting application {args.uuid}...")
    
    response = make_coolify_request(f'/applications/{args.uuid}/restart')
    if response is None:
        sys.exit(1)
    
    print("✅ Application restart command sent successfully!")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")

def coolify_deploy_application(args) -> None:
    """Deploy an application by UUID."""
    if not args.uuid:
        print("❌ Application UUID is required")
        print("💡 Use 'max coolify applications' to list available applications and their UUIDs")
        sys.exit(1)
    
    print(f"🚀 Deploying application {args.uuid}...")
    
    response = make_coolify_request(f'/applications/{args.uuid}/deploy')
    if response is None:
        sys.exit(1)
    
    print("✅ Application deployment started successfully!")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}") 