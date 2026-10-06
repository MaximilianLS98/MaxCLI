# Commands in scripts

MaxCLI exits 0 on success, nonzero on failure, and 130 when interrupted. Errors
are written to stderr. External command failures retain their exit status.

Use `max --non-interactive <command>` to prohibit MaxCLI prompts. This behavior
is also enabled when stdin is not a terminal. External tools (SSH, cloud login,
etc.) may have their own interactive behavior; pass their explicit credentials
or use those tools directly for unattended authentication.

Structured output is available on `max modules list --json` and
`max ssh targets list --json`, as well as `max clean --json`. Cleanup previews
by default; unattended removal requires `max --non-interactive clean --apply --yes`.
See [cleanup reports and failure behavior](CLEANUP.md). Unsupported JSON options fail during parsing.
Module enabling accepts multiple names and validates them before changing state.

`max init` is an alias for `max config init`. A malformed module configuration
is preserved and reported as an error rather than silently replaced.

Configuration defaults to `$XDG_CONFIG_HOME/maxcli` (or `~/.config/maxcli`).
`MAXCLI_CONFIG_DIR=/absolute/path` overrides the entire configuration directory,
including SSH profiles and configuration backups. This is useful for tests and
isolated development. It does not sandbox external tools or redirect SSH keys.
