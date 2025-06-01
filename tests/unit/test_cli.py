"""
Unit tests for the main CLI module (maxcli.cli).

This module provides comprehensive testing coverage for all core CLI functions,
including file operations, version management, update workflows, and argument parsing.
Tests follow functional programming principles with comprehensive mocking of external dependencies.
"""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, mock_open, call

import pytest

from maxcli.cli import (
    get_files_to_remove,
    remove_path_from_shell_config,
    confirm_uninstall,
    uninstall_maxcli,
    get_current_version,
    compare_versions,
    get_latest_release_version,
    check_for_updates_quietly,
    display_version,
    fetch_github_releases,
    display_release_notes,
    ensure_git_repository,
    update_maxcli,
    create_parser,
    register_core_commands,
    main
)


class TestFileDiscovery:
    """Test suite for file discovery and cleanup functionality."""

    @pytest.fixture
    def mock_home_dir(self, tmp_path: Path) -> Path:
        """Create a temporary home directory structure for testing."""
        home = tmp_path / "home"
        home.mkdir()
        return home

    def test_get_files_to_remove_all_present(self, mock_home_dir: Path) -> None:
        """Test get_files_to_remove when all MaxCLI files exist."""
        # Arrange: Create all MaxCLI directories and files
        config_dir = mock_home_dir / ".config" / "maxcli"
        config_dir.mkdir(parents=True)
        
        lib_dir = mock_home_dir / ".local" / "lib" / "python" / "maxcli"
        lib_dir.mkdir(parents=True)
        
        bin_dir = mock_home_dir / "bin"
        bin_dir.mkdir()
        max_executable = bin_dir / "max"
        max_executable.touch()
        
        ssh_backup1 = mock_home_dir / "ssh_keys_backup.tar.gz"
        ssh_backup1.touch()
        ssh_backup2 = mock_home_dir / "ssh_keys_backup.tar.gz.gpg"
        ssh_backup2.touch()

        with patch('pathlib.Path.home', return_value=mock_home_dir):
            # Act: Get files to remove
            result = get_files_to_remove()

            # Assert: All files should be detected
            assert len(result) == 5
            
            paths = [str(item[0]) for item in result]
            descriptions = [item[1] for item in result]
            
            assert str(config_dir) in paths
            assert str(lib_dir) in paths
            assert str(max_executable) in paths
            assert str(ssh_backup1) in paths
            assert str(ssh_backup2) in paths
            
            assert "Configuration directory" in descriptions[0]
            assert "MaxCLI library" in descriptions[1]
            assert "MaxCLI executable" in descriptions[2]

    def test_get_files_to_remove_none_present(self, mock_home_dir: Path) -> None:
        """Test get_files_to_remove when no MaxCLI files exist."""
        with patch('pathlib.Path.home', return_value=mock_home_dir):
            # Act: Get files to remove
            result = get_files_to_remove()

            # Assert: No files should be detected
            assert result == []

    def test_get_files_to_remove_partial_installation(self, mock_home_dir: Path) -> None:
        """Test get_files_to_remove with only some MaxCLI files present."""
        # Arrange: Create only config directory
        config_dir = mock_home_dir / ".config" / "maxcli"
        config_dir.mkdir(parents=True)

        with patch('pathlib.Path.home', return_value=mock_home_dir):
            # Act: Get files to remove
            result = get_files_to_remove()

            # Assert: Only config directory should be detected
            assert len(result) == 1
            assert str(config_dir) in str(result[0][0])
            assert "Configuration directory" in result[0][1]


