"""Named, portable argument-array recipes with prompted variables."""
import copy
import json
import re
import shlex
import subprocess
from pathlib import Path
from string import Formatter
from typing import Any

from .paths import config_dir
from .runtime import CommandError, NON_INTERACTIVE, prompt_input
from .storage import read_object, write_object
from .utils.interactive import interactive_selection

BUILTINS: dict[str, dict[str, Any]] = {
    'appstore-resize': {
        'description': 'App Store screenshot: force 1284x2778 pixels and flatten onto white.',
        'engine': 'imagemagick',
        'command': ['magick', '{input}', '-resize', '{size}', '-background', '{background}', '-flatten', '{output}'],
        'variables': {
            'input': {'prompt': 'Input image path'},
            'output': {'prompt': 'Output image path'},
            'size': {'prompt': 'Resize geometry (! forces exact dimensions)', 'default': '1284x2778!'},
            'background': {'prompt': 'Background color', 'default': 'white', 'choices': ['white', 'black']},
        },
    },
}
VARIABLE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')


def registry_path():
    return config_dir() / 'saved_commands.json'


def placeholders(command):
    if not isinstance(command, list) or not command or any(not isinstance(part, str) or '\0' in part for part in command):
        raise CommandError('command must be a nonempty argument array of strings without NUL characters')
    if not command[0]:
        raise CommandError('Command executable cannot be empty')
    names = set()
    try:
        for part in command:
            for _, name, spec, conversion in Formatter().parse(part):
                if name is not None:
                    if not VARIABLE.fullmatch(name) or spec or conversion:
                        raise CommandError('Use simple placeholders such as {input}; escape literal braces as {{ and }}')
                    names.add(name)
    except ValueError as exc:
        raise CommandError('Invalid command template: {}'.format(exc)) from exc
    return names


def validate_pack(data):
    if set(data) != {'version', 'commands'} or type(data['version']) is not int or data['version'] != 1:
        raise CommandError('Command packs require version 1 and a commands object')
    commands = data['commands']
    if not isinstance(commands, dict):
        raise CommandError('commands must be an object')
    for name, recipe in commands.items():
        if not name.strip() or '\0' in name or not isinstance(recipe, dict):
            raise CommandError('Each command needs a nonempty name and a recipe object')
        if set(recipe) - {'command', 'description', 'variables', 'engine'}:
            raise CommandError('Unknown recipe fields for {}'.format(name))
        if not isinstance(recipe.get('description', ''), str):
            raise CommandError('Command description must be a string')
        used = placeholders(recipe.get('command'))
        variables = recipe.get('variables', {})
        if not isinstance(variables, dict) or set(variables) != used:
            raise CommandError('{}: variables must match command placeholders exactly'.format(name))
        for key, settings in variables.items():
            if not isinstance(settings, dict) or set(settings) - {'prompt', 'default', 'choices'}:
                raise CommandError('Invalid variable definition: {}'.format(key))
            for field in ('prompt', 'default'):
                if field in settings and (not isinstance(settings[field], str) or '\0' in settings[field]):
                    raise CommandError('{} {} must be a string without NUL characters'.format(key, field))
            choices = settings.get('choices')
            if choices is not None:
                if (not isinstance(choices, list) or not choices
                        or any(not isinstance(x, str) or not x or '\0' in x for x in choices)
                        or len(set(choices)) != len(choices)):
                    raise CommandError('{} choices must be a nonempty list of unique strings'.format(key))
                if 'default' in settings and settings['default'] not in choices:
                    raise CommandError('{} default must be one of its choices'.format(key))
        engine = recipe.get('engine', 'command')
        if engine not in ('command', 'imagemagick'):
            raise CommandError('Unknown command engine: {}'.format(engine))
        if engine == 'imagemagick' and (recipe['command'][0] != 'magick' or not {'input', 'output'}.issubset(used)):
            raise CommandError('Image recipes must start with magick and declare {input} and {output}')
    return commands


def user_commands():
    path = registry_path()
    return validate_pack(read_object(path)) if path.exists() else {}


def all_commands():
    return dict(copy.deepcopy(BUILTINS), **user_commands())


