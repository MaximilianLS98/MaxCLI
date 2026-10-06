"""Preview and explicitly clear a fixed allowlist of regenerable development caches.

Directory descriptors keep scans and deletion from following symlink replacements.
No external tools, shell commands, configuration writes, or sudo are involved.
"""
import os
import platform
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .runtime import CommandError, prompt_input


@dataclass(frozen=True)
class Target:
    category: str
    path: Path
    effect: str
    cleanable: bool = True


CATEGORIES = ('npm', 'bun', 'pnpm', 'gradle', 'cocoapods', 'xcode', 'simulator-caches', 'test-browsers')


def targets(home: Path, system: str) -> list[Target]:
    """Use default locations only; environment/config overrides are never deletion targets."""
    definitions = [
        ('npm', '.npm/_cacache', 'Packages must be downloaded again.'),
        ('bun', '.bun/install/cache', 'Packages must be downloaded again.'),
        ('gradle', '.gradle/caches', 'Dependencies and build caches must be recreated.'),
        ('gradle', '.gradle/wrapper/dists', 'Gradle distributions must be downloaded again.'),
        ('test-browsers', '.cache/puppeteer', 'Run Puppeteer browser installation again before testing.'),
    ]
    if system == 'Darwin':
        definitions.extend([
            ('pnpm', 'Library/Caches/pnpm', 'Package metadata and temporary dlx installations must be recreated.'),
            ('cocoapods', 'Library/Caches/CocoaPods', 'Pods must be downloaded again; project Pods are preserved.'),
            ('xcode', 'Library/Developer/Xcode/DerivedData', 'Projects must rebuild and reindex.'),
            ('xcode', 'Library/Caches/com.apple.dt.Xcode', 'Xcode caches must be recreated.'),
            ('simulator-caches', 'Library/Developer/CoreSimulator/Caches', 'Simulator caches must be recreated.'),
            ('test-browsers', 'Library/Caches/ms-playwright', 'Run playwright install again before testing.'),
        ])
    else:
        definitions.extend([
            ('pnpm', '.cache/pnpm', 'Package metadata and temporary dlx installations must be recreated.'),
            ('test-browsers', '.cache/ms-playwright', 'Run playwright install again before testing.'),
        ])
    result = [Target(category, home / relative, effect) for category, relative, effect in definitions]
    review = [
        ('pnpm-store', 'Library/pnpm/store' if system == 'Darwin' else '.local/share/pnpm/store',
         'Use pnpm store prune to remove unreferenced packages from the configured store.'),
        ('android-devices', '.android/avd', 'Review and delete unused virtual devices in Android Studio Device Manager.'),
    ]
    if system == 'Darwin':
        review.extend([
            ('library-caches', 'Library/Caches', 'Includes some caches above; review other caches in their owning apps.'),
            ('app-data', 'Library/Application Support', 'May contain sessions, databases, and personal data; review in each app.'),
            ('android-sdk', 'Library/Android/sdk', 'Uninstall unused SDK versions and system images in Android Studio SDK Manager.'),
            ('simulator-devices', 'Library/Developer/CoreSimulator/Devices', 'Review devices in Xcode Devices and Simulators.'),
            ('device-support', 'Library/Developer/Xcode/iOS DeviceSupport', 'Review device support versions in Xcode.'),
            ('xcode-archives', 'Library/Developer/Xcode/Archives', 'May contain release builds and debug symbols; review in Xcode Organizer.'),
        ])
        # Images rather than mounted runtime volumes: avoid double counting whole OS trees.
        result.append(Target('simulator-runtimes', Path('/Library/Developer/CoreSimulator/Images'),
                             'Remove unused simulator runtimes through Xcode Settings > Components.', False))
    else:
        review.append(('android-sdk', 'Android/Sdk', 'Uninstall unused SDK versions and system images in Android Studio SDK Manager.'))
    result.extend(Target(category, home / relative, effect, False) for category, relative, effect in review)
    return result


