import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / 'project with spaces'
    root.mkdir()
    env = dict(os.environ, MAXCLI_CONFIG_DIR=str(tmp_path / 'config'),
               PYTHONPATH=str(Path(__file__).resolve().parents[2]), PYTHONDONTWRITEBYTECODE='1')
    def run(*args, cwd=None):
        return subprocess.run([sys.executable, '-m', 'maxcli', *args], env=env, cwd=cwd or root,
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=10)
    return root, run


def test_register_search_open_remove(workspace):
    root, run = workspace
    assert run('project', 'add', 'app', str(root), '--tag', 'personal', '--editor', 'code --wait').returncode == 0
    listed = run('project', 'list', 'ap', '--tag', 'personal', '--json')
    assert json.loads(listed.stdout)[0]['path'] == str(root)
    assert run('project', 'add', 'app', str(root)).returncode == 1
    opened = run('project', 'open', 'app', '--dry-run')
    assert opened.returncode == 0
    assert 'code --wait' in opened.stdout and str(root) in opened.stdout
    assert run('project', 'remove', 'app').returncode == 0
    assert root.is_dir()
    assert json.loads(run('project', 'list', '--json').stdout) == []


def test_task_cwd_environment_arguments_and_exit(workspace):
    root, run = workspace
    (root / '.maxcli.json').write_text(json.dumps({
        'version': 1,
        'tasks': {
            'inspect': [sys.executable, '-c', 'import os,sys,json;print(json.dumps([os.getcwd(),os.environ["MODE"],sys.argv[1:]]))'],
            'fail': [sys.executable, '-c', 'raise SystemExit(7)'],
        },
        'environments': {'dev': {'env': {'MODE': 'development'}, 'ssh_target': 'dev-server'}},
    }))
    nested = root / 'nested'
    nested.mkdir()
    result = run('run', '--env', 'dev', 'inspect', '--', 'literal;echo nope', cwd=nested)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [str(root), 'development', ['literal;echo nope']]
    assert run('run', 'fail').returncode == 7
    assert run('run', 'missing').returncode == 1
    assert run('run', '--env', 'missing', 'inspect').returncode == 1
    plan = json.loads(run('run', '--dry-run', '--env', 'dev', 'inspect').stdout)
    assert plan['env_keys'] == ['MODE']
    assert 'development' not in json.dumps(plan)


def test_editor_executes_with_directory_as_one_argument(workspace):
    root, run = workspace
    script = root / 'editor.py'
    script.write_text('import sys,json;print(json.dumps(sys.argv[1:]))')
    (root / '.maxcli.json').write_text(json.dumps({'editor': [sys.executable, str(script)]}))
    run('project', 'add', 'app', str(root))
    result = run('project', 'open', 'app')
    assert result.returncode == 0
    assert json.loads(result.stdout) == [str(root)]


def test_invalid_configuration_and_no_implicit_task_execution(workspace):
    root, run = workspace
    (root / '.maxcli.json').write_text(json.dumps({'tasks': {'bad': 'echo not-an-argv-array'}}))
    assert run('project', 'add', 'app', str(root)).returncode == 0
    assert run('run', 'bad').returncode == 1
    assert run('project', 'init').returncode == 1
    (root / '.maxcli.json').write_text(json.dumps({'tasks': {'escape': {'command': ['echo', 'x'], 'cwd': '..'}}}))
    assert run('run', 'escape').returncode == 1
    (root / '.maxcli.json').write_text('{broken')
    assert run('project', 'show', 'app').returncode == 1


def test_init_and_missing_path(workspace):
    root, run = workspace
    assert run('project', 'init').returncode == 0
    assert json.loads((root / '.maxcli.json').read_text())['version'] == 1
    assert run('project', 'add', 'missing', str(root / 'missing')).returncode == 1