def assignments(items, label, repeated=False):
    values: dict[str, Any] = {}
    for item in items:
        key, separator, value = item.partition('=')
        if not separator or not VARIABLE.fullmatch(key) or '\0' in value:
            raise CommandError('{} requires NAME=VALUE'.format(label))
        if repeated:
            values.setdefault(key, []).append(value)
        elif key in values:
            raise CommandError('Duplicate variable: {}'.format(key))
        else:
            values[key] = value
    return values


def save_command(args):
    template = args.template
    if template is None:
        template = prompt_input('Command template (e.g. magick "{input}" "{output}"): ')
    command = shlex.split(template)
    variables: dict[str, dict[str, Any]] = {name: {} for name in sorted(placeholders(command))}
    defaults = assignments(args.default, '--default')
    choices = assignments(args.choice, '--choice', repeated=True)
    if (set(defaults) | set(choices)) - set(variables):
        raise CommandError('Defaults and choices must refer to command placeholders')
    for key, settings in variables.items():
        if key in defaults:
            settings['default'] = defaults[key]
        if key in choices:
            settings['choices'] = choices[key]
    recipe = {'command': command, 'variables': variables, 'description': args.description, 'engine': args.engine}
    validate_pack({'version': 1, 'commands': {args.name: recipe}})
    known = user_commands()
    if args.name in all_commands() and not args.replace:
        raise CommandError('Command already exists; use --replace to update it')
    known[args.name] = recipe
    write_object(registry_path(), {'version': 1, 'commands': known})
    print('Saved {}'.format(args.name))


def list_commands(args):
    local = user_commands()
    entries = [dict(recipe, name=name, source='user' if name in local else 'builtin')
               for name, recipe in sorted(all_commands().items())]
    if args.json:
        print(json.dumps(entries))
    else:
        for item in entries:
            print('{} [{}]  {}'.format(item['name'], item['source'], item.get('description', '')))


def get_recipe(name):
    known = all_commands()
    if name is None:
        name = interactive_selection('Choose a saved command', sorted(known))
        if name is None:
            raise CommandError('No command selected')
    if name not in known:
        raise CommandError('Unknown saved command: {}. Use max gm commands list.'.format(name))
    return name, known[name]


def show_command(args):
    name, recipe = get_recipe(args.name)
    print(json.dumps({'version': 1, 'commands': {name: recipe}}, indent=2))


def resolve_values(recipe, supplied):
    variables = recipe.get('variables', {})
    unknown = set(supplied) - set(variables)
    if unknown:
        raise CommandError('Unknown variables: {}'.format(', '.join(sorted(unknown))))
    values = dict(supplied)
    for name, settings in variables.items():
        if name not in values:
            if NON_INTERACTIVE.get():
                if 'default' not in settings:
                    raise CommandError('Missing variable {}. Supply --set {}=VALUE.'.format(name, name))
                values[name] = settings['default']
            elif 'choices' in settings:
                choices = settings['choices'][:]
                if 'default' in settings:
                    choices.remove(settings['default'])
                    choices.insert(0, settings['default'])
                value = interactive_selection(settings.get('prompt', name), choices)
                if value is None:
                    raise CommandError('Selection cancelled')
                values[name] = value
            else:
                default = settings.get('default')
                prompt = settings.get('prompt', name) + (' [{}]'.format(default) if default is not None else '')
                values[name] = prompt_input(prompt + ': ') or (default if default is not None else '')
        value = values[name]
        if not isinstance(value, str) or not value or '\0' in value:
            raise CommandError('{} must have a nonempty value without NUL characters'.format(name))
        if 'choices' in settings and value not in settings['choices']:
            raise CommandError('{} must be one of: {}'.format(name, ', '.join(settings['choices'])))
    return values


def execute(name, supplied, dry_run=False, overwrite=False):
    name, recipe = get_recipe(name)
    values = resolve_values(recipe, supplied)
    if recipe.get('engine') == 'imagemagick':
        from .images import prepare_conversion, conversion_tool
        values = prepare_conversion(values, overwrite, dry_run)
        command = conversion_tool(required=not dry_run) + [part.format_map(values) for part in recipe['command'][1:]]
    else:
        command = [part.format_map(values) for part in recipe['command']]
    if not command[0]:
        raise CommandError('Command executable cannot be empty')
    if dry_run:
        print(json.dumps({'name': name, 'command': command}))
        return 0
    result = subprocess.run(command)  # Never evaluate templates or values through a shell.
    return result.returncode if result.returncode >= 0 else 128 - result.returncode


