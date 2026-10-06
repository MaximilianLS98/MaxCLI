"""Cleanup safety tests use disposable trees, never the user's caches."""
import argparse
import json
import os
from unittest.mock import Mock, patch

import pytest

from maxcli import cleanup
from maxcli.runtime import CommandError, NON_INTERACTIVE


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(cleanup.Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(cleanup.platform, 'system', lambda: 'Darwin')
    return tmp_path


def arguments(*argv):
    parser = argparse.ArgumentParser()
    cleanup.register_commands(parser.add_subparsers())
    return parser.parse_args(['clean', *argv])


def cache_file(home, relative='.npm/_cacache/content/package'):
    path = home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'package' * 2048)
    return path


def test_default_preview_and_dry_run_never_modify_caches(sandbox, capsys):
    path = cache_file(sandbox)
    original = path.read_bytes()
    for flags in ([], ['--dry-run']):
        assert cleanup.clean(arguments(*flags)) == 0
        assert path.read_bytes() == original
        assert 'nothing deleted' in capsys.readouterr().out
    assert not (sandbox / '.config').exists()


def test_json_preview_reports_allocation_and_no_prompts(sandbox, capsys, monkeypatch):
    path = cache_file(sandbox)
    monkeypatch.setattr(cleanup, 'prompt_input', Mock(side_effect=AssertionError('Unexpected prompt')))
    assert cleanup.clean(arguments('--category', 'npm', '--json')) == 0
    captured = capsys.readouterr()
    assert not captured.err
    report = json.loads(captured.out)
    assert not report['applied']
    assert len(report['targets']) == 1
    assert report['targets'][0]['allocated_bytes'] == path.stat().st_blocks * 512
    assert report['estimated_reclaimable_bytes'] == path.stat().st_blocks * 512


def test_apply_removes_only_selected_contents_and_preserves_cache_root(sandbox, capsys):
    npm = cache_file(sandbox)
    bun = cache_file(sandbox, '.bun/install/cache/package/file')
    credentials = cache_file(sandbox, '.npmrc')
    project = cache_file(sandbox, 'project/node_modules/package/file')
    gradle_config = cache_file(sandbox, '.gradle/gradle.properties')
    root = sandbox / '.npm/_cacache'
    assert cleanup.clean(arguments('--category', 'npm', '--apply', '--yes', '--json')) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['applied']
    assert report['removed_allocated_bytes'] > 0
    assert root.is_dir() and list(root.iterdir()) == []
    assert not npm.exists()
    assert all(path.exists() for path in (bun, credentials, project, gradle_config))


def test_repeated_categories_and_protected_locations(sandbox, capsys):
    npm = cache_file(sandbox)
    bun = cache_file(sandbox, '.bun/install/cache/package/file')
    protected = [cache_file(sandbox, relative) for relative in (
        '.android/avd/device/userdata', 'Library/Android/sdk/system-images/image',
        'Library/Developer/CoreSimulator/Devices/device/data', 'Library/pnpm/store/package/index',
        'Library/Application Support/app/database', 'Library/Developer/Xcode/Archives/app/archive',
    )]
    # The real system runtime path is not part of this disposable home.
    original_targets = cleanup.targets
    def local_targets(home, system):
        return [t for t in original_targets(home, system) if t.path.is_relative_to(home)]

    with patch.object(cleanup, 'targets', local_targets):
        assert cleanup.clean(arguments('--all', '--category', 'npm', '--category', 'bun', '--apply', '--yes')) == 0
    capsys.readouterr()
    assert not npm.exists() and not bun.exists()
    assert all(path.exists() for path in protected)


def test_confirmation_decline_and_noninteractive_fail_before_deleting(sandbox, monkeypatch, capsys):
    path = cache_file(sandbox)
    with monkeypatch.context() as context:
        context.setattr(cleanup, 'prompt_input', lambda prompt: 'no')
        with pytest.raises(CommandError, match='cancelled'):
            cleanup.clean(arguments('--category', 'npm', '--apply'))
    assert path.exists()
    token = NON_INTERACTIVE.set(True)
    try:
        with pytest.raises(CommandError, match='requires input'):
            cleanup.clean(arguments('--category', 'npm', '--apply'))
    finally:
        NON_INTERACTIVE.reset(token)
    assert path.exists()


def test_confirmation_accepts_explicit_yes(sandbox, monkeypatch, capsys):
    path = cache_file(sandbox)
    monkeypatch.setattr(cleanup, 'prompt_input', lambda prompt: 'yes')
    assert cleanup.clean(arguments('--category', 'npm', '--apply')) == 0
    assert not path.exists()


def test_links_inside_cache_are_unlinked_without_following(sandbox, capsys):
    path = cache_file(sandbox)
    outside = cache_file(sandbox, 'personal/important.txt')
    root = sandbox / '.npm/_cacache'
    (root / 'outside').symlink_to(outside.parent, target_is_directory=True)
    (root / 'loop').symlink_to(root, target_is_directory=True)
    (root / 'broken').symlink_to(sandbox / 'missing')
    before = outside.read_bytes()
    assert cleanup.clean(arguments('--category', 'npm', '--apply', '--yes')) == 0
    assert outside.read_bytes() == before
    assert not path.exists()
    assert list(root.iterdir()) == []


