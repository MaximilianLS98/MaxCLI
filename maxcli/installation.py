"""Standalone installer and channel launcher. Uses only the Python standard library.

Can be downloaded and executed directly, or imported by an installed MaxCLI.
Each environment contains its own copy, so code and launcher switch together.
"""
import argparse
import contextlib
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
import venv

REPOSITORY = 'MaximilianLS98/MaxCLI'
MARKER = '# MaxCLI managed launcher v2'
METADATA = 'maxcli-install.json'


class InstallError(Exception):
    pass


def install_root():
    return Path(os.environ.get('MAXCLI_INSTALL_ROOT', str(Path.home() / '.local/share/maxcli'))).expanduser().resolve()


def atomic_text(path, content, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextlib.contextmanager
def installation_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.install.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InstallError('Another MaxCLI installation/update is running') from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def release_info(repository=REPOSITORY, version=None):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise InstallError('Repository must be OWNER/REPO')
    suffix = 'tags/' + urllib.parse.quote(version, safe='') if version else 'latest'
    url = 'https://api.github.com/repos/{}/releases/{}'.format(repository, suffix)
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'MaxCLI-installer'}
    token = os.environ.get('MAXCLI_GITHUB_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            release = json.load(response)
    except (OSError, ValueError) as exc:
        raise InstallError('Cannot resolve a published GitHub release: {}'.format(exc)) from exc
    if not isinstance(release, dict) or release.get('draft') or release.get('prerelease') or not release.get('tag_name'):
        raise InstallError('A published stable GitHub release is required')
    return release


def pointer_target(root, channel):
    pointer = root / channel
    if pointer.exists() and not pointer.is_symlink():
        raise InstallError('{} is not a managed channel symlink'.format(pointer))
    if not pointer.is_symlink():
        return None
    target = pointer.resolve()
    if target.parent != (root / 'envs').resolve() or not (target / METADATA).is_file():
        raise InstallError('Invalid managed environment: {}'.format(target))
    return target


def replace_pointer(pointer, target):
    temporary = pointer.with_name('.' + pointer.name + '-' + uuid.uuid4().hex)
    try:
        temporary.symlink_to(target, target_is_directory=True)
        os.replace(temporary, pointer)
    finally:
        if temporary.is_symlink():
            temporary.unlink()


def launcher_text(root, channel):
    pointer = root / channel
    return '#!/bin/sh\n{}\nexec {} -I {} launch "$@"\n'.format(
        MARKER, shlex.quote(str(pointer / 'bin/python')), shlex.quote(str(pointer / 'maxcli-manager.py')))


def build_environment(destination, source, editable=False, with_dev_tools=False):
    venv.EnvBuilder(with_pip=True, symlinks=True).create(str(destination))
    python = str(destination / 'bin/python')
    command = [python, '-I', '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input']
    if editable:
        command.append('--editable')
        if with_dev_tools:
            source += '[test]'
    subprocess.run(command + [source], check=True, timeout=600)
    with tempfile.TemporaryDirectory(prefix='maxcli-install-check-') as home:
        # Old releases may not understand MAXCLI_CONFIG_DIR yet.
        env = dict(os.environ, HOME=home, MAXCLI_CONFIG_DIR=home + '/config')
        subprocess.run([python, '-I', '-c', 'from maxcli.cli import main; main()', '--help'],
                       cwd=home, env=env, check=True, stdout=subprocess.DEVNULL, timeout=30)


def install(channel='stable', source=None, version=None, repository=REPOSITORY,
            root=None, bin_dir=None, replace_existing=False, with_dev_tools=False):
    if sys.version_info < (3, 10):
        raise InstallError('Python 3.10 or newer is required')
    if channel not in ('stable', 'development'):
        raise InstallError('Unknown channel')
    root = Path(root or install_root()).expanduser().resolve()
    bin_dir = Path(bin_dir or Path.home() / '.local/bin').expanduser().resolve()
    command_name = 'max' if channel == 'stable' else 'max-dev'
    launcher = bin_dir / command_name
    with installation_lock(root):
        if launcher.exists() or launcher.is_symlink():
            managed = launcher.is_file() and MARKER in launcher.read_text(errors='replace')
            if not managed and not replace_existing:
                raise InstallError('{} already exists. Use --replace-existing to back it up and replace it.'.format(launcher))
        previous = pointer_target(root, channel)
        if channel == 'stable':
            release = release_info(repository, version)
            version = release['tag_name']
            source = 'https://github.com/{}/archive/refs/tags/{}.tar.gz'.format(repository, urllib.parse.quote(version, safe=''))
        else:
            checkout = Path(source or '.').expanduser().resolve()
            if not (checkout / 'pyproject.toml').is_file() or not (checkout / 'maxcli/cli.py').is_file():
                raise InstallError('Development source must be a MaxCLI checkout')
            source = str(checkout)
            version = 'editable'
        destination = root / 'envs' / (channel + '-' + uuid.uuid4().hex)
        metadata = {'channel': channel, 'version': version, 'source': source,
                    'repository': repository, 'root': str(root), 'bin_dir': str(bin_dir)}
        try:
            print('Installing {} from {}'.format(channel, source), flush=True)
            build_environment(destination, source, channel == 'development', with_dev_tools)
            atomic_text(destination / METADATA, json.dumps(metadata, indent=2))
            atomic_text(destination / 'maxcli-manager.py', Path(__file__).read_text())
            if launcher.exists() and MARKER not in launcher.read_text(errors='replace'):
                backup = launcher.with_name(launcher.name + '.backup-' + uuid.uuid4().hex[:8])
                shutil.copy2(launcher, backup)
                print('Previous launcher backed up to {}'.format(backup))
            # The launcher always references the channel pointer. Existing invocations
            # continue on their original interpreter while activation is atomic.
            atomic_text(launcher, launcher_text(root, channel), 0o755)
            if previous:
                replace_pointer(root / (channel + '-previous'), previous)
            replace_pointer(root / channel, destination)
        except BaseException:
            # Never delete an environment that was successfully activated.
            if not (root / channel).is_symlink() or (root / channel).resolve() != destination:
                shutil.rmtree(destination, ignore_errors=True)
            raise
    print('Ready: {}'.format(launcher))
    print('Ensure {} is before older MaxCLI installations on PATH.'.format(bin_dir))
    if channel == 'development':
        print('Source edits are live on the next max-dev invocation. Reinstall after dependency/metadata changes.')
    return metadata


def current_installation():
    path = Path(sys.prefix) / METADATA
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        raise InstallError('Cannot read installation metadata: {}'.format(exc)) from exc
    if (not isinstance(data, dict) or data.get('channel') not in ('stable', 'development')
            or any(not isinstance(data.get(key), str) or not data[key]
                   for key in ('root', 'bin_dir', 'repository', 'source', 'version'))):
        raise InstallError('Invalid installation metadata')
    return data


def version_info():
    info = current_installation()
    try:
        package_version = importlib.metadata.version('maxcli')
    except importlib.metadata.PackageNotFoundError:
        package_version = 'uninstalled checkout'
    result = {'package_version': package_version, 'channel': info['channel'] if info else 'unmanaged',
              'release': info.get('version') if info else None,
              'source': info.get('source') if info else None, 'python': sys.executable}
    return result


def display_version(args):
    data = version_info()
    if getattr(args, 'json', False):
        print(json.dumps(data))
    else:
        print('MaxCLI {} ({})'.format(data['release'] or data['package_version'], data['channel']))
        if data['source']:
            print('Source: {}'.format(data['source']))
        print('Python: {}'.format(data['python']))


def rollback(root, channel):
    with installation_lock(root):
        current = pointer_target(root, channel)
        previous = pointer_target(root, channel + '-previous')
        if not current or not previous:
            raise InstallError('No previous environment is available')
        subprocess.run([str(previous / 'bin/python'), '-I', '-c', 'from maxcli.cli import main'], check=True, timeout=20)
        replace_pointer(root / channel, previous)
        replace_pointer(root / (channel + '-previous'), current)
    print('Restored previous {} environment'.format(channel))


def update(args):
    info = current_installation()
    if not info:
        raise InstallError('This installation is unmanaged. Use bootstrap.sh for stable or bootstrap.sh --dev for development.')
    if info['channel'] == 'development':
        raise InstallError('Development uses your live checkout. Edit source directly; rerun bootstrap.sh --dev to refresh dependencies.')
    if getattr(args, 'rollback', False):
        if getattr(args, 'check_only', False) or getattr(args, 'version', None) or getattr(args, 'show_releases', False):
            raise InstallError('--rollback cannot be combined with check-only, version, or release-note options')
        rollback(Path(info['root']), 'stable')
        return
    release = release_info(info['repository'], getattr(args, 'version', None))
    print('Installed: {} | GitHub release: {}'.format(info['version'], release['tag_name']))
    if getattr(args, 'show_releases', False):
        print(release.get('body') or 'No release notes.')
    if getattr(args, 'check_only', False) or release['tag_name'] == info['version']:
        return
    install('stable', version=release['tag_name'], repository=info['repository'], root=info['root'], bin_dir=info['bin_dir'])


def uninstall(args):
    info = current_installation()
    if not info:
        raise InstallError('Unmanaged installation: remove it with the package manager that installed it. Configuration is preserved.')
    root = Path(info['root'])
    channel = info['channel']
    launcher = Path(info['bin_dir']) / ('max' if channel == 'stable' else 'max-dev')
    print('Remove launcher {} and deactivate {}. Configuration and environments are preserved.'.format(launcher, channel))
    if getattr(args, 'dry_run', False):
        return
    if not getattr(args, 'force', False):
        if getattr(args, 'non_interactive', False) or not sys.stdin.isatty() or input('Continue? [y/N]: ').strip().lower() not in ('y', 'yes'):
            raise InstallError('Uninstall cancelled. Use --force for unattended deactivation.')
    with installation_lock(root):
        pointer_target(root, channel)  # Validate ownership before removing a pointer.
        if launcher.is_file() and launcher.read_text() == launcher_text(root, channel):
            launcher.unlink()
        else:
            raise InstallError('Launcher changed; refusing to remove it')
        (root / channel).unlink()
    print('Channel deactivated. Reinstall to reactivate; backups and user files are untouched.')


def add_update_arguments(parser):
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--show-releases', action='store_true')
    parser.add_argument('--version', help='Install a specific published stable release')
    parser.add_argument('--rollback', action='store_true', help='Activate the previous stable environment')


def launch(arguments):
    info = current_installation()
    if info is None:
        raise InstallError('Managed launcher has no installation metadata')
    os.environ['MAXCLI_CHANNEL'] = info['channel']
    os.environ['MAXCLI_INSTALL_ROOT'] = info['root']
    if info['channel'] == 'development':
        base = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
        os.environ.setdefault('MAXCLI_CONFIG_DIR', str(base / 'maxcli-dev'))
    # Lifecycle operations are managed here even for releases predating v2.
    if arguments[:1] in (['--version'], ['-v']):
        parser = argparse.ArgumentParser(prog='max --version')
        parser.add_argument('--json', action='store_true')
        display_version(parser.parse_args(arguments[1:]))
    elif arguments[:1] == ['update']:
        parser = argparse.ArgumentParser(prog='max update')
        add_update_arguments(parser)
        update(parser.parse_args(arguments[1:]))
    elif arguments[:1] == ['uninstall']:
        parser = argparse.ArgumentParser(prog='max uninstall')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        uninstall(parser.parse_args(arguments[1:]))
    else:
        from maxcli.cli import main
        sys.argv = ['max-dev' if info['channel'] == 'development' else 'max', *arguments]
        main()


def main():
    try:
        if sys.argv[1:2] == ['launch']:
            launch(sys.argv[2:])
            return
        parser = argparse.ArgumentParser(description='Install a GitHub release as max, or a live checkout as max-dev.')
        parser.add_argument('--dev', nargs='?', const='.', metavar='CHECKOUT')
        parser.add_argument('--version', help='Published stable GitHub tag; defaults to latest release')
        parser.add_argument('--github-repo', default=REPOSITORY)
        parser.add_argument('--root', type=Path)
        parser.add_argument('--bin-dir', type=Path)
        parser.add_argument('--replace-existing', action='store_true')
        parser.add_argument('--with-dev-tools', action='store_true', help='Install the test extra in the development environment')
        args = parser.parse_args()
        if args.dev is not None and args.version:
            parser.error('--dev and --version are mutually exclusive')
        if args.with_dev_tools and args.dev is None:
            parser.error('--with-dev-tools requires --dev')
        install('development' if args.dev is not None else 'stable', source=args.dev,
                version=args.version, repository=args.github_repo, root=args.root, bin_dir=args.bin_dir,
                replace_existing=args.replace_existing, with_dev_tools=args.with_dev_tools)
    except (InstallError, OSError, subprocess.SubprocessError) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            print('Installation command failed (exit {}). Active installation was preserved.'.format(exc.returncode), file=sys.stderr)
        else:
            print('Error: {}'.format(exc), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('Installation cancelled.', file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
