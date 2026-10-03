"""Exercise the real entry point with isolated user state."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli_run(tmp_path):
    def run(*args):
        return subprocess.run(
            [sys.executable, '-m', 'maxcli', *args],
            env=dict(os.environ, MAXCLI_CONFIG_DIR=str(tmp_path / 'config'), PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=10,
        )
    return run


def test_module_failure_and_batch_validation(cli_run):
    result = cli_run('modules', 'enable', 'no_such_module')
    assert result.returncode == 1
    assert 'Unknown modules' in result.stderr
    assert cli_run('modules', 'enable', 'docker_manager', 'gcp_manager').returncode == 0
    data = json.loads(cli_run('modules', 'list', '--json').stdout)
    assert all(row['enabled'] for row in data if row['name'] in ('docker_manager', 'gcp_manager'))


def test_noninteractive_init_fails_promptly(cli_run):
    result = cli_run('--non-interactive', 'init')
    assert result.returncode != 0
    assert 'requires input' in result.stderr
    assert 'Traceback' not in result.stderr


def test_ssh_failure_reaches_exit_code(cli_run):
    result = cli_run('ssh', 'targets', 'remove', 'missing')
    assert result.returncode == 1


def test_ssh_json(cli_run):
    result = cli_run('ssh', 'targets', 'list', '--json')
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}


def test_invalid_config_is_preserved(cli_run, tmp_path):
    directory = tmp_path / 'config'
    directory.mkdir()
    path = directory / 'modules_config.json'
    path.write_text('{broken')
    result = cli_run('modules', 'list')
    assert result.returncode == 1
    assert path.read_text() == '{broken'


def test_setup_initialization_calls_existing_function(monkeypatch):
    from maxcli import config
    called = []
    monkeypatch.setattr(config, 'is_initialized', lambda: False)
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    monkeypatch.setattr(config, 'init_config', lambda args: called.append(args.force))
    config.check_initialization()
    assert called == [False]