@contextmanager
def open_directory(path: Path):
    """Open every component without following links, including ancestor directories."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def open_child(parent: int, name: str, expected: os.stat_result):
    descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    try:
        actual = os.fstat(descriptor)
        if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
            raise OSError('Directory changed during operation; retry with tools stopped')
        yield descriptor
    finally:
        os.close(descriptor)


def measure(descriptor: int, device: int, seen: set, errors: list[str]) -> tuple[int, int]:
    """Count allocated regular-file bytes once per inode; linked files aren't reclaim estimates."""
    size = estimate = 0
    with os.scandir(descriptor) as entries:
        for entry in entries:
            try:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    continue
                if info.st_dev != device:
                    raise OSError('Mounted filesystem skipped: ' + entry.name)
                if stat.S_ISDIR(info.st_mode):
                    with open_child(descriptor, entry.name, info) as child:
                        child_size, child_estimate = measure(child, device, seen, errors)
                    size += child_size
                    estimate += child_estimate
                elif stat.S_ISREG(info.st_mode):
                    identity = (info.st_dev, info.st_ino)
                    if identity not in seen:
                        seen.add(identity)
                        allocated = info.st_blocks * 512
                        size += allocated
                        if info.st_nlink == 1:
                            estimate += allocated
                else:
                    raise OSError('Special file skipped: ' + entry.name)
            except OSError as exc:
                # Partial measurements must never be presented as complete or applied.
                if len(errors) < 5:
                    errors.append(str(exc))
    return size, estimate


def inspect_target(target: Target) -> dict:
    row: dict = {'category': target.category, 'path': str(target.path), 'cleanable': target.cleanable,
                 'effect': target.effect, 'status': 'missing', 'allocated_bytes': 0,
                 'estimated_reclaimable_bytes': 0, 'errors': []}
    try:
        with open_directory(target.path) as descriptor:
            info = os.fstat(descriptor)
            row['identity'] = [info.st_dev, info.st_ino]
            row['allocated_bytes'], estimate = measure(descriptor, info.st_dev, set(), row['errors'])
            row['estimated_reclaimable_bytes'] = estimate if target.cleanable else 0
            row['status'] = 'error' if row['errors'] else 'ready'
    except FileNotFoundError:
        pass
    except OSError as exc:
        row['status'] = 'error'
        row['errors'].append(str(exc))
    return row


def clear_directory(descriptor: int, device: int) -> None:
    """Remove contents via directory descriptors; preserve the allowlisted root."""
    with os.scandir(descriptor) as entries:
        for entry in entries:
            info = entry.stat(follow_symlinks=False)
            if info.st_dev != device:
                raise OSError('Refusing to remove a mounted filesystem: ' + entry.name)
            if stat.S_ISDIR(info.st_mode):
                with open_child(descriptor, entry.name, info) as child:
                    clear_directory(child, device)
                os.rmdir(entry.name, dir_fd=descriptor)
            elif stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
                os.unlink(entry.name, dir_fd=descriptor)
            else:
                raise OSError('Refusing to remove a special file: ' + entry.name)


def clear_target(target: Target, row: dict) -> None:
    if not target.cleanable:
        raise CommandError('This location is for manual review only: ' + str(target.path))
    with open_directory(target.path) as descriptor:
        info = os.fstat(descriptor)
        if [info.st_dev, info.st_ino] != row['identity']:
            raise CommandError('Cache directory changed since preview: ' + str(target.path))
        clear_directory(descriptor, info.st_dev)


def format_size(size: int) -> str:
    amount = float(size)
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if amount < 1024 or unit == 'TiB':
            return '{:.1f} {}'.format(amount, unit)
        amount /= 1024
    raise AssertionError('unreachable')


def print_report(report: dict) -> None:
    print('Development cache cleanup — ' + ('applied' if report['applied'] else 'preview; nothing deleted'))
    for row in sorted(report['targets'], key=lambda item: item['allocated_bytes'], reverse=True):
        if row['status'] == 'missing':
            continue
        state = row.get('cleanup_status', row['status'])
        mode = 'cache' if row['cleanable'] else 'manual review only'
        print('[{}] {:>10}  {} ({}, {})'.format(state, format_size(row['allocated_bytes']), row['category'], mode, row['path']))
        print('  ' + row['effect'])
        for error in row['errors']:
            print('  ' + error)
    timing = ' before cleanup' if report['applied'] else ''
    print('Estimated reclaimable cache space{} (upper bound): {}'.format(timing, format_size(report['estimated_reclaimable_bytes'])))
    print('Hard-linked files are excluded from the estimate. APFS clones, snapshots, and active tools can reduce actual savings.')
    if report['applied']:
        print('Cache file allocation removed: ' + format_size(report['removed_allocated_bytes']))
    else:
        print('Stop builds, package installs, simulators, and test browsers before cleanup.')
        print('Use --apply to confirm cleanup, --category NAME to select caches, or --all to also review larger data folders.')
    if not report['ok']:
        print('Some locations could not be fully inspected or cleaned; see errors above.')


