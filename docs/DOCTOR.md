# Diagnose your environment

```sh
max-dev doctor
max-dev doctor --json
max-dev doctor --all-modules
max-dev doctor --network
```

Doctor is read-only and works before initialization and with a malformed module
configuration. It does not install tools, repair files, switch contexts, or
create configuration. Errors return exit status 1; warnings return 0 when there
are no errors. JSON output includes `ok`, `checks`, `modules`, `contexts`, the
configuration path, installation metadata, and whether network checks ran.

Checks include:

- Python version, stable/development channel, and whether PATH selects the expected launcher.
- Configuration JSON validity and file/directory permissions, without printing stored values.
- Enabled module dependencies, optional tools, and missing implementations.
- Missing project directories and SSH key files (key contents are never read).
- Coolify configuration presence and URL shape, without displaying the token.
- Local GCP, Kubernetes, and Docker context names, using bounded local configuration commands.

`--all-modules` also reports disabled modules. Missing tools for disabled modules
are warnings; a missing required tool for an enabled module is an error.
Readiness means the local prerequisites exist, not that credentials or remote
services have been verified. Optional tools are listed separately because not
every command needs GPG, rsync, or Homebrew.

Network probes are opt-in: `--network` checks the latest GitHub release and the
configured Coolify health endpoint. Default diagnostics make no intentional
network requests. Context probes invoke installed CLIs with local configuration
commands; those tools retain their own implementation behavior.

Use `max-dev doctor` to inspect the development configuration independently of
stable. To examine a specific configuration, set `MAXCLI_CONFIG_DIR=/path`.
