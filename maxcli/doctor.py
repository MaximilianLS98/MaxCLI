"""Read-only diagnostics; external network probes require --network."""
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.parse

from .installation import current_installation, version_info, release_info, InstallError
from .modules.module_manager import AVAILABLE_MODULES, DEFAULT_ENABLED_MODULES
from .paths import config_dir
from .storage import read_object
from .runtime import CommandError


def inspect_environment(all_modules=False, network=False):
    checks = []
    contexts = {}
    modules = []
    directory = config_dir()

    def check(name, status, message, fix=None):
        checks.append({'name': name, 'status': status, 'message': message, 'fix': fix})

    check('python', 'ok' if sys.version_info >= (3, 10) else 'error', platform.python_version(), 'Use Python 3.10 or newer')
    try:
        installation = version_info()
        managed = current_installation()
        check('installation', 'ok' if managed else 'warning', installation['channel'],
              None if managed else 'Run bootstrap.sh --dev for a live checkout or bootstrap.sh for stable')
        if managed:
            command_name = 'max-dev' if managed['channel'] == 'development' else 'max'
            selected = shutil.which(command_name)
            expected = Path(managed['bin_dir']) / command_name
            correct = selected is not None and Path(selected).resolve() == expected.resolve()
            check('launcher', 'ok' if correct else 'warning', selected or '{} is not on PATH'.format(command_name),
                  None if correct else 'Put {} first on PATH'.format(expected.parent))
    except InstallError as exc:
        installation = {'channel': 'unknown'}
        check('installation', 'error', str(exc), 'Reinstall the affected channel')

    configuration = {}
    module_config = {}
    for filename in ('config.json', 'modules_config.json', 'ssh_targets.json', 'projects.json'):
        path = directory / filename
        try:
            data = read_object(path)
            if filename == 'config.json':
                configuration = data
            if filename == 'modules_config.json':
                module_config = data
            if filename == 'ssh_targets.json':
                for name, target in data.items():
                    valid = isinstance(target, dict) and all(isinstance(target.get(key), str) and target[key]
                                                           for key in ('host', 'user', 'key'))
                    if not valid:
                        check('ssh:' + name, 'error', 'Invalid SSH profile', 'Repair {}'.format(path))
                    else:
                        present = Path(target['key']).expanduser().is_file()
                        check('ssh:' + name, 'ok' if present else 'warning',
                              'Key file exists' if present else 'Configured SSH key file is missing',
                              None if present else 'Update the SSH target key path or restore the key')
            if filename == 'projects.json':
                for name, project in data.items():
                    valid = isinstance(project, dict) and isinstance(project.get('path'), str)
                    present = valid and Path(project['path']).is_dir()
                    check('project:' + name, 'ok' if present else 'warning',
                          'Directory exists' if present else 'Registered directory is missing or invalid',
                          None if present else 'Re-register the project or remove its stale registration')
            if path.exists():
                private = path.stat().st_mode & 0o077 == 0
                check(filename, 'ok' if private else 'warning', 'Valid JSON; owner-only' if private else 'Readable by other users',
                      None if private else 'Set owner-only permissions (chmod 600) on {}'.format(path))
            else:
                check(filename, 'info', 'Not created yet')
        except CommandError as exc:
            check(filename, 'error', str(exc), 'Repair the JSON file; doctor has not changed it')
    if directory.exists():
        private = directory.stat().st_mode & 0o077 == 0
        check('config-directory', 'ok' if private else 'warning', str(directory),
              None if private else 'Set owner-only permissions (chmod 700) on {}'.format(directory))
    else:
        check('config-directory', 'info', 'Not created yet: {}'.format(directory), 'Run max config init when ready')

    enabled = module_config.get('enabled_modules', DEFAULT_ENABLED_MODULES)
    if not isinstance(enabled, list) or any(not isinstance(name, str) for name in enabled):
        check('enabled-modules', 'error', 'enabled_modules must be a list of names', 'Repair modules_config.json')
        enabled = []
    info = module_config.get('module_info', {})
    if not isinstance(info, dict) or any(not isinstance(value, dict) for value in info.values()):
        check('module-info', 'error', 'module_info must map names to objects', 'Repair modules_config.json')
    for name in enabled:
        if name not in AVAILABLE_MODULES:
            check('module:' + name, 'error', 'Unknown module', 'Remove this stale module name from configuration')
    for name, metadata in AVAILABLE_MODULES.items():
        active = name in enabled
        if not active and not all_modules:
            continue
        required = metadata.get('dependencies', [])
        optional = metadata.get('optional_dependencies', [])
        missing = [tool for tool in required if not shutil.which(tool)]
        optional_missing = [tool for tool in optional if not shutil.which(tool)]
        available = importlib.util.find_spec('maxcli.modules.' + name) is not None
        ready = available and not missing
        modules.append({'name': name, 'enabled': active, 'ready': ready,
                        'missing_required': missing, 'missing_optional': optional_missing})
        check('module:' + name, 'ok' if ready else 'error' if active else 'warning',
              'Ready' if ready else 'Missing: ' + ', '.join(missing or ['module implementation']),
              None if ready else 'Install {} or disable {}'.format(', '.join(missing) or 'the module', name))
        if optional_missing:
            check('optional:' + name, 'warning', 'Optional tools missing: ' + ', '.join(optional_missing),
                  'Install these tools to use the corresponding backup/setup features')

    api_key = os.environ.get('MAXCLI_COOLIFY_API_KEY') or configuration.get('coolify_api_key')
    instance_url = os.environ.get('MAXCLI_COOLIFY_URL') or configuration.get('coolify_instance_url')
    if 'coolify_manager' in enabled:
        valid_url = False
        if isinstance(instance_url, str):
            try:
                url = urllib.parse.urlsplit(instance_url)
                valid_url = url.scheme in ('http', 'https') and bool(url.hostname) and not url.username and not url.password
            except ValueError:
                pass
        configured = bool(api_key) and valid_url
        check('coolify-config', 'ok' if configured else 'error',
              'Credentials and URL configured (values hidden)' if configured else 'Missing credentials or invalid URL',
              None if configured else 'Set MAXCLI_COOLIFY_API_KEY and MAXCLI_COOLIFY_URL, or run max config init')
        for module in modules:
            if module['name'] == 'coolify_manager':
                module['ready'] = module['ready'] and configured

    local_contexts = (
        ('gcp_manager', 'gcp', ['gcloud', 'config', 'configurations', 'list', '--filter=is_active:true', '--format=value(name)']),
        ('kubernetes_manager', 'kubernetes', ['kubectl', 'config', 'current-context']),
        ('docker_manager', 'docker', ['docker', 'context', 'show']),
    )
    for module_name, label, command in local_contexts:
        if module_name not in enabled or not shutil.which(command[0]):
            continue
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            contexts[label] = result.stdout.strip() if result.returncode == 0 else None
            if result.returncode != 0:
                check('context:' + label, 'warning', 'Cannot read local active context', 'Configure {} and retry'.format(label))
        except (OSError, subprocess.TimeoutExpired):
            contexts[label] = None
            check('context:' + label, 'warning', 'Local context query failed or timed out')

    if network:
        try:
            release = release_info()
            check('network:github', 'ok', 'Latest stable release: ' + release['tag_name'])
        except InstallError as exc:
            check('network:github', 'error', str(exc), 'Check connectivity and GitHub API availability')
        if 'coolify_manager' in enabled and api_key and instance_url:
            from .commands.coolify import make_coolify_request
            try:
                response = make_coolify_request('/health', expect_json=False)
                healthy = isinstance(response, str) and response.strip().lower() == 'ok'
                check('network:coolify', 'ok' if healthy else 'error', 'Healthy' if healthy else 'Health check failed')
            except (CommandError, ValueError):
                check('network:coolify', 'error', 'Invalid endpoint or health response')
    return {'config_dir': str(directory), 'installation': installation, 'checks': checks,
            'modules': modules, 'contexts': contexts, 'network_checked': network,
            'ok': not any(item['status'] == 'error' for item in checks)}


def doctor(args):
    report = inspect_environment(args.all_modules, args.network)
    if args.json:
        print(json.dumps(report))
    else:
        print('MaxCLI doctor — {} — {}'.format(report['installation']['channel'], report['config_dir']))
        for item in report['checks']:
            print('[{}] {}: {}'.format(item['status'], item['name'], item['message']))
            if item['fix'] and item['status'] != 'ok':
                print('  Fix: ' + item['fix'])
        for name, value in report['contexts'].items():
            print('{} context: {}'.format(name, value or 'unknown'))
        if not args.network:
            print('Network checks skipped. Use --network to probe GitHub/Coolify.')
    return 0 if report['ok'] else 1


def register_commands(subparsers):
    parser = subparsers.add_parser('doctor', help='Inspect configuration, dependencies, and active contexts without making changes')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--network', action='store_true', help='Also probe GitHub and configured Coolify health')
    parser.add_argument('--all-modules', action='store_true', help='Include disabled modules in readiness checks')
    parser.set_defaults(func=doctor)