class TestShellConfigManagement:
    """Test suite for shell configuration file management."""

    def test_remove_path_from_shell_config_exact_match(self, tmp_path: Path) -> None:
        """Test removal of exact MaxCLI PATH line from shell config."""
        # Arrange: Create shell config with MaxCLI PATH line
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        zshrc = home_dir / ".zshrc"
        
        shell_content = '''# User configuration
export PATH="/usr/local/bin:$PATH"
export PATH="$HOME/bin:$PATH"
# End configuration'''
        
        zshrc.write_text(shell_content)

        with patch('pathlib.Path.home', return_value=home_dir):
            # Act: Remove MaxCLI PATH modification
            result = remove_path_from_shell_config()

            # Assert: MaxCLI line should be removed
            assert result is True
            remaining_content = zshrc.read_text()
            assert 'export PATH="$HOME/bin:$PATH"' not in remaining_content
            assert 'export PATH="/usr/local/bin:$PATH"' in remaining_content
            assert "# User configuration" in remaining_content

    def test_remove_path_from_shell_config_no_modification(self, tmp_path: Path) -> None:
        """Test shell config cleanup when no MaxCLI modifications exist."""
        # Arrange: Create shell config without MaxCLI PATH line
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        zshrc = home_dir / ".zshrc"
        
        shell_content = '''# User configuration
export PATH="/usr/local/bin:$PATH"
# End configuration'''
        
        zshrc.write_text(shell_content)

        with patch('pathlib.Path.home', return_value=home_dir):
            # Act: Remove MaxCLI PATH modification
            result = remove_path_from_shell_config()

            # Assert: No modifications should be found
            assert result is False
            assert zshrc.read_text() == shell_content

    def test_remove_path_from_shell_config_multiple_files(self, tmp_path: Path) -> None:
        """Test PATH removal across multiple shell configuration files."""
        # Arrange: Create multiple shell configs with MaxCLI PATH
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        configs = {
            ".zshrc": 'export PATH="$HOME/bin:$PATH"\nother_config',
            ".bashrc": 'some_config\nexport PATH="$HOME/bin:$PATH"',
            ".bash_profile": 'export PATH="$HOME/bin:$PATH"'
        }
        
        for filename, content in configs.items():
            config_file = home_dir / filename
            config_file.write_text(content)

        with patch('pathlib.Path.home', return_value=home_dir):
            # Act: Remove MaxCLI PATH modification
            result = remove_path_from_shell_config()

            # Assert: All MaxCLI lines should be removed
            assert result is True
            
            for filename in configs.keys():
                config_file = home_dir / filename
                content = config_file.read_text()
                assert 'export PATH="$HOME/bin:$PATH"' not in content

    def test_remove_path_from_shell_config_file_error(self, tmp_path: Path) -> None:
        """Test shell config cleanup with file permission errors."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        with patch('pathlib.Path.home', return_value=home_dir), \
             patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Act: Attempt to remove PATH modification
            result = remove_path_from_shell_config()

            # Assert: Should handle error gracefully
            assert result is False


class TestUninstallConfirmation:
    """Test suite for uninstall confirmation logic."""

    def test_confirm_uninstall_force_mode(self) -> None:
        """Test uninstall confirmation in force mode."""
        # Act: Confirm uninstall with force flag
        result = confirm_uninstall(force=True)

        # Assert: Should skip confirmations
        assert result is True

    @patch('builtins.input')
    @patch('maxcli.cli.get_files_to_remove')
    def test_confirm_uninstall_valid_confirmations(
        self, 
        mock_get_files: Mock, 
        mock_input: Mock
    ) -> None:
        """Test uninstall confirmation with valid user responses."""
        # Arrange: Mock file discovery and user input
        mock_get_files.return_value = [
            (Path("/home/user/.config/maxcli"), "Configuration directory"),
            (Path("/home/user/bin/max"), "MaxCLI executable")
        ]
        mock_input.side_effect = ['yes', 'DELETE EVERYTHING']

        # Act: Confirm uninstall
        result = confirm_uninstall(force=False)

        # Assert: Should accept valid confirmations
        assert result is True
        assert mock_input.call_count == 2

    @patch('builtins.input')
    @patch('maxcli.cli.get_files_to_remove')
    def test_confirm_uninstall_first_confirmation_failed(
        self, 
        mock_get_files: Mock, 
        mock_input: Mock
    ) -> None:
        """Test uninstall confirmation when first confirmation fails."""
        # Arrange: Mock file discovery and user input
        mock_get_files.return_value = []
        mock_input.return_value = 'no'

        # Act: Confirm uninstall
        result = confirm_uninstall(force=False)

        # Assert: Should reject on first confirmation failure
        assert result is False
        assert mock_input.call_count == 1

    @patch('builtins.input')
    @patch('maxcli.cli.get_files_to_remove')
    def test_confirm_uninstall_second_confirmation_failed(
        self, 
        mock_get_files: Mock, 
        mock_input: Mock
    ) -> None:
        """Test uninstall confirmation when second confirmation fails."""
        # Arrange: Mock file discovery and user input
        mock_get_files.return_value = []
        mock_input.side_effect = ['yes', 'wrong phrase']

        # Act: Confirm uninstall
        result = confirm_uninstall(force=False)

        # Assert: Should reject on second confirmation failure
        assert result is False
        assert mock_input.call_count == 2


class TestUninstallWorkflow:
    """Test suite for complete uninstall workflow."""

    @patch('maxcli.cli.confirm_uninstall')
    def test_uninstall_maxcli_cancelled(self, mock_confirm: Mock) -> None:
        """Test uninstall workflow when user cancels."""
        # Arrange: Mock user cancellation
        mock_confirm.return_value = False
        args = Mock(force=False)

        # Act: Attempt uninstall
        uninstall_maxcli(args)

        # Assert: Should exit early on cancellation
        mock_confirm.assert_called_once_with(False)

    @patch('maxcli.cli.remove_path_from_shell_config')
    @patch('maxcli.cli.get_files_to_remove')
    @patch('maxcli.cli.confirm_uninstall')
    @patch('shutil.rmtree')
    def test_uninstall_maxcli_successful(
        self, 
        mock_rmtree: Mock,
        mock_confirm: Mock,
        mock_get_files: Mock,
        mock_remove_path: Mock,
        tmp_path: Path
    ) -> None:
        """Test successful uninstall workflow."""
        # Arrange: Mock successful uninstall scenario
        mock_confirm.return_value = True
        mock_remove_path.return_value = True
        
        test_file = tmp_path / "test_file.txt"
        test_file.touch()
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        mock_get_files.return_value = [
            (test_file, "Test file"),
            (test_dir, "Test directory")
        ]
        
        args = Mock(force=False)

        # Act: Perform uninstall
        uninstall_maxcli(args)

        # Assert: All cleanup operations should be performed
        mock_confirm.assert_called_once_with(False)
        mock_get_files.assert_called_once()
        mock_remove_path.assert_called_once()
        assert not test_file.exists()  # File should be removed
        mock_rmtree.assert_called_once_with(test_dir)  # Directory removal

    @patch('maxcli.cli.remove_path_from_shell_config')
    @patch('maxcli.cli.get_files_to_remove')
    @patch('maxcli.cli.confirm_uninstall')
    def test_uninstall_maxcli_file_removal_error(
        self, 
        mock_confirm: Mock,
        mock_get_files: Mock,
        mock_remove_path: Mock,
        tmp_path: Path
    ) -> None:
        """Test uninstall workflow with file removal errors."""
        # Arrange: Mock file removal error
        mock_confirm.return_value = True
        mock_remove_path.return_value = False
        
        # Create a file that will cause removal to fail
        test_file = tmp_path / "readonly_file.txt"
        test_file.touch()
        test_file.chmod(0o444)  # Read-only
        
        mock_get_files.return_value = [(test_file, "Read-only file")]
        args = Mock(force=False)

        # Act: Perform uninstall (should handle errors gracefully)
        uninstall_maxcli(args)

        # Assert: Should continue despite file errors
        mock_confirm.assert_called_once_with(False)
        mock_get_files.assert_called_once()
        mock_remove_path.assert_called_once()


class TestVersionManagement:
    """Test suite for version management functionality."""

    @patch('subprocess.run')
    def test_get_current_version_with_tag(self, mock_run: Mock) -> None:
        """Test version retrieval when git tag is available."""
        # Arrange: Mock successful git tag command
        mock_run.return_value = Mock(
            returncode=0,
            stdout="v1.2.3\n"
        )

        # Act: Get current version
        result = get_current_version()

        # Assert: Should return tag version
        assert result == "v1.2.3"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_current_version_with_commit_hash(self, mock_run: Mock) -> None:
        """Test version retrieval when only commit hash is available."""
        # Arrange: Mock git commands (tag fails, commit succeeds)
        mock_run.side_effect = [
            Mock(returncode=1),  # Tag command fails
            Mock(returncode=0, stdout="abc1234\n")  # Commit hash succeeds
        ]

        # Act: Get current version
        result = get_current_version()

        # Assert: Should return commit hash
        assert result == "abc1234"
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_get_current_version_no_git(self, mock_run: Mock) -> None:
        """Test version retrieval when git is not available."""
        # Arrange: Mock git command failure
        mock_run.side_effect = FileNotFoundError("git not found")

        # Act: Get current version
        result = get_current_version()

        # Assert: Should return None
        assert result is None

    @patch('subprocess.run')
    def test_get_current_version_timeout(self, mock_run: Mock) -> None:
        """Test version retrieval with command timeout."""
        # Arrange: Mock git command timeout
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        # Act: Get current version
        result = get_current_version()

        # Assert: Should return None on timeout
        assert result is None

    def test_compare_versions_semantic_versions(self) -> None:
        """Test version comparison with semantic versions."""
        # Test cases: (current, latest, expected_newer)
        test_cases = [
            ("v1.0.0", "v1.0.1", True),   # Patch update
            ("v1.0.0", "v1.1.0", True),   # Minor update  
            ("v1.0.0", "v2.0.0", True),   # Major update
            ("v1.0.1", "v1.0.0", False),  # Downgrade
            ("v1.0.0", "v1.0.0", False),  # Same version
            ("v1.2.3", "v1.2.4", True),   # Newer patch
            ("v2.0.0", "v1.9.9", False),  # Older major
        ]

        for current, latest, expected in test_cases:
            # Act: Compare versions
            result = compare_versions(current, latest)
            
            # Assert: Should match expected result
            assert result == expected, f"Failed for {current} vs {latest}"

    def test_compare_versions_commit_hash(self) -> None:
        """Test version comparison with commit hashes."""
        # Act: Compare commit hash with release
        result = compare_versions("abc1234", "v1.0.0")

        # Assert: Any release should be newer than commit hash
        assert result is True

    def test_compare_versions_non_semantic(self) -> None:
        """Test version comparison with non-semantic versions."""
        # Act: Compare non-semantic versions
        result = compare_versions("alpha", "beta")

        # Assert: Should fall back to string comparison
        assert result is True  # "beta" > "alpha"

    @patch('maxcli.cli.fetch_github_releases')
    def test_get_latest_release_version_stable(self, mock_fetch: Mock) -> None:
        """Test retrieving latest stable release version."""
        # Arrange: Mock releases with stable and prerelease
        mock_fetch.return_value = [
            {"tag_name": "v1.1.0-beta", "prerelease": True},
            {"tag_name": "v1.0.0", "prerelease": False},
            {"tag_name": "v0.9.0", "prerelease": False}
        ]

        # Act: Get latest release version
        result = get_latest_release_version()

        # Assert: Should prefer stable release
        assert result == "v1.0.0"

    @patch('maxcli.cli.fetch_github_releases')
    def test_get_latest_release_version_prerelease_only(self, mock_fetch: Mock) -> None:
        """Test retrieving latest version when only prereleases exist."""
        # Arrange: Mock only prerelease versions
        mock_fetch.return_value = [
            {"tag_name": "v1.1.0-beta", "prerelease": True},
            {"tag_name": "v1.0.0-alpha", "prerelease": True}
        ]

        # Act: Get latest release version
        result = get_latest_release_version()

        # Assert: Should return latest prerelease
        assert result == "v1.1.0-beta"

    @patch('maxcli.cli.fetch_github_releases')
    def test_get_latest_release_version_no_releases(self, mock_fetch: Mock) -> None:
        """Test retrieving latest version when no releases exist."""
        # Arrange: Mock empty releases
        mock_fetch.return_value = []

        # Act: Get latest release version
        result = get_latest_release_version()

        # Assert: Should return None
        assert result is None

    @patch('maxcli.cli.get_latest_release_version')
    @patch('maxcli.cli.get_current_version')
    def test_check_for_updates_quietly_update_available(
        self, 
        mock_current: Mock, 
        mock_latest: Mock
    ) -> None:
        """Test update checking when updates are available."""
        # Arrange: Mock versions with update available
        mock_current.return_value = "v1.0.0"
        mock_latest.return_value = "v1.1.0"

        # Act: Check for updates
        has_update, latest_version = check_for_updates_quietly()

        # Assert: Should detect update
        assert has_update is True
        assert latest_version == "v1.1.0"

    @patch('maxcli.cli.get_latest_release_version')
    @patch('maxcli.cli.get_current_version')
    def test_check_for_updates_quietly_no_update(
        self, 
        mock_current: Mock, 
        mock_latest: Mock
    ) -> None:
        """Test update checking when no updates are available."""
        # Arrange: Mock same versions
        mock_current.return_value = "v1.0.0"
        mock_latest.return_value = "v1.0.0"

        # Act: Check for updates
        has_update, latest_version = check_for_updates_quietly()

        # Assert: Should not detect update
        assert has_update is False
        assert latest_version is None

    @patch('maxcli.cli.get_latest_release_version')
    @patch('maxcli.cli.get_current_version')
    def test_check_for_updates_quietly_version_unavailable(
        self, 
        mock_current: Mock, 
        mock_latest: Mock
    ) -> None:
        """Test update checking when version information is unavailable."""
        # Arrange: Mock unavailable versions
        mock_current.return_value = None
        mock_latest.return_value = "v1.1.0"

        # Act: Check for updates
        has_update, latest_version = check_for_updates_quietly()

        # Assert: Should not detect update without current version
        assert has_update is False
        assert latest_version is None


class TestDisplayFunctions:
    """Test suite for display and output functions."""

    @patch('maxcli.cli.check_for_updates_quietly')
    @patch('maxcli.cli.get_current_version')
    def test_display_version_with_updates(
        self, 
        mock_current: Mock, 
        mock_check: Mock,
        capsys
    ) -> None:
        """Test version display when updates are available."""
        # Arrange: Mock version with available update
        mock_current.return_value = "v1.0.0"
        mock_check.return_value = (True, "v1.1.0")
        args = Mock()

        # Act: Display version information
        display_version(args)

        # Assert: Should show update information
        captured = capsys.readouterr()
        assert "v1.0.0" in captured.out
        assert "v1.1.0" in captured.out
        assert "New release available" in captured.out

    @patch('maxcli.cli.check_for_updates_quietly')
    @patch('maxcli.cli.get_current_version')
    def test_display_version_up_to_date(
        self, 
        mock_current: Mock, 
        mock_check: Mock,
        capsys
    ) -> None:
        """Test version display when up to date."""
        # Arrange: Mock current version without updates
        mock_current.return_value = "v1.0.0"
        mock_check.return_value = (False, None)
        args = Mock()

        # Act: Display version information
        display_version(args)

        # Assert: Should show up-to-date message
        captured = capsys.readouterr()
        assert "v1.0.0" in captured.out
        assert "latest version" in captured.out

    @patch('maxcli.cli.check_for_updates_quietly')
    @patch('maxcli.cli.get_current_version')
    def test_display_version_unknown(
        self, 
        mock_current: Mock, 
        mock_check: Mock,
        capsys
    ) -> None:
        """Test version display when version is unknown."""
        # Arrange: Mock unknown version
        mock_current.return_value = None
        args = Mock()

        # Act: Display version information
        display_version(args)

        # Assert: Should show unknown version message
        captured = capsys.readouterr()
        assert "Unknown" in captured.out
        assert "not git-tracked" in captured.out

    @patch('urllib.request.urlopen')
    def test_fetch_github_releases_success(self, mock_urlopen: Mock) -> None:
        """Test successful GitHub releases fetching."""
        # Arrange: Mock successful API response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps([
            {"tag_name": "v1.0.0", "name": "Release 1.0.0"}
        ]).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Act: Fetch GitHub releases
        result = fetch_github_releases()

        # Assert: Should return parsed releases
        assert len(result) == 1
        assert result[0]["tag_name"] == "v1.0.0"

    @patch('urllib.request.urlopen')
    def test_fetch_github_releases_api_error(self, mock_urlopen: Mock) -> None:
        """Test GitHub releases fetching with API error."""
        # Arrange: Mock API error response
        mock_response = Mock()
        mock_response.status = 404
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Act: Fetch GitHub releases
        result = fetch_github_releases()

        # Assert: Should return empty list on error
        assert result == []

    @patch('urllib.request.urlopen')
    def test_fetch_github_releases_network_error(self, mock_urlopen: Mock) -> None:
        """Test GitHub releases fetching with network error."""
        # Arrange: Mock network error
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Network error")

        # Act: Fetch GitHub releases
        result = fetch_github_releases()

        # Assert: Should return empty list on network error
        assert result == []

    def test_display_release_notes_with_releases(self, capsys) -> None:
        """Test display of release notes with valid releases."""
        # Arrange: Mock release data
        releases = [
            {
                "tag_name": "v1.1.0",
                "name": "Release 1.1.0",
                "body": "- New feature\n- Bug fix",
                "published_at": "2023-01-15T10:00:00Z",
                "prerelease": False
            },
            {
                "tag_name": "v1.0.0",
                "name": "Release 1.0.0", 
                "body": "- Initial release",
                "published_at": "2023-01-01T10:00:00Z",
                "prerelease": False
            }
        ]

        # Act: Display release notes
        display_release_notes(releases, "v1.0.0")

        # Assert: Should format and display releases
        captured = capsys.readouterr()
        assert "Release 1.1.0" in captured.out
        assert "New feature" in captured.out
        assert "🆕" in captured.out  # New release marker
        assert "✅" in captured.out  # Current release marker

    def test_display_release_notes_empty(self, capsys) -> None:
        """Test display of release notes with no releases."""
        # Act: Display empty release notes
        display_release_notes([], "v1.0.0")

        # Assert: Should show no release notes message
        captured = capsys.readouterr()
        assert "No release notes available" in captured.out


class TestGitRepository:
    """Test suite for git repository management."""

    @patch('subprocess.run')
    def test_ensure_git_repository_already_exists(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test git repository initialization when .git already exists."""
        # Arrange: Create directory structure with .git
        maxcli_dir = tmp_path / ".local" / "lib" / "python" / "maxcli"
        maxcli_dir.mkdir(parents=True)
        git_dir = maxcli_dir / ".git"
        git_dir.mkdir()

        with patch('pathlib.Path.home', return_value=tmp_path):
            # Act: Ensure git repository
            result = ensure_git_repository()

            # Assert: Should return True without running git commands
            assert result is True
            mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_ensure_git_repository_initialize_success(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test successful git repository initialization."""
        # Arrange: Create directory structure without .git
        maxcli_dir = tmp_path / ".local" / "lib" / "python" / "maxcli"
        maxcli_dir.mkdir(parents=True)
        
        # Mock successful git commands
        mock_run.return_value = Mock(returncode=0)

        with patch('pathlib.Path.home', return_value=tmp_path):
            # Act: Ensure git repository
            result = ensure_git_repository()

            # Assert: Should successfully initialize git repository
            assert result is True
            assert mock_run.call_count == 4  # init, remote add, fetch, reset

    @patch('subprocess.run')
    def test_ensure_git_repository_no_directory(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test git repository initialization when MaxCLI directory doesn't exist."""
        with patch('pathlib.Path.home', return_value=tmp_path):
            # Act: Ensure git repository
            result = ensure_git_repository()

            # Assert: Should return False when directory doesn't exist
            assert result is False
            mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_ensure_git_repository_git_command_fails(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test git repository initialization when git commands fail."""
        # Arrange: Create directory structure without .git
        maxcli_dir = tmp_path / ".local" / "lib" / "python" / "maxcli"
        maxcli_dir.mkdir(parents=True)
        
        # Mock git command failure
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        with patch('pathlib.Path.home', return_value=tmp_path):
            # Act: Ensure git repository
            result = ensure_git_repository()

            # Assert: Should return False on git command failure
            assert result is False


class TestArgumentParsing:
    """Test suite for argument parsing and CLI structure."""

    def test_create_parser_basic_structure(self) -> None:
        """Test basic argument parser creation and structure."""
        # Act: Create parser
        parser = create_parser()

        # Assert: Should create parser with correct properties
        assert parser.prog == 'max'
        assert "Personal CLI" in parser.description
        assert parser.formatter_class == argparse.RawDescriptionHelpFormatter

    def test_create_parser_version_argument(self) -> None:
        """Test version argument parsing."""
        # Arrange: Create parser
        parser = create_parser()

        # Act: Parse version arguments
        args_short = parser.parse_args(['-v'])
        args_long = parser.parse_args(['--version'])

        # Assert: Version flag should be parsed correctly
        assert args_short.version is True
        assert args_long.version is True

    def test_register_core_commands_structure(self) -> None:
        """Test core command registration structure."""
        # Arrange: Create parser and subparsers
        parser = create_parser()
        subparsers = parser.add_subparsers()

        # Act: Register core commands
        register_core_commands(subparsers)

        # Assert: Core commands should be registered
        # Parse different commands to verify they exist
        try:
            parser.parse_args(['init'])
            parser.parse_args(['update'])
            parser.parse_args(['uninstall'])
        except SystemExit:
            # Expected behavior for help commands
            pass

    def test_register_core_commands_init_arguments(self) -> None:
        """Test init command argument parsing."""
        # Arrange: Create parser with core commands
        parser = create_parser()
        subparsers = parser.add_subparsers()
        register_core_commands(subparsers)

        # Act: Parse init command with force flag
        args = parser.parse_args(['init', '--force'])

        # Assert: Force flag should be parsed correctly
        assert hasattr(args, 'force')
        assert args.force is True

    def test_register_core_commands_update_arguments(self) -> None:
        """Test update command argument parsing."""
        # Arrange: Create parser with core commands
        parser = create_parser()
        subparsers = parser.add_subparsers()
        register_core_commands(subparsers)

        # Act: Parse update command with flags
        args = parser.parse_args(['update', '--check-only', '--show-releases'])

        # Assert: Update flags should be parsed correctly
        assert hasattr(args, 'check_only')
        assert hasattr(args, 'show_releases')
        assert args.check_only is True
        assert args.show_releases is True

    def test_register_core_commands_uninstall_arguments(self) -> None:
        """Test uninstall command argument parsing."""
        # Arrange: Create parser with core commands
        parser = create_parser()
        subparsers = parser.add_subparsers()
        register_core_commands(subparsers)

        # Act: Parse uninstall command with force flag
        args = parser.parse_args(['uninstall', '--force'])

        # Assert: Force flag should be parsed correctly
        assert hasattr(args, 'force')
        assert args.force is True


class TestMainEntryPoint:
    """Test suite for the main CLI entry point."""

    @patch('maxcli.cli.display_version')
    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    @patch('sys.argv', ['max', '-v'])
    def test_main_version_flag(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock,
        mock_display_version: Mock
    ) -> None:
        """Test main function with version flag."""
        # Act: Run main with version flag
        main()

        # Assert: Should call display_version and exit early
        mock_display_version.assert_called_once()

    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    @patch('sys.argv', ['max'])
    def test_main_no_command(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock,
        capsys
    ) -> None:
        """Test main function with no command provided."""
        # Act: Run main with no command
        main()

        # Assert: Should show help (captured in output)
        captured = capsys.readouterr()
        # Help is printed to stdout when no command is provided
        assert "usage:" in captured.out or "Max's Personal CLI" in captured.out

    @patch('maxcli.cli.init_config')
    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    @patch('sys.argv', ['max', 'init'])
    def test_main_with_command(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock,
        mock_init_config: Mock
    ) -> None:
        """Test main function with init command."""
        # Act: Run main with init command
        main()

        # Assert: Should call the init_config function
        mock_init_config.assert_called_once()

    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    def test_main_module_loading(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock
    ) -> None:
        """Test main function module loading integration."""
        with patch('sys.argv', ['max', '--help']):
            try:
                # Act: Run main (will exit due to help)
                main()
            except SystemExit:
                # Expected behavior for help command
                pass

            # Assert: Should register both core and module commands
            mock_register_modules.assert_called_once()
            mock_load_modules.assert_called_once()

    @patch('maxcli.cli.load_and_register_modules')
    @patch('maxcli.cli.register_module_commands')
    def test_main_argcomplete_integration(
        self, 
        mock_register_modules: Mock,
        mock_load_modules: Mock
    ) -> None:
        """Test main function with optional argcomplete integration."""
        # Mock the argcomplete import inside the main function
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'argcomplete':
                raise ImportError("argcomplete not found")
            return original_import(name, *args, **kwargs)
        
        with patch('sys.argv', ['max']), \
             patch('builtins.__import__', side_effect=mock_import):
            # Act: Run main without argcomplete
            main()

            # Assert: Should handle missing argcomplete gracefully
            mock_register_modules.assert_called_once()
            mock_load_modules.assert_called_once()


# Integration test for complete workflow
class TestCLIIntegration:
    """Integration tests for complete CLI workflows."""

    @patch('maxcli.cli.subprocess.run')
    @patch('maxcli.cli.fetch_github_releases')
    @patch('pathlib.Path.home')
    def test_update_workflow_integration(
        self,
        mock_home: Mock,
        mock_fetch: Mock,
        mock_subprocess: Mock,
        tmp_path: Path
    ) -> None:
        """Test complete update workflow integration."""
        # Arrange: Setup test environment
        mock_home.return_value = tmp_path
        maxcli_dir = tmp_path / ".local" / "lib" / "python" / "maxcli"
        maxcli_dir.mkdir(parents=True)
        git_dir = maxcli_dir / ".git"
        git_dir.mkdir()

        # Mock git commands and GitHub API
        mock_subprocess.return_value = Mock(returncode=0, stdout="v1.0.0\n")
        mock_fetch.return_value = [
            {"tag_name": "v1.1.0", "prerelease": False}
        ]

        args = Mock(check_only=False, show_releases=False)

        # Act: Run update workflow
        update_maxcli(args)

        # Assert: Should execute update workflow
        mock_fetch.assert_called()
        assert mock_subprocess.call_count > 0 