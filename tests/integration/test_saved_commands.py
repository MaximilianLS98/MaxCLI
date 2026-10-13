import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def workspace(tmp_path):
    config = tmp_path / 'config'
    env = dict(os.environ, MAXCLI_CONFIG_DIR=str(config),
               PYTHONPATH=str(Path(__file__).resolve().parents[2]), PYTHONDONTWRITEBYTECODE='1')

    def run(*args):
        return subprocess.run([sys.executable, '-m', 'maxcli', *args], env=env, cwd=tmp_path,
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30)

    return tmp_path, config, run


def test_save_run_literal_arguments_and_exit_status(workspace):
    root, config, run = workspace
    script = root / 'argument_probe.py'
    script.write_text('import sys,json; print(json.dumps(sys.argv[1:])); raise SystemExit(7)')
    template = '{} "{}" "{{input}}"'.format(sys.executable, script)
    saved = run('gm', 'commands', 'save', 'Human readable name', '--command', template)
    assert saved.returncode == 0, saved.stderr
    assert (config / 'saved_commands.json').stat().st_mode & 0o777 == 0o600
    assert not (config / 'modules_config.json').exists()
    value = 'a file; $(touch should-not-exist) "quotes" {other}'
    executed = run('gm', 'commands', 'run', 'Human readable name', '--set', 'input=' + value)
    assert executed.returncode == 7
    assert json.loads(executed.stdout) == [value]
    assert not (root / 'should-not-exist').exists()
    dry = run('gm', 'commands', 'run', 'Human readable name', '--set', 'input=' + value, '--dry-run')
    assert dry.returncode == 0
    assert json.loads(dry.stdout)['command'][-1] == value
    assert run('gm', 'commands', 'run', 'Human readable name').returncode == 1
    assert run('gm', 'commands', 'run', 'Human readable name', '--set', 'unknown=x').returncode == 1
    assert run('gm', 'commands', 'run', 'Human readable name', '--set', 'input=x', '--set', 'input=y').returncode == 1


def test_defaults_choices_update_remove(workspace):
    _, _, run = workspace
    assert run('gm', 'commands', 'save', 'List files', '--command', 'ls {style}',
               '--default', 'style=-l', '--choice', 'style=-l', '--choice', 'style=-la').returncode == 0
    assert json.loads(run('gm', 'commands', 'run', 'List files', '--dry-run').stdout)['command'] == ['ls', '-l']
    assert run('gm', 'commands', 'run', 'List files', '--set', 'style=-la').returncode == 0
    assert run('gm', 'commands', 'run', 'List files', '--set', 'style=invalid').returncode == 1
    assert run('gm', 'commands', 'save', 'List files', '--command', 'ls -a').returncode == 1
    assert run('gm', 'commands', 'save', 'List files', '--command', 'ls -a', '--replace').returncode == 0
    assert run('gm', 'commands', 'remove', 'List files').returncode == 0
    assert run('gm', 'commands', 'run', 'List files').returncode == 1
    assert run('gm', 'commands', 'remove', 'appstore-resize').returncode == 1
    assert run('gm', 'commands', 'save', 'appstore-resize', '--command', 'echo override', '--replace').returncode == 0
    assert json.loads(run('gm', 'commands', 'run', 'appstore-resize', '--dry-run').stdout)['command'] == ['echo', 'override']
    assert run('gm', 'commands', 'remove', 'appstore-resize').returncode == 0
    assert '1284x2778!' in run('gm', 'commands', 'show', 'appstore-resize').stdout


def test_portable_pack_atomic_import_and_no_execution(workspace):
    root, config, run = workspace
    template = '{} -c "from pathlib import Path; Path(\'marker\').touch()"'.format(sys.executable)
    assert run('gm', 'commands', 'save', 'Create marker', '--command', template).returncode == 0
    assert run('gm', 'commands', 'export', 'pack.json', 'Create marker', 'appstore-resize').returncode == 0
    pack = json.loads((root / 'pack.json').read_text())
    assert set(pack['commands']) == {'Create marker', 'appstore-resize'}
    assert run('gm', 'commands', 'export', 'pack.json').returncode == 1
    assert run('gm', 'commands', 'export', str(config / 'saved_commands.json'), '--replace').returncode == 1
    assert run('gm', 'commands', 'import', 'pack.json').returncode == 1
    assert run('gm', 'commands', 'remove', 'Create marker').returncode == 0
    assert run('gm', 'commands', 'import', 'pack.json', '--replace').returncode == 0
    assert not (root / 'marker').exists()
    before = (config / 'saved_commands.json').read_bytes()
    pack['commands']['bad'] = {'command': 'echo bad'}
    (root / 'pack.json').write_text(json.dumps(pack))
    assert run('gm', 'commands', 'import', 'pack.json', '--replace').returncode == 1
    assert (config / 'saved_commands.json').read_bytes() == before
    entries = json.loads(run('gm', 'commands', 'list', '--json').stdout)
    assert {item['name'] for item in entries} == {'Create marker', 'appstore-resize'}


