# Stable releases and live development

MaxCLI requires Python 3.10+ on macOS or Linux. Installation only sets up MaxCLI;
it does not install Homebrew, applications, or change shell configuration.

## Install the stable GitHub release

```sh
./bootstrap.sh
# Or, without cloning:
curl -fsSL https://raw.githubusercontent.com/MaximilianLS98/MaxCLI/main/bootstrap.sh | bash
```

The installer resolves the latest published, non-prerelease GitHub release and
installs that tag into a dedicated virtual environment. It never installs `main`
as the stable CLI. To pin an existing release:

```sh
./bootstrap.sh --version v2.0.0
```

Add `~/.local/bin` before older installations in your shell PATH:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Persist that line in your shell configuration if needed. Verify with `command -v
max` and `max --version`. If a different executable already occupies the target
path, installation stops. `--replace-existing` backs it up before replacement.
An older `~/bin/max` is left intact; PATH order decides which command runs.

## Migrate an older installation to v2

MaxCLI 2 requires Python 3.10 or newer. If your `max` comes from the old
bootstrap installer, run the current `bootstrap.sh` once to adopt the managed
installation, then put `~/.local/bin` first on PATH and run `hash -r`.
Use `--replace-existing` only if the installer reports a conflicting executable;
it saves that executable before replacing it. Existing configuration is retained.
Verify `max --version --json` reports the `stable` channel and release `v2.0.0`.
Subsequent upgrades use `max update`; existing managed installations can use
`max update` immediately.

Development now uses the separate `max-dev` command and configuration directory.
Rerun the development bootstrap below to associate it with your checkout.
Plain configuration backups omit recognized secret fields; use an encrypted
backup when you need to preserve credentials. See [configuration safety](CONFIGURATION_SAFETY.md).

## Develop alongside stable

From your checkout:

```sh
./bootstrap.sh --dev "$PWD" --with-dev-tools
max-dev --version
max-dev project list
max --version
```

| Command | Code | Default configuration |
| --- | --- | --- |
| `max` | Published GitHub release | `~/.config/maxcli` |
| `max-dev` | Editable local checkout | `~/.config/maxcli-dev` |

Python source edits are picked up on the **next invocation**, without a build or
reinstall. This is command-by-command reload, not a watcher restarting already
running tasks. After dependency, entry-point, or package metadata changes, rerun
`bootstrap.sh --dev`. Each channel has its own virtual environment. No activation
is needed. Isolated Python launch (`-I`) prevents the current checkout or
`PYTHONPATH` from shadowing the stable package.

Run tests using the development interpreter:

```sh
~/.local/share/maxcli/development/bin/python -m pytest -o addopts= -q
# Explicitly include the real GitHub download/editable-install lifecycle test:
MAXCLI_RUN_INSTALL_TESTS=1 ~/.local/share/maxcli/development/bin/python -m pytest -o addopts= tests/integration/test_installation_lifecycle.py
```

Alternatively `./max --help` runs the checkout directly with system Python and
the development configuration directory. It is useful before installation; it
does not install dependencies. `python -m maxcli` also works, but uses normal
configuration unless `MAXCLI_CONFIG_DIR` is set.

`XDG_CONFIG_HOME` is respected. Override the entire configuration directory with
`MAXCLI_CONFIG_DIR=/path`. Sharing stable configuration with development is
explicit, e.g. `MAXCLI_CONFIG_DIR="$HOME/.config/maxcli" max-dev modules list`.
Configuration isolation does not sandbox tasks, cloud credentials, SSH keys,
Docker, or other external tools.

## Updates and rollback

```sh
max --version                  # offline; shows channel and installed release
max --version --json
max update --check-only
max update --show-releases
max update                     # install latest published stable release
max update --version v2.0.0    # explicit pin/downgrade
max update --rollback
```

Updates build and smoke-test a new environment before switching the channel's
symlink. Failed builds leave the active release intact. The previous environment
is retained for rollback; older environments are also retained on disk. No git
reset, checkout mutation, or copying over a running package occurs. The launcher
handles lifecycle commands even when the installed release predates this system.
`max-dev update` explains how to refresh development dependencies and does not
change the checkout or stable installation.

`max uninstall --dry-run` previews deactivation. `max uninstall --force` removes
only the managed stable launcher and active pointer. `max-dev uninstall --force`
does the same for development. Configuration, SSH keys, backups, and retained
environments are preserved; shell configuration is never edited. Use the package
manager for removal of an unmanaged installation.

Advanced: `--root /path` relocates managed environments, `--bin-dir /path` chooses
the launcher directory, and `--github-repo OWNER/REPO` chooses the release source.
Only run installers or editable checkouts you trust.

Implementation references: [pip editable installs](https://pip.pypa.io/en/stable/topics/local-project-installs/)
and [Python isolated mode](https://docs.python.org/3.10/using/cmdline.html#cmdoption-I).
