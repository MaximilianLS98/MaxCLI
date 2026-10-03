import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
from unittest.mock import Mock

import pytest

from maxcli import backups, config
from maxcli.runtime import CommandError


def test_config_display_redacts_secret(monkeypatch, capsys):
    monkeypatch.setattr(config, 'load_config', lambda: {'git_name': 'Tester', 'coolify_api_key': 'DO-NOT-PRINT'})
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    config.init_config(argparse.Namespace(force=False))
    text = capsys.readouterr().out
    assert 'DO-NOT-PRINT' not in text
    assert '[redacted]' in text


def test_environment_secret_overrides_stored_secret(monkeypatch):
    monkeypatch.setenv('MAXCLI_COOLIFY_API_KEY', 'from-environment')
    monkeypatch.setattr(config, 'load_config', lambda: {'coolify_api_key': 'stored'})
    assert config.get_config_value('coolify_api_key') == 'from-environment'


def test_backup_omits_secrets_and_restore_merge_persists(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'config.json').write_text(json.dumps({'git_name': 'Remote', 'coolify_api_key': 'secret'}))
    (source / 'modules_config.json').write_text(json.dumps({'enabled_modules': ['docker_manager']}))
    archive = backups.create_backup(source, tmp_path / 'archives')
    assert archive.stat().st_mode & 0o777 == 0o600
    with tarfile.open(archive) as tar:
        data = json.load(tar.extractfile('maxcli/config.json'))
        assert data == {'git_name': 'Remote'}
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'config.json').write_text(json.dumps({'git_name': 'Local', 'coolify_api_key': 'local-secret'}))
    (target / 'modules_config.json').write_text(json.dumps({'enabled_modules': ['ssh_manager']}))
    backups.restore_backup(archive, target, merge=True, dry_run=True)
    assert json.loads((target / 'config.json').read_text())['git_name'] == 'Local'
    recovery = backups.restore_backup(archive, target, merge=True)
    assert recovery.is_dir()
    assert json.loads((recovery / 'config.json').read_text())['git_name'] == 'Local'
    assert json.loads((target / 'config.json').read_text()) == {'git_name': 'Remote', 'coolify_api_key': 'local-secret'}
    assert set(json.loads((target / 'modules_config.json').read_text())['enabled_modules']) == {'ssh_manager', 'docker_manager'}


@pytest.mark.parametrize('name,kind', [('../outside', 'file'), ('/tmp/outside', 'file'), ('maxcli/link', 'link'), ('maxcli/device', 'device')])
def test_archive_rejects_unsafe_members(tmp_path, name, kind):
    archive = tmp_path / 'bad.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        member = tarfile.TarInfo(name)
        member.type = tarfile.SYMTYPE if kind == 'link' else tarfile.CHRTYPE if kind == 'device' else tarfile.REGTYPE
        member.linkname = '/tmp'
        tar.addfile(member, io.BytesIO(b''))
    with pytest.raises(CommandError):
        backups.restore_backup(archive, tmp_path / 'target')
    assert not (tmp_path / 'target').exists()


def test_failed_restore_rolls_back_original_directory(tmp_path, monkeypatch):
    source, target = tmp_path / 'source', tmp_path / 'target'
    source.mkdir(); target.mkdir()
    (source / 'config.json').write_text('{"name":"new"}')
    (target / 'config.json').write_text('{"name":"old"}')
    archive = backups.create_backup(source, tmp_path / 'archives')
    replace = os.replace
    def fail_activation(src, dst):
        if Path(src).name == 'config' and Path(dst) == target:
            raise OSError('simulated activation failure')
        return replace(src, dst)
    monkeypatch.setattr(backups.os, 'replace', fail_activation)
    with pytest.raises(OSError):
        backups.restore_backup(archive, target)
    assert json.loads((target / 'config.json').read_text()) == {'name': 'old'}


def test_dotfiles_keep_recovery_copy(tmp_path, monkeypatch):
    from maxcli.commands import setup
    (tmp_path / 'dotfiles').mkdir()
    (tmp_path / 'dotfiles/.zshrc').write_text('new shell config')
    (tmp_path / '.zshrc').write_text('old shell config')
    monkeypatch.setattr(setup.Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(setup, 'get_config_value', lambda _: 'https://example.invalid/dotfiles')
    setup.clone_dotfiles()
    assert (tmp_path / '.zshrc').read_text() == 'new shell config'
    assert next(tmp_path.glob('.zshrc.maxcli-backup-*')).read_text() == 'old shell config'


def test_coolify_http_failure_never_prints_token(monkeypatch, capsys):
    from maxcli.commands import coolify
    monkeypatch.setattr(coolify, 'get_coolify_config', lambda: ('SECRET-TOKEN', 'https://example.invalid'))
    opener = Mock()
    opener.open.side_effect = urllib.error.HTTPError('https://example.invalid', 401, 'SECRET-TOKEN', {}, None)
    monkeypatch.setattr(coolify.urllib.request, 'build_opener', lambda *args: opener)
    assert coolify.make_coolify_request('/services') is None
    captured = capsys.readouterr()
    assert '401' in captured.err
    assert 'SECRET-TOKEN' not in captured.out + captured.err
    assert opener.open.call_args.kwargs['timeout'] == 20


@pytest.mark.skipif(shutil.which('gpg') is None, reason='GPG unavailable')
def test_encrypted_backup_roundtrip(tmp_path, monkeypatch):
    # GPG agent sockets need a short pathname on macOS.
    temporary_keyring = tempfile.TemporaryDirectory(prefix='maxgpg-', dir='/tmp')
    keyring = Path(temporary_keyring.name)
    monkeypatch.setenv('GNUPGHOME', str(keyring))
    recipient = 'maxcli-test@example.invalid'
    try:
        subprocess.run(['gpg', '--batch', '--pinentry-mode', 'loopback', '--passphrase', '',
                        '--quick-generate-key', recipient, 'rsa2048', 'encr', '1d'],
                       check=True, capture_output=True, timeout=30)
        source = tmp_path / 'source'
        source.mkdir()
        (source / 'config.json').write_text('{"coolify_api_key":"encrypted-secret"}')
        archive = backups.create_backup(source, tmp_path / 'archives', recipient)
        assert archive.suffix == '.gpg'
        assert len(list((tmp_path / 'archives').iterdir())) == 1
        backups.restore_backup(archive, tmp_path / 'restored')
        assert json.loads((tmp_path / 'restored/config.json').read_text())['coolify_api_key'] == 'encrypted-secret'
    finally:
        if shutil.which('gpgconf'):
            subprocess.run(['gpgconf', '--homedir', str(keyring), '--kill', 'gpg-agent'], capture_output=True)
        temporary_keyring.cleanup()
