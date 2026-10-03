# Bootstrap migration

The former package-copying/Homebrew bootstrap has been replaced by the isolated
stable/development channel installer. See [installation](docs/INSTALLATION.md).

The installer no longer runs Homebrew, modifies shell startup files, or mixes
package downloads with heredoc-generated application code. `test_bootstrap.sh`
checks installer behavior; the opt-in lifecycle test verifies a real released
GitHub package alongside an editable checkout in temporary directories.
