"""Project discovery and explicit task execution; no implicit shell evaluation."""
import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import config_dir
from .runtime import CommandError
from .storage import read_object, write_object
from .utils.interactive import interactive_selection

PROJECT_FILE = '.maxcli.json'


def registry_path() -> Path:
    return config_dir() / 'projects.json'


def projects() -> Dict[str, Any]:
    data = read_object(registry_path())
    for name, item in data.items():
        if not isinstance(item, dict) or not isinstance(item.get('path'), str):
            raise CommandError("Invalid project entry: {}".format(name))
        if not isinstance(item.get('tags', []), list) or any(not isinstance(t, str) for t in item.get('tags', [])):
            raise CommandError("Project tags must be strings: {}".format(name))
    return data


def argv(value: Any, label: str) -> List[str]:
    if not isinstance(value, list) or not value or any(not isinstance(part, str) for part in value):
        raise CommandError('{} must be a nonempty JSON array of strings'.format(label))
    if not value[0] or any('\0' in part for part in value):
        raise CommandError('{} contains an invalid command argument'.format(label))
    return value


def project_config(root: Path) -> Dict[str, Any]:
    data = read_object(root / PROJECT_FILE)
    if data.get('version', 1) != 1:
        raise CommandError('Unsupported .maxcli.json version')
    for key in ('tasks', 'environments'):
        if not isinstance(data.get(key, {}), dict):
            raise CommandError('{} must be an object in .maxcli.json'.format(key))
    if 'editor' in data:
        argv(data['editor'], 'editor')
    return data


def resolve_project(name: Optional[str] = None, choose: bool = False) -> Dict[str, Any]:
    known = projects()
    if name:
        matches = [name] if name in known else [key for key in known if name.casefold() in key.casefold()]
        if len(matches) != 1:
            raise CommandError('Project not found or ambiguous: {}. Use max project list.'.format(name))
        name = matches[0]
        item = dict(known[name], name=name)
    elif choose:
        selected = interactive_selection('Open project', sorted(known))
        if not selected:
            raise CommandError('No project selected. Register one with max project add.')
        item = dict(known[selected], name=selected)
    else:
        cwd = Path.cwd().resolve()
        candidates = [(Path(info['path']).resolve(), key, info) for key, info in known.items()]
        matches_here = [(p, key, info) for p, key, info in candidates if p == cwd or p in cwd.parents]
        if matches_here:
            root, name, info = max(matches_here, key=lambda entry: len(entry[0].parts))
            item = dict(info, name=name)
        else:
            discovered = next((p for p in [cwd, *cwd.parents] if (p / PROJECT_FILE).is_file()), None)
            if discovered is None:
                raise CommandError('No project found. Use --project NAME or max project init.')
            item = {'name': discovered.name, 'path': str(discovered), 'tags': []}
    root = Path(item['path']).expanduser().resolve()
    if not root.is_dir():
        raise CommandError('Project directory no longer exists: {}'.format(root))
    return dict(item, path=str(root), config=project_config(root))


def add_project(args) -> None:
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise CommandError('Not a directory: {}'.format(root))
    if not args.name.strip():
        raise CommandError('Project name cannot be empty')
    known = projects()
    if args.name in known:
        raise CommandError('Project already registered; remove its entry before replacing it')
    entry = {'path': str(root), 'tags': sorted(set(args.tag))}
    if args.editor:
        entry['editor'] = argv(shlex.split(args.editor), 'editor')
    known[args.name] = entry
    write_object(registry_path(), known)
    print('Registered {} at {}'.format(args.name, root))


def list_projects(args) -> None:
    entries = [dict(info, name=name, exists=Path(info['path']).is_dir())
               for name, info in sorted(projects().items())
               if (not args.query or args.query.casefold() in name.casefold())
               and set(args.tag).issubset(info.get('tags', []))]
    if args.json:
        print(json.dumps(entries))
    else:
        for item in entries:
            print('{}  {}  [{}]{}'.format(item['name'], item['path'], ', '.join(item.get('tags', [])),
                                         '' if item['exists'] else ' (missing directory)'))
        if not entries:
            print('No matching projects. Use max project add NAME PATH.')


def remove_project(args) -> None:
    known = projects()
    if args.name not in known:
        raise CommandError('Unknown project: {}'.format(args.name))
    del known[args.name]
    write_object(registry_path(), known)
    print('Removed registration for {}. Project files are unchanged.'.format(args.name))


def init_project(args) -> None:
    path = Path.cwd() / PROJECT_FILE
    if path.exists():
        raise CommandError('{} already exists; edit it to add tasks'.format(path))
    write_object(path, {'version': 1, 'tasks': {}, 'environments': {}})
    print('Created {}. Add tasks as argument arrays, e.g. ["npm", "run", "dev"].'.format(path))


