"""Opt-in real GitHub install + editable reload test; all state stays in tmp_path."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.mark.network
@pytest.mark.skipif(os.environ.get('MAXCLI_RUN_INSTALL_TESTS') != '1', reason='opt-in package download test')
def test_released_stable_and_live_checkout_coexist(tmp_path):
    repository = Path(__file__).resolve().parents[2]
    checkout = tmp_path / 'checkout with spaces'
    checkout.mkdir()
    shutil.copytree(repository / 'maxcli', checkout / 'maxcli', ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('pyproject.toml', 'README.md'):
        shutil.copy2(repository / name, checkout / name)
    root, binaries = tmp_path / 'managed', tmp_path / 'bin'
    home = tmp_path / 'home'
    home.mkdir()
    environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'))
    environment.pop('MAXCLI_CONFIG_DIR', None)
    installer = checkout / 'maxcli/installation.py'
    common = ['--root', str(root), '--bin-dir', str(binaries)]
    def execute(command):
        return subprocess.run(command, env=environment, cwd=checkout, text=True,
                              capture_output=True, timeout=600, check=True).stdout
    execute([sys.executable, str(installer), *common, '--version', 'v1.0.0'])
    stable = (root / 'stable').resolve()
    execute([sys.executable, str(installer), *common, '--dev', str(checkout)])
    assert (root / 'stable').resolve() == stable
    assert json.loads(execute([str(binaries / 'max'), '--version', '--json']))['release'] == 'v1.0.0'
    assert json.loads(execute([str(binaries / 'max-dev'), '--version', '--json']))['channel'] == 'development'
    execute([str(binaries / 'max-dev'), 'project', 'add', 'self', str(checkout)])
    assert (home / '.config/maxcli-dev/projects.json').is_file()
    assert not (home / '.config/maxcli/projects.json').exists()
    # Editing source is visible without reinstalling; isolated Python still finds the editable package.
    with (checkout / 'maxcli/__init__.py').open('a') as stream:
        stream.write('\nLIVE_RELOAD_PROBE = "changed-without-reinstall"\n')
    python = str(root / 'development/bin/python')
    assert execute([python, '-I', '-c', 'import maxcli; print(maxcli.LIVE_RELOAD_PROBE)']).strip() == 'changed-without-reinstall'
    # Stable remains the GitHub code even when invoked inside the edited checkout.
    python = str(root / 'stable/bin/python')
    assert execute([python, '-I', '-c', 'import maxcli; print(hasattr(maxcli, "LIVE_RELOAD_PROBE"))']).strip() == 'False'
    execute([str(binaries / 'max'), '--help'])
