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


def test_image_picker_filters_current_directory_and_preserves_names(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ('z.png', 'A screenshot.PNG', 'photo.jpeg', '.hidden.png', 'notes.txt'):
        (tmp_path / name).write_text('placeholder')
    (tmp_path / 'folder.jpg').mkdir()
    (tmp_path / 'nested').mkdir()
    (tmp_path / 'nested' / 'inside.png').write_text('placeholder')
    offered = []
    monkeypatch.setattr(images, 'interactive_selection',
                        lambda title, choices: offered.append((title, choices)) or 'A screenshot.PNG')
    assert images.pick_input_image() == 'A screenshot.PNG'
    assert offered[0][1] == ['A screenshot.PNG', 'photo.jpeg', 'z.png', images.MANUAL_PATH]
    assert str(tmp_path) in offered[0][0]


def test_image_picker_manual_entry_empty_directory_and_cancel(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompts = []
    monkeypatch.setattr(images, 'prompt_input', lambda prompt: prompts.append(prompt) or '../other image.png')
    # Empty directories fall back to a path prompt without an empty menu.
    monkeypatch.setattr(images, 'interactive_selection', lambda *args: pytest.fail('Unexpected picker'))
    assert images.pick_input_image('Source') == '../other image.png'
    assert prompts == ['Source: ']
    (tmp_path / 'here.png').touch()
    monkeypatch.setattr(images, 'interactive_selection', lambda *args: images.MANUAL_PATH)
    assert images.pick_input_image() == '../other image.png'
    monkeypatch.setattr(images, 'interactive_selection', lambda *args: None)
    with pytest.raises(CommandError, match='cancelled'):
        images.pick_input_image()


def test_input_picker_respects_explicit_values_defaults_choices_and_noninteractive(monkeypatch):
    recipe = {'engine': 'imagemagick', 'variables': {'input': {}}}
    picked = []
    monkeypatch.setattr(images, 'pick_input_image', lambda prompt: picked.append(prompt) or 'picked.png')
    monkeypatch.setattr(recipes, 'prompt_input', lambda _: '')
    monkeypatch.setattr(recipes, 'interactive_selection', lambda *args: 'choice.png')
    token = NON_INTERACTIVE.set(False)
    try:
        assert recipes.resolve_values(recipe, {}) == {'input': 'picked.png'}
        assert recipes.resolve_values(recipe, {'input': 'explicit.png'}) == {'input': 'explicit.png'}
        recipe['variables']['input'] = {'default': 'default.png'}
        assert recipes.resolve_values(recipe, {}) == {'input': 'default.png'}
        recipe['variables']['input'] = {'choices': ['choice.png']}
        assert recipes.resolve_values(recipe, {}) == {'input': 'choice.png'}
        assert picked == ['input']
    finally:
        NON_INTERACTIVE.reset(token)
    token = NON_INTERACTIVE.set(True)
    try:
        recipe['variables']['input'] = {}
        with pytest.raises(CommandError, match='Missing variable input'):
            recipes.resolve_values(recipe, {})
        assert recipes.resolve_values(recipe, {'input': 'explicit.png'}) == {'input': 'explicit.png'}
        assert picked == ['input']
    finally:
        NON_INTERACTIVE.reset(token)
