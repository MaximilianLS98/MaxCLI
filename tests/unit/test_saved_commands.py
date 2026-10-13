import copy
import json
import tarfile

import pytest

from maxcli import backups, images, saved_commands as recipes
from maxcli.runtime import CommandError, NON_INTERACTIVE


@pytest.mark.parametrize('recipe', [
    {'command': 'echo bad'},
    {'command': []},
    {'command': ['']},
    {'command': ['echo', '\0']},
    {'command': ['echo', '{'], 'variables': {}},
    {'command': ['echo', '{x.attr}'], 'variables': {'x': {}}},
    {'command': ['echo', '{x!r}'], 'variables': {'x': {}}},
    {'command': ['echo', '{x:10}'], 'variables': {'x': {}}},
    {'command': ['echo', '{x}'], 'variables': {}},
    {'command': ['echo'], 'variables': {'unused': {}}},
    {'command': ['echo', '{x}'], 'variables': {'x': {'choices': []}}},
    {'command': ['echo', '{x}'], 'variables': {'x': {'choices': ['a', 'a']}}},
    {'command': ['echo', '{x}'], 'variables': {'x': {'choices': ['a'], 'default': 'b'}}},
    {'command': ['echo', '{x}'], 'variables': {'x': {'default': 1}}},
    {'command': ['echo'], 'engine': 'shell'},
    {'command': ['echo'], 'engine': 'imagemagick'},
    {'command': ['echo'], 'unrecognized': True},
])
def test_invalid_pack_rejected(recipe):
    with pytest.raises(CommandError):
        recipes.validate_pack({'version': 1, 'commands': {'bad': recipe}})


def test_choice_menu_defaults_prompts_and_cancellation(monkeypatch):
    recipe = {'variables': {'color': {'prompt': 'Color', 'choices': ['black', 'white'], 'default': 'white'},
                            'size': {'default': '1284x2778!'}}}
    offered = []
    monkeypatch.setattr(recipes, 'interactive_selection', lambda title, choices: offered.append((title, choices)) or 'black')
    monkeypatch.setattr(recipes, 'prompt_input', lambda _: '')
    token = NON_INTERACTIVE.set(False)
    try:
        assert recipes.resolve_values(recipe, {}) == {'color': 'black', 'size': '1284x2778!'}
        assert offered == [('Color', ['white', 'black'])]
        monkeypatch.setattr(recipes, 'interactive_selection', lambda *args: None)
        with pytest.raises(CommandError, match='cancelled'):
            recipes.resolve_values(recipe, {})
    finally:
        NON_INTERACTIVE.reset(token)


def test_escaped_braces_and_variable_values_are_literal(monkeypatch):
    recipe = {'command': ['echo', '{{literal}}', '{value}'], 'variables': {'value': {}}}
    monkeypatch.setattr(recipes, 'get_recipe', lambda _: ('test', recipe))
    calls = []
    class Result:
        returncode = -15
    monkeypatch.setattr(recipes.subprocess, 'run', lambda command: calls.append(command) or Result())
    assert recipes.execute('test', {'value': '{value}; $HOME'}) == 143
    assert calls == [['echo', '{literal}', '{value}; $HOME']]


def test_engine_fallback_and_missing_dependency(monkeypatch):
    monkeypatch.setattr(images.shutil, 'which', lambda name: '/bin/' + name if name == 'gm' else None)
    assert images.conversion_tool() == ['gm', 'convert']
    monkeypatch.setattr(images.shutil, 'which', lambda _: None)
    assert images.conversion_tool(required=False) == ['magick']
    with pytest.raises(CommandError, match='brew install imagemagick'):
        images.conversion_tool()


def test_doctor_checks_malformed_registry(tmp_path, monkeypatch):
    from maxcli import doctor
    monkeypatch.setenv('MAXCLI_CONFIG_DIR', str(tmp_path))
    (tmp_path / 'saved_commands.json').write_text('{"version":2,"commands":{}}')
    results = doctor.inspect_environment()
    assert any(c['name'] == 'saved_commands.json' and c['status'] == 'error' for c in results['checks'])


def test_unencrypted_backup_omits_recipes_and_merge_keeps_local(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'config.json').write_text('{}')
    pack = {'version': 1, 'commands': {'secret command': {'command': ['echo', 'inline-secret'], 'variables': {}}}}
    (source / 'saved_commands.json').write_text(json.dumps(pack))
    archive = backups.create_backup(source, tmp_path / 'archives')
    with tarfile.open(archive) as tar:
        assert 'maxcli/saved_commands.json' not in tar.getnames()
    backups.restore_backup(archive, source, merge=True)
    assert json.loads((source / 'saved_commands.json').read_text()) == pack


def test_restore_accepts_valid_recipes_and_rejects_invalid_before_writing(tmp_path):
    pack = {'version': 1, 'commands': copy.deepcopy(recipes.BUILTINS)}
    backups.validate_config('saved_commands.json', pack)
    pack['commands']['appstore-resize']['variables'] = {}
    with pytest.raises(CommandError):
        backups.validate_config('saved_commands.json', pack)


def test_restore_merge_replaces_complete_recipe_and_retains_local_only(tmp_path):
    import io
    target = tmp_path / 'target'
    target.mkdir()
    local = {'version': 1, 'commands': {
        'shared': {'command': ['echo', '{old}'], 'variables': {'old': {'default': 'local'}}},
        'local only': {'command': ['echo', 'local'], 'variables': {}},
    }}
    incoming = {'version': 1, 'commands': {'shared': {'command': ['echo', 'updated'], 'variables': {}}}}
    (target / 'saved_commands.json').write_text(json.dumps(local))
    archive = tmp_path / 'pack.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        payload = json.dumps(incoming).encode()
        member = tarfile.TarInfo('maxcli/saved_commands.json')
        member.size = len(payload)
        tar.addfile(member, io.BytesIO(payload))
    backups.restore_backup(archive, target, merge=True)
    restored = json.loads((target / 'saved_commands.json').read_text())
    assert restored['commands']['shared'] == incoming['commands']['shared']
    assert restored['commands']['local only'] == local['commands']['local only']
