import json
from pathlib import Path
from unittest.mock import Mock
import pytest

from maxcli import doctor


@pytest.fixture
def diagnostics(tmp_path, monkeypatch):
    root = tmp_path / 'config'
    monkeypatch.setattr(doctor, 'config_dir', lambda: root)
    monkeypatch.setattr(doctor, 'current_installation', lambda: None)
    monkeypatch.setattr(doctor, 'version_info', lambda: {'channel': 'unmanaged'})
    monkeypatch.setattr(doctor.shutil, 'which', lambda tool: '/fake/' + tool)
    monkeypatch.delenv('MAXCLI_COOLIFY_API_KEY', raising=False)
    monkeypatch.delenv('MAXCLI_COOLIFY_URL', raising=False)
    return root


def test_offline_diagnostics_are_read_only(diagnostics, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Network was used in offline doctor')
    monkeypatch.setattr(doctor, 'release_info', forbidden)
    report = doctor.inspect_environment()
    assert report['ok']
    assert not report['network_checked']
    assert not diagnostics.exists()


def test_missing_enabled_dependency_is_an_error(diagnostics, monkeypatch):
    diagnostics.mkdir()
    (diagnostics / 'modules_config.json').write_text('{"enabled_modules":["docker_manager"]}')
    monkeypatch.setattr(doctor.shutil, 'which', lambda tool: None)
    report = doctor.inspect_environment()
    assert not report['ok']
    assert report['modules'][0]['missing_required'] == ['docker']
    assert report['modules'][0]['enabled'] and not report['modules'][0]['ready']


def test_broken_config_and_secret_values_are_not_echoed(diagnostics):
    diagnostics.mkdir()
    bad = diagnostics / 'modules_config.json'
    bad.write_text('{broken')
    (diagnostics / 'config.json').write_text('{"coolify_api_key":"NEVER-ECHO"}')
    report = doctor.inspect_environment()
    assert not report['ok']
    assert 'NEVER-ECHO' not in json.dumps(report)
    assert bad.read_text() == '{broken'


def test_context_queries_are_bounded_and_local(diagnostics, monkeypatch):
    diagnostics.mkdir()
    (diagnostics / 'modules_config.json').write_text('{"enabled_modules":["docker_manager","kubernetes_manager","gcp_manager"]}')
    execute = Mock(return_value=Mock(returncode=0, stdout='development\n'))
    monkeypatch.setattr(doctor.subprocess, 'run', execute)
    report = doctor.inspect_environment()
    assert report['contexts'] == {'docker': 'development', 'kubernetes': 'development', 'gcp': 'development'}
    assert execute.call_count == 3
    assert all(call.kwargs['timeout'] == 5 for call in execute.call_args_list)


def test_network_requires_opt_in(diagnostics, monkeypatch):
    request = Mock(return_value={'tag_name': 'v2.0.0'})
    monkeypatch.setattr(doctor, 'release_info', request)
    report = doctor.inspect_environment(network=True)
    request.assert_called_once()
    assert report['network_checked']
    assert any(check['name'] == 'network:github' for check in report['checks'])


def test_enabled_coolify_reports_unconfigured_state(diagnostics):
    diagnostics.mkdir()
    (diagnostics / 'modules_config.json').write_text('{"enabled_modules":["coolify_manager"]}')
    report = doctor.inspect_environment()
    assert not report['ok']
    assert not report['modules'][0]['ready']
    assert any(check['name'] == 'coolify-config' and check['status'] == 'error' for check in report['checks'])
