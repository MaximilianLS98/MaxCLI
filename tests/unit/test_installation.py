import argparse
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest
from maxcli import installation as inst


@pytest.fixture
def channels(tmp_path, monkeypatch):
    root, binaries = tmp_path / 'install root', tmp_path / 'bin'
    monkeypatch.setattr(inst, 'release_info', lambda repo, version=None: {'tag_name': version or 'v2.0.0'})
    def build(destination, source, editable=False, with_dev_tools=False):
        (destination / 'bin').mkdir(parents=True)
        (destination / 'bin/python').touch()
    monkeypatch.setattr(inst, 'build_environment', build)
    return root, binaries


def test_stable_and_development_are_independent(channels, monkeypatch, tmp_path):
    root, binaries = channels
    inst.install(root=root, bin_dir=binaries)
    stable = (root / 'stable').resolve()
    checkout = tmp_path / 'source'
    (checkout / 'maxcli').mkdir(parents=True)
    (checkout / 'maxcli/cli.py').touch()
    (checkout / 'pyproject.toml').touch()
    inst.install('development', source=str(checkout), root=root, bin_dir=binaries)
    assert (root / 'stable').resolve() == stable
    assert (root / 'development').resolve() != stable
    assert ' -I ' in (binaries / 'max').read_text()
    assert 'development' in (binaries / 'max-dev').read_text()
    monkeypatch.setattr(inst, 'current_installation', lambda: json.loads((root / 'development' / inst.METADATA).read_text()))
    with pytest.raises(inst.InstallError, match='live checkout'):
        inst.update(argparse.Namespace())


def test_failed_install_preserves_active_release(channels, monkeypatch):
    root, binaries = channels
    inst.install(root=root, bin_dir=binaries)
    active = (root / 'stable').resolve()
    def fail(*args):
        raise subprocess.CalledProcessError(1, ['pip'])
    monkeypatch.setattr(inst, 'build_environment', fail)
    with pytest.raises(subprocess.CalledProcessError):
        inst.install(root=root, bin_dir=binaries, version='v2.1.0')
    assert (root / 'stable').resolve() == active
    assert len(list((root / 'envs').iterdir())) == 1


def test_update_and_rollback(channels, monkeypatch):
    root, binaries = channels
    inst.install(root=root, bin_dir=binaries, version='v2.0.0')
    first = (root / 'stable').resolve()
    inst.install(root=root, bin_dir=binaries, version='v2.1.0')
    second = (root / 'stable').resolve()
    assert first != second
    monkeypatch.setattr(inst.subprocess, 'run', Mock())
    inst.rollback(root, 'stable')
    assert (root / 'stable').resolve() == first
    assert (root / 'stable-previous').resolve() == second


def test_existing_binary_requires_explicit_replacement(channels):
    root, binaries = channels
    binaries.mkdir()
    (binaries / 'max').write_text('another program')
    with pytest.raises(inst.InstallError, match='already exists'):
        inst.install(root=root, bin_dir=binaries)
    assert (binaries / 'max').read_text() == 'another program'
    inst.install(root=root, bin_dir=binaries, replace_existing=True)
    assert next(binaries.glob('max.backup-*')).read_text() == 'another program'


def test_release_resolution_never_accepts_prereleases(monkeypatch):
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = json.dumps({'tag_name': 'v2-rc1', 'prerelease': True})
    monkeypatch.setattr(inst.urllib.request, 'urlopen', lambda *a, **kw: response)
    with pytest.raises(inst.InstallError, match='stable'):
        inst.release_info()


def test_uninstall_only_deactivates_one_channel(channels, monkeypatch):
    root, binaries = channels
    info = inst.install(root=root, bin_dir=binaries)
    active = (root / 'stable').resolve()
    monkeypatch.setattr(inst, 'current_installation', lambda: info)
    inst.uninstall(argparse.Namespace(force=True, dry_run=True))
    assert (binaries / 'max').exists()
    inst.uninstall(argparse.Namespace(force=True, dry_run=False))
    assert not (binaries / 'max').exists()
    assert not (root / 'stable').exists()
    assert active.exists()


def test_unmanaged_update_is_actionable(monkeypatch):
    monkeypatch.setattr(inst, 'current_installation', lambda: None)
    with pytest.raises(inst.InstallError, match='unmanaged'):
        inst.update(argparse.Namespace())
