"""Exercise the cleanup entry point with an isolated home and broken configuration."""
import json
import os
import subprocess
import sys


def test_cleanup_cli_is_read_only_by_default_and_requires_explicit_approval(tmp_path):
    home = tmp_path / 'home'
    cache = home / '.npm/_cacache/package'
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b'cached package' * 1024)
    config = tmp_path / 'config'
    config.mkdir()
    modules = config / 'modules_config.json'
    modules.write_text('{broken')

    def run(*args):
        return subprocess.run([sys.executable, '-m', 'maxcli', *args], stdin=subprocess.DEVNULL,
                              env=dict(os.environ, HOME=str(home), MAXCLI_CONFIG_DIR=str(config), PYTHONDONTWRITEBYTECODE='1'),
                              text=True, capture_output=True, timeout=10)

    preview = run('clean', '--category', 'npm', '--json')
    assert preview.returncode == 0, preview.stderr
    assert not json.loads(preview.stdout)['applied']
    assert cache.exists()
    denied = run('--non-interactive', 'clean', '--category', 'npm', '--apply')
    assert denied.returncode == 1 and 'requires input' in denied.stderr
    assert cache.exists()
    applied = run('--non-interactive', 'clean', '--category', 'npm', '--apply', '--yes', '--json')
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)['targets'][0]['cleanup_status'] == 'cleared'
    assert not cache.exists()
    assert modules.read_text() == '{broken'
    assert sorted(path.name for path in config.iterdir()) == ['modules_config.json']
    assert run('clean', '--help').returncode == 0
