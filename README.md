# MaxCLI

A personal developer CLI for projects, SSH, Docker, cloud environments, and
machine setup. Modules can be enabled independently.

## Install and develop

Requires Python 3.10+ on macOS or Linux.

```sh
# Install the latest published GitHub release as max:
./bootstrap.sh
# Install this checkout alongside stable as max-dev:
./bootstrap.sh --dev "$PWD" --with-dev-tools
export PATH="$HOME/.local/bin:$PATH"

max --version
max-dev --version
```

`max-dev` loads source changes on its next invocation. It has a separate virtual
environment and `~/.config/maxcli-dev` configuration. `max` stays on the installed
GitHub release, even when invoked inside the checkout. Both commands support
the workflows below; use `max-dev` to try your local changes.

See [installation, updates, rollback, and migration](docs/INSTALLATION.md).

## Projects and tasks

```sh
max project add app ~/developer/app --tag personal --editor 'code --wait'
max project list --tag personal
max project open app
# In a project, create .maxcli.json and define argument-array tasks:
max project init
max run dev
max run --project app --dry-run test
```

See [project configuration and environments](docs/PROJECTS.md).

## Environment diagnostics

```sh
max doctor
max doctor --json
max doctor --network  # optional GitHub/Coolify probes
```

See [diagnostic checks and exit codes](docs/DOCTOR.md).

## Configuration and modules

```sh
max config init
max modules list
max modules enable docker_manager gcp_manager
max modules disable gcp_manager
max modules list --json
```

Use the same commands with `max-dev` to configure development independently.
`MAXCLI_CONFIG_DIR` overrides the configuration location; otherwise XDG paths
are used. See [commands in scripts](docs/COMMAND_CONTRACT.md).

| Module | Commands |
| --- | --- |
| SSH | `ssh targets add/list/remove`, `ssh connect`, `ssh generate-keypair`, `ssh backup`, `ssh rsync` |
| Docker | `docker clean --minimal`, `docker clean --extensive` |
| Kubernetes | `kctx CONTEXT` |
| GCP | `gcp config list/create/switch` |
| Coolify | `coolify health/status`, `coolify services`, `coolify applications` |
| Setup | `setup minimal`, `setup dev-full`, `setup apps` |
| Configuration | `config init/backup/restore` |
| OpenClaw | `openclaw status`, `openclaw gateway status/start/stop/restart`, `openclaw logs` |
| Miscellaneous | `process-csv`; `backup-db` and `deploy-app` remain placeholders |

Use `max <command> --help` for exact arguments. SSH, setup, and configuration
modules are enabled by default.

## Development and checks

```sh
./bootstrap.sh --dev "$PWD" --with-dev-tools
~/.local/share/maxcli/development/bin/python -m pytest -o addopts= -q
```

Tests use temporary configuration. Real installation tests are opt-in because
they download a GitHub release and Python packages; see the installation guide.

See [configuration safety, encrypted backups, and previews](docs/CONFIGURATION_SAFETY.md).

Additional documentation: [extensions](docs/extending_maxcli.md),
[Coolify](docs/COOLIFY_README.md), [CSV processing](docs/CSV_PROCESSING_README.md).

## Contributing

Every PR must include a release-note entry. Agents must follow [AGENTS.md](AGENTS.md).
See the [entry format](release-notes/README.md) and [GitHub release guide](docs/RELEASING.md)
for authoring, validation, and automatic release assembly.