def run_command(args):
    return execute(args.name, assignments(args.values, '--set'), args.dry_run, args.overwrite)


def remove_command(args):
    known = user_commands()
    if args.name not in known:
        raise CommandError('No user command named {}. Built-in presets cannot be removed.'.format(args.name))
    del known[args.name]
    write_object(registry_path(), {'version': 1, 'commands': known})
    print('Removed {}'.format(args.name))


def export_commands(args):
    known = all_commands()
    names = args.names or sorted(known)
    missing = set(names) - set(known)
    if missing:
        raise CommandError('Unknown commands: {}'.format(', '.join(sorted(missing))))
    target = Path(args.file).expanduser()
    if target.resolve() == registry_path().resolve():
        raise CommandError('Export to a separate file, not the command registry')
    if target.exists() and not args.replace:
        raise CommandError('Export file exists; use --replace to overwrite')
    write_object(target, {'version': 1, 'commands': {name: known[name] for name in names}})
    print('Exported {} commands to {}'.format(len(names), target))


def import_commands(args):
    incoming = validate_pack(read_object(Path(args.file).expanduser()))
    local = user_commands()
    collisions = set(incoming) & set(all_commands())
    if collisions and not args.replace:
        raise CommandError('Commands already exist: {}. Use --replace to update.'.format(', '.join(sorted(collisions))))
    local.update(incoming)
    write_object(registry_path(), {'version': 1, 'commands': local})
    print('Imported {} commands. Use max gm commands show NAME to inspect them before running.'.format(len(incoming)))


def register_commands(subparsers):
    group = subparsers.add_parser('commands', help='Save, run, and share named command templates')
    group.set_defaults(func=run_command, name=None, values=[], dry_run=False, overwrite=False)
    subs = group.add_subparsers(dest='saved_command_action')
    listing = subs.add_parser('list', help='List saved commands and packaged presets')
    listing.add_argument('--json', action='store_true')
    listing.set_defaults(func=list_commands)
    saving = subs.add_parser('save', help='Save a command template; quote placeholders such as {input}')
    saving.add_argument('name', help='Human-readable name (quote names containing spaces)')
    saving.add_argument('--command', dest='template', help='Command string split into arguments, never evaluated by a shell')
    saving.add_argument('--description', default='')
    saving.add_argument('--default', action='append', default=[], metavar='NAME=VALUE')
    saving.add_argument('--choice', action='append', default=[], metavar='NAME=VALUE', help='Repeat for each allowed choice')
    saving.add_argument('--engine', choices=['command', 'imagemagick'], default='command')
    saving.add_argument('--replace', action='store_true')
    saving.set_defaults(func=save_command)
    showing = subs.add_parser('show', help='Inspect a recipe as a portable JSON pack')
    showing.add_argument('name')
    showing.set_defaults(func=show_command)
    running = subs.add_parser('run', help='Run a recipe; omit NAME for a selection menu')
    running.add_argument('name', nargs='?')
    running.add_argument('--set', dest='values', action='append', default=[], metavar='NAME=VALUE')
    running.add_argument('--dry-run', action='store_true', help='Print resolved argument array without executing')
    running.add_argument('--overwrite', action='store_true', help='Allow image recipes to replace an existing output')
    running.set_defaults(func=run_command)
    removing = subs.add_parser('remove', help='Remove a user recipe; built-in presets remain available')
    removing.add_argument('name')
    removing.set_defaults(func=remove_command)
    exporting = subs.add_parser('export', help='Write a shareable JSON pack (may contain literal command values)')
    exporting.add_argument('file')
    exporting.add_argument('names', nargs='*', help='Names to export; defaults to all recipes')
    exporting.add_argument('--replace', action='store_true')
    exporting.set_defaults(func=export_commands)
    importing = subs.add_parser('import', help='Import a JSON pack without executing its commands')
    importing.add_argument('file')
    importing.add_argument('--replace', action='store_true')
    importing.set_defaults(func=import_commands)