@pytest.mark.parametrize('linked_component', ['.npm', '.npm/_cacache'])
def test_linked_cache_root_or_ancestor_refuses_cleanup(sandbox, linked_component, capsys):
    outside = cache_file(sandbox, 'personal/_cacache/important.txt')
    link = sandbox / linked_component
    link.parent.mkdir(parents=True, exist_ok=True)
    destination = outside.parent.parent if linked_component == '.npm' else outside.parent
    link.symlink_to(destination, target_is_directory=True)
    with pytest.raises(CommandError, match='could not be fully inspected'):
        cleanup.clean(arguments('--category', 'npm', '--apply', '--yes'))
    assert outside.exists()


def test_hardlinks_are_counted_once_and_not_promised_as_reclaimable(sandbox, capsys):
    outside = cache_file(sandbox, 'project/node_modules/package/file')
    root = sandbox / '.npm/_cacache'
    root.mkdir(parents=True)
    os.link(outside, root / 'package')
    os.link(outside, root / 'duplicate')
    target = cleanup.Target('npm', root, 'Download again.')
    row = cleanup.inspect_target(target)
    assert row['allocated_bytes'] == outside.stat().st_blocks * 512
    assert row['estimated_reclaimable_bytes'] == 0
    cleanup.clear_target(target, row)
    assert outside.exists()


def test_replaced_cache_root_is_rejected(sandbox):
    path = cache_file(sandbox)
    root = sandbox / '.npm/_cacache'
    target = cleanup.Target('npm', root, 'Download again.')
    row = cleanup.inspect_target(target)
    root.rename(root.with_name('original'))
    replacement = cache_file(sandbox)
    with pytest.raises(CommandError, match='changed since preview'):
        cleanup.clear_target(target, row)
    assert replacement.exists()
    assert root.with_name('original').joinpath(path.relative_to(root)).exists()


def test_partial_scan_refuses_entire_selection(sandbox, monkeypatch, capsys):
    npm = cache_file(sandbox)
    bun = cache_file(sandbox, '.bun/install/cache/package/file')
    original = cleanup.open_child

    def unreadable(parent, name, info):
        if name == 'content':
            raise PermissionError('Cache is unreadable')
        return original(parent, name, info)

    monkeypatch.setattr(cleanup, 'open_child', unreadable)
    with pytest.raises(CommandError, match='could not be fully inspected'):
        cleanup.clean(arguments('--category', 'npm', '--category', 'bun', '--apply', '--yes', '--json'))
    report = json.loads(capsys.readouterr().out)
    assert not report['ok'] and not report['applied']
    assert npm.exists() and bun.exists()


def test_deletion_failure_is_reported_without_claiming_success(sandbox, monkeypatch, capsys):
    path = cache_file(sandbox)
    monkeypatch.setattr(cleanup, 'clear_target', Mock(side_effect=PermissionError('Cannot remove cache')))
    assert cleanup.clean(arguments('--category', 'npm', '--apply', '--yes', '--json')) == 1
    report = json.loads(capsys.readouterr().out)
    assert not report['ok']
    assert report['targets'][0]['cleanup_status'] == 'error'
    assert report['removed_allocated_bytes'] == 0
    assert path.exists()


def test_review_only_targets_cannot_be_removed(sandbox):
    path = cache_file(sandbox, '.android/avd/device/userdata')
    target = cleanup.Target('android-devices', path.parent, 'Review manually.', False)
    with pytest.raises(CommandError, match='manual review only'):
        cleanup.clear_target(target, cleanup.inspect_target(target))
    assert path.exists()


def test_non_default_environment_paths_are_never_targeted(sandbox, monkeypatch):
    for variable in ('GRADLE_USER_HOME', 'BUN_INSTALL_CACHE_DIR', 'XDG_CACHE_HOME', 'PNPM_HOME'):
        monkeypatch.setenv(variable, str(sandbox / 'personal'))
    assert all(target.path != sandbox / 'personal' for target in cleanup.targets(sandbox, 'Darwin'))


def test_linux_uses_linux_cache_locations(sandbox):
    entries = cleanup.targets(sandbox, 'Linux')
    assert any(target.path == sandbox / '.cache/pnpm' and target.cleanable for target in entries)
    assert any(target.path == sandbox / '.cache/ms-playwright' and target.cleanable for target in entries)
    assert not any('Library' in target.path.parts for target in entries)


def test_invalid_modes_and_unknown_category_do_not_run(sandbox):
    path = cache_file(sandbox)
    with pytest.raises(SystemExit):
        arguments('--apply', '--dry-run')
    with pytest.raises(SystemExit):
        arguments('--category', 'app-data')
    with pytest.raises(CommandError, match='requires --apply --yes'):
        cleanup.clean(arguments('--apply', '--json'))
    with pytest.raises(CommandError, match='requires --apply'):
        cleanup.clean(arguments('--yes'))
    assert path.exists()


def test_missing_caches_are_not_created(sandbox, capsys):
    assert cleanup.clean(arguments('--category', 'npm', '--apply', '--yes')) == 0
    assert list(sandbox.iterdir()) == []


def test_directory_swapped_for_link_during_scan_is_not_followed(sandbox, monkeypatch, capsys):
    path = cache_file(sandbox)
    outside = cache_file(sandbox, 'personal/important.txt')
    original = cleanup.open_child

    def swap(parent, name, info):
        if name == 'content':
            path.parent.rename(path.parent.with_name('old-content'))
            path.parent.symlink_to(outside.parent, target_is_directory=True)
        return original(parent, name, info)

    monkeypatch.setattr(cleanup, 'open_child', swap)
    assert cleanup.clean(arguments('--category', 'npm', '--json')) == 1
    assert outside.exists()
    assert not json.loads(capsys.readouterr().out)['ok']
