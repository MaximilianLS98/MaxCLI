"""Configuration archive staging, bounded extraction and recoverable restore."""
import contextlib
from datetime import datetime
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
import uuid

from .runtime import CommandError
from .secrets import redact
from .storage import read_object, write_object

FILES = ('config.json', 'modules_config.json', 'ssh_targets.json', 'projects.json')
LIMIT = 64 * 1024 * 1024


def create_backup(config, destination=None, recipient=None):
    config = Path(config)
    if not config.is_dir():
        raise CommandError('Configuration directory does not exist')
    destination = Path(destination).expanduser() if destination else Path.home() / 'backups'
    destination.mkdir(parents=True, exist_ok=True)
    name = 'maxcli_backup_{}-{}.tar.gz'.format(datetime.now().strftime('%Y%m%d_%H%M%S'), uuid.uuid4().hex[:8])
    target = destination / (name + '.gpg' if recipient else name)
    with tempfile.TemporaryDirectory(prefix='.maxcli-backup-', dir=str(destination)) as stage:
        archive = Path(stage) / name
        with tarfile.open(archive, 'w:gz') as tar:
            for filename in FILES:
                path = config / filename
                if path.is_symlink():
                    raise CommandError('Refusing to back up configuration symlink: {}'.format(path))
                if not path.is_file():
                    continue
                data = read_object(path)
                if not recipient:
                    data = redact(data, omit=True)
                    # Arbitrary project commands/environment values may contain inline secrets.
                    if filename == 'projects.json':
                        data = {key: {field: value for field, value in entry.items() if field in ('path', 'tags')}
                                for key, entry in data.items() if isinstance(entry, dict)}
                payload = json.dumps(data, indent=2).encode()
                member = tarfile.TarInfo('maxcli/' + filename)
                member.size = len(payload)
                member.mode = 0o600
                tar.addfile(member, io.BytesIO(payload))
        archive.chmod(0o600)
        if recipient:
            encrypted = Path(stage) / (name + '.gpg')
            subprocess.run(['gpg', '--batch', '--yes', '--output', str(encrypted), '--encrypt',
                            '--recipient', recipient, str(archive)], check=True, timeout=60)
            encrypted.chmod(0o600)
            os.replace(encrypted, target)
        else:
            os.replace(archive, target)
    return target


@contextlib.contextmanager
def extracted_backup(path):
    path = Path(path).expanduser()
    if not path.is_file():
        raise CommandError('Backup file does not exist: {}'.format(path))
    with tempfile.TemporaryDirectory(prefix='maxcli-restore-') as temporary:
        stage = Path(temporary)
        archive = path
        if path.suffix == '.gpg':
            archive = stage / 'decrypted.tar.gz'
            subprocess.run(['gpg', '--batch', '--yes', '--output', str(archive), '--decrypt', str(path)],
                           check=True, timeout=60)
        output = stage / 'payload'
        output.mkdir(mode=0o700)
        try:
            with tarfile.open(archive, 'r:gz') as tar:
                total = 0
                seen = set()
                count = 0
                for member in tar:
                    count += 1
                    pure = PurePosixPath(member.name)
                    if (pure.is_absolute() or '..' in pure.parts or not pure.parts
                            or pure.parts[0] != 'maxcli' or member.issym() or member.islnk()
                            or not (member.isdir() or member.isfile())):
                        raise CommandError('Unsafe archive member: {}'.format(member.name))
                    total += member.size
                    if total > LIMIT or count > 100:
                        raise CommandError('Configuration archive exceeds extraction limits')
                    if member.isdir():
                        continue
                    if len(pure.parts) != 2 or pure.parts[1] not in FILES or member.name in seen:
                        raise CommandError('Unexpected or duplicate configuration file: {}'.format(member.name))
                    seen.add(member.name)
                    stream = tar.extractfile(member)
                    if stream is None:
                        raise CommandError('Cannot read archive member')
                    with stream:
                        try:
                            data = json.load(stream)
                        except (ValueError, UnicodeError) as exc:
                            raise CommandError('Invalid JSON in archive: {}'.format(member.name)) from exc
                    if not isinstance(data, dict):
                        raise CommandError('Configuration must contain JSON objects')
                    validate_config(pure.parts[1], data)
                    write_object(output / pure.parts[1], data)
                if not seen:
                    raise CommandError('Backup contains no supported configuration files')
        except tarfile.TarError as exc:
            raise CommandError('Invalid configuration archive') from exc
        yield output


def validate_config(filename, data):
    if filename == 'modules_config.json':
        enabled = data.get('enabled_modules', [])
        info = data.get('module_info', {})
        if (not isinstance(enabled, list) or any(not isinstance(x, str) for x in enabled)
                or not isinstance(info, dict) or any(not isinstance(x, dict) for x in info.values())):
            raise CommandError('Invalid module configuration in backup')
    if filename in ('ssh_targets.json', 'projects.json'):
        if any(not isinstance(value, dict) for value in data.values()):
            raise CommandError('Invalid entries in {}'.format(filename))


def merge_objects(local, incoming):
    merged = dict(local)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_objects(merged[key], value)
        elif key == 'enabled_modules' and isinstance(value, list):
            merged[key] = sorted(set(merged.get(key, [])) | set(value))
        else:
            merged[key] = value
    # The enabled list is authoritative after merging module configurations.
    if 'enabled_modules' in merged and isinstance(merged.get('module_info'), dict):
        for name, info in merged['module_info'].items():
            info['enabled'] = name in merged['enabled_modules']
    return merged


def restore_backup(path, config, merge=False, dry_run=False):
    config = Path(config)
    if config.is_symlink():
        raise CommandError('Refusing to replace a symlinked configuration directory')
    with extracted_backup(path) as incoming:
        names = sorted(p.name for p in incoming.iterdir())
        print('{} configuration files: {}'.format('Merge' if merge else 'Replace', ', '.join(names)))
        if dry_run:
            return None
        config.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.maxcli-restore-', dir=str(config.parent)) as temporary:
            staged = Path(temporary) / 'config'
            staged.mkdir(mode=0o700)
            if merge and config.exists():
                # Only supported config files participate; never follow symlinks.
                for name in FILES:
                    old = config / name
                    if old.is_symlink():
                        raise CommandError('Refusing configuration symlink: {}'.format(old))
                    if old.is_file():
                        write_object(staged / name, read_object(old))
            for name in names:
                data = read_object(incoming / name)
                if merge and (staged / name).exists():
                    data = merge_objects(read_object(staged / name), data)
                validate_config(name, data)
                write_object(staged / name, data)
            backup = config.with_name(config.name + '.before-restore-' + uuid.uuid4().hex[:8])
            existed = config.exists()
            if existed:
                os.replace(config, backup)
                backup.chmod(0o700)
            try:
                os.replace(staged, config)
            except BaseException:
                if existed:
                    os.replace(backup, config)
                raise
            if existed:
                print('Previous configuration preserved at {}'.format(backup))
                return backup
    return None