def show_project(args) -> None:
    item = resolve_project(args.name)
    if args.json:
        print(json.dumps(item))
    else:
        print('{}: {}'.format(item['name'], item['path']))
        print('Tags: ' + ', '.join(item.get('tags', [])))
        print('Tasks: ' + ', '.join(sorted(item['config'].get('tasks', {}))))
        print('Environments: ' + ', '.join(sorted(item['config'].get('environments', {}))))
        print('Use --json for editor and environment associations.')


def open_project(args) -> None:
    item = resolve_project(args.name, choose=args.name is None)
    editor = item['config'].get('editor') or item.get('editor')
    if editor is None:
        editor = shlex.split(os.environ.get('VISUAL') or os.environ.get('EDITOR') or 'code')
    command = argv(editor, 'editor') + [item['path']]
    if args.dry_run:
        print(shlex.join(command))
        return
    subprocess.run(command, cwd=item['path'], check=True)


def run_task(args) -> int:
    item = resolve_project(args.project)
    cfg = item['config']
    if args.task not in cfg.get('tasks', {}):
        raise CommandError('Unknown task {}. Available: {}'.format(args.task, ', '.join(cfg.get('tasks', {}))))
    task = cfg['tasks'][args.task]
    settings = task if isinstance(task, dict) else {'command': task}
    command = list(argv(settings.get('command'), 'task command'))
    extra = args.task_args
    command.extend(extra[1:] if extra[:1] == ['--'] else extra)
    root = Path(item['path'])
    relative_cwd = settings.get('cwd', '.')
    if not isinstance(relative_cwd, str):
        raise CommandError('Task cwd must be a string')
    cwd = (root / relative_cwd).resolve()
    if (cwd != root and root not in cwd.parents) or not cwd.is_dir():
        raise CommandError('Task cwd must be an existing directory inside the project')
    environment = {}
    if args.env:
        if args.env not in cfg.get('environments', {}):
            raise CommandError('Unknown environment: {}'.format(args.env))
        selected = cfg['environments'][args.env]
        if not isinstance(selected, dict):
            raise CommandError('Environment must be an object')
        environment = selected.get('env', {})
    task_env = settings.get('env', {})
    for values in (environment, task_env):
        if not isinstance(values, dict) or any(not isinstance(k, str) or not k or '=' in k or '\0' in k
                or not isinstance(v, str) or '\0' in v for k, v in values.items()):
            raise CommandError('Task/environment env must map valid variable names to strings')
    overrides = dict(environment, **task_env)
    if args.dry_run:
        print(json.dumps({'project': item['name'], 'cwd': str(cwd), 'command': command,
                          'environment': args.env, 'env_keys': sorted(overrides)}))
        return 0
    # Tasks run only on explicit invocation. No lifecycle hooks run on add/open/list.
    result = subprocess.run(command, cwd=str(cwd), env=dict(os.environ, **overrides))
    return result.returncode if result.returncode >= 0 else 128 - result.returncode


def register_commands(subparsers) -> None:
    group = subparsers.add_parser('project', help='Register, find, and open projects')
    subs = group.add_subparsers(dest='project_command', required=True)
    add = subs.add_parser('add', help='Register an existing directory')
    add.add_argument('name')
    add.add_argument('path', nargs='?', default='.')
    add.add_argument('--tag', action='append', default=[])
    add.add_argument('--editor', help='Editor command, e.g. "code --wait"')
    add.set_defaults(func=add_project)
    listing = subs.add_parser('list', help='Search projects by name or tags')
    listing.add_argument('query', nargs='?')
    listing.add_argument('--tag', action='append', default=[])
    listing.add_argument('--json', action='store_true')
    listing.set_defaults(func=list_projects)
    remove = subs.add_parser('remove', help='Remove a registration; never deletes project files')
    remove.add_argument('name')
    remove.set_defaults(func=remove_project)
    init = subs.add_parser('init', help='Create .maxcli.json in the current directory')
    init.set_defaults(func=init_project)
    show = subs.add_parser('show', help='Show project tasks and environment associations')
    show.add_argument('name', nargs='?')
    show.add_argument('--json', action='store_true')
    show.set_defaults(func=show_project)
    opening = subs.add_parser('open', help='Open a project in its configured editor')
    opening.add_argument('name', nargs='?')
    opening.add_argument('--dry-run', action='store_true')
    opening.set_defaults(func=open_project)
    run = subparsers.add_parser('run', help='Run a named project task',
                               epilog='Put MaxCLI options before TASK; everything after TASK is passed to the task.')
    run.add_argument('--project', help='Registered project name; defaults to current directory')
    run.add_argument('--env', help='Environment from .maxcli.json')
    run.add_argument('--dry-run', action='store_true', help='Print command plan as JSON without executing')
    run.add_argument('task')
    run.add_argument('task_args', nargs=argparse.REMAINDER)
    run.set_defaults(func=run_task)