def test_core_commands_work_without_valid_module_config(workspace):
    _, config, run = workspace
    config.mkdir()
    (config / 'modules_config.json').write_text('broken')
    assert run('gm', 'commands', 'list').returncode == 0
    result = run('--non-interactive', 'gm', 'appstore', '--input', 'in.png', '--output', 'out.png', '--dry-run')
    assert result.returncode == 0, result.stderr
    command = json.loads(result.stdout)['command']
    assert command[1:] == [str(config.parent / 'in.png'), '-resize', '1284x2778!', '-background', 'white', '-flatten',
                           str(config.parent / 'out.png')]
    assert run('gm', 'commands', 'run').returncode == 1
    assert run('gm', 'appstore').returncode == 1


@pytest.mark.skipif(shutil.which('magick') is None, reason='ImageMagick not installed')
def test_real_resize_dimensions_background_and_overwrite(workspace):
    root, _, run = workspace
    source = root / 'input with spaces.png'
    output = root / 'output with spaces.png'
    subprocess.run(['magick', '-size', '4x8', 'xc:none', '-fill', 'red', '-draw', 'rectangle 0,0 1,3', str(source)], check=True)
    original = source.read_bytes()
    result = run('gm', 'appstore', '--input', str(source), '--output', str(output))
    assert result.returncode == 0, result.stderr
    inspected = subprocess.check_output(['magick', str(output), '-format', '%wx%h %[opaque] %[pixel:p{1283,2777}]', 'info:'], text=True)
    assert inspected.startswith('1284x2778 True ')
    assert '255,255,255' in inspected or '100%,100%,100%' in inspected
    assert source.read_bytes() == original
    previous = output.read_bytes()
    assert run('gm', 'appstore', '--input', str(source), '--output', str(output)).returncode == 1
    assert output.read_bytes() == previous
    assert run('gm', 'appstore', '--input', str(source), '--output', str(output), '--overwrite', '--size', '12x24!').returncode == 0
    assert subprocess.check_output(['magick', 'identify', '-format', '%wx%h', str(output)], text=True) == '12x24'
    assert run('gm', 'appstore', '--input', str(source), '--output', str(source), '--overwrite').returncode == 1
    hardlink = root / 'hardlink.png'
    os.link(source, hardlink)
    assert run('gm', 'appstore', '--input', str(source), '--output', str(hardlink), '--overwrite').returncode == 1
    assert source.read_bytes() == original
    assert run('gm', 'appstore', '--input', 'missing.png', '--output', 'new.png').returncode == 1


def test_namespace_help_and_core_entry_points(workspace):
    _, _, run = workspace
    help_text = run('gm', '--help')
    assert help_text.returncode == 0
    assert 'commands' in help_text.stdout and 'appstore' in help_text.stdout
    assert run('gm', 'commands', '--help').returncode == 0
    assert run('commands', 'list').returncode == 2
    assert run('image', 'appstore').returncode == 2
    assert run('gm').returncode == 1
    assert run('gm', 'commands').returncode == 1


@pytest.mark.parametrize('arguments', [('gm',), ('gm', 'commands'), ('gm', 'commands', 'run'), ('gm', 'appstore')])
def test_interactive_namespace_runs_recipe_with_directory_picker(tmp_path, monkeypatch, arguments):
    from types import SimpleNamespace
    from maxcli import cli, images, saved_commands as recipes

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('MAXCLI_CONFIG_DIR', str(tmp_path / 'config'))
    source = tmp_path / 'screenshot with spaces.PNG'
    source.write_bytes(b'source stays unchanged')
    menu_calls = []

    def select_recipe_or_background(title, choices):
        menu_calls.append((title, choices))
        return 'appstore-resize' if 'appstore-resize' in choices else 'white'

    monkeypatch.setattr(recipes, 'interactive_selection', select_recipe_or_background)
    monkeypatch.setattr(images, 'interactive_selection',
                        lambda title, choices: menu_calls.append((title, choices)) or source.name)
    answers = iter(['output with spaces.png', ''])
    monkeypatch.setattr(recipes, 'prompt_input', lambda _: next(answers))
    monkeypatch.setattr(images, 'conversion_tool', lambda **kwargs: ['magick'])
    executed = []
    monkeypatch.setattr(recipes.subprocess, 'run', lambda command: executed.append(command) or SimpleNamespace(returncode=0))
    monkeypatch.setattr(cli.sys, 'stdin', SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(cli.sys, 'argv', ['max', *arguments])
    cli.main()
    assert executed == [['magick', str(source), '-resize', '1284x2778!', '-background', 'white', '-flatten',
                         str(tmp_path / 'output with spaces.png')]]
    assert any(choices == [source.name, images.MANUAL_PATH] for _, choices in menu_calls)
    assert source.read_bytes() == b'source stays unchanged'