def clean(args) -> int:
    import json
    import sys

    if platform.system() not in ('Darwin', 'Linux'):
        raise CommandError('Development cache cleanup is supported on macOS and Linux.')
    if args.yes and not args.apply:
        raise CommandError('--yes requires --apply; a preview never deletes anything.')
    if args.json and args.apply and not args.yes:
        raise CommandError('JSON cleanup requires --apply --yes; preview first without --apply.')
    home = Path.home().resolve()
    selected = set(args.category or CATEGORIES)
    candidates = [target for target in targets(home, platform.system())
                  if (target.cleanable and target.category in selected) or (not target.cleanable and args.all)]
    rows = []
    for target in candidates:
        if not args.json:
            print('Scanning ' + str(target.path), file=sys.stderr)
        rows.append(inspect_target(target))
    report = {'applied': False, 'ok': all(row['status'] != 'error' for row in rows), 'targets': rows,
              'estimated_reclaimable_bytes': sum(row['estimated_reclaimable_bytes'] for row in rows if row['status'] == 'ready'),
              'removed_allocated_bytes': 0}
    if args.apply:
        # Validate the complete selection before removing anything. Review-only errors
        # don't prevent cleaning unrelated allowlisted caches.
        if any(row['cleanable'] and row['status'] == 'error' for row in rows):
            if args.json:
                print(json.dumps(report))
            else:
                print_report(report)
            raise CommandError('Cleanup refused: selected caches could not be fully inspected. Narrow --category or fix the errors.')
        actionable = [(target, row) for target, row in zip(candidates, rows) if target.cleanable and row['status'] == 'ready']
        if actionable and not args.yes:
            print_report(report)
            answer = prompt_input('Permanently clear these cache contents? Downloads/rebuilds will be required. [y/N]: ')
            if answer.strip().lower() not in ('y', 'yes'):
                raise CommandError('Cleanup cancelled; nothing deleted.')
        report['applied'] = True
        for target, row in actionable:
            try:
                clear_target(target, row)
                after = inspect_target(target)
                if after['status'] not in ('ready', 'missing'):
                    raise CommandError('Cannot verify cache after cleanup: ' + '; '.join(after['errors']))
                row['remaining_allocated_bytes'] = after['allocated_bytes']
                row['removed_allocated_bytes'] = max(0, row['allocated_bytes'] - after['allocated_bytes'])
                report['removed_allocated_bytes'] += row['removed_allocated_bytes']
                row['cleanup_status'] = 'cleared'
            except (OSError, CommandError) as exc:
                row['cleanup_status'] = 'error'
                row['errors'].append(str(exc))
                report['ok'] = False
    if args.json:
        print(json.dumps(report))
    else:
        print_report(report)
    return 0 if report['ok'] else 1


def register_commands(subparsers) -> None:
    parser = subparsers.add_parser('clean', help='Preview and clear selected development caches; never delete personal data',
                                   description='Preview default development cache locations. Use --apply to remove contents after confirmation.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', help='Preview only (the default)')
    mode.add_argument('--apply', action='store_true', help='Clear selected cache contents after confirmation')
    parser.add_argument('--yes', action='store_true', help='Approve --apply without prompting')
    parser.add_argument('--category', choices=CATEGORIES, action='append', help='Select a cache category; repeat to select several (default: all)')
    parser.add_argument('--all', action='store_true', help='Also measure larger data locations for manual review; they are never deleted')
    parser.add_argument('--json', action='store_true', help='Print a structured report; applying requires --yes')
    parser.set_defaults(func=clean)
