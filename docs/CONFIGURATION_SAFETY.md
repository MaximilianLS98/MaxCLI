# Configuration, credentials, and previews

Configuration writes are atomic. Personal configuration, module state, and SSH
profiles are written with owner-only file permissions (0600), inside a private
configuration directory (0700). Stored secrets are redacted from configuration
initialization output, and secret prompts do not echo their values.

Prefer environment-provided Coolify credentials:

```sh
export MAXCLI_COOLIFY_API_KEY='...'
export MAXCLI_COOLIFY_URL='https://coolify.example.com'
max coolify health
```

Environment values override stored values and are not written to configuration.
Coolify uses an in-process HTTP client with a timeout, checks HTTP failures, and
refuses redirects so authorization headers cannot be forwarded to another host.
Error output does not echo request headers or response bodies.

## Backups and restore

```sh
max config backup --dry-run
max config backup
max config backup --encrypt --recipient YOUR_GPG_KEY_ID
max config restore --backup-file ~/backups/FILE.tar.gz --dry-run
max config restore --backup-file ~/backups/FILE.tar.gz --yes
max config restore --backup-file ~/backups/FILE.tar.gz.gpg --merge --yes
```

Ordinary backups include supported JSON files (`config.json`, module state, SSH
profiles, and project registrations), with recognized password, token, secret,
credential, and API/private-key fields omitted recursively. Ordinary project
registration backups include only names, paths, and tags. Unknown files are not
included. Secret detection is based on field names: do not put secrets in
unrelated fields, paths, tags, or URLs.

Use `--encrypt --recipient` for a GPG-encrypted backup including stored credentials.
GPG must be installed and the recipient's public key must already be available.
Restore requires the corresponding private key; unlock it with your usual GPG
agent before unattended restore. Temporary plaintext stays in private temporary
directories and is removed when the operation finishes. These configuration
backups do not include SSH private keys; the existing `ssh backup` command is
separate.

Restore validates archive paths, types, sizes, and JSON before replacing anything.
Links, devices, traversal paths, duplicate files, and unknown configuration files
are rejected. Existing configuration is moved to a private recovery directory;
failed activation restores that directory. `--merge` recursively applies incoming
values, keeps local-only values, and unions enabled modules. Without `--merge`,
files absent from the archive (including omitted credentials) are absent from the
restored configuration; the recovery copy retains the originals.

Remote backup upload still uses `--target NAME`. For unattended remote restore,
specify both `--target NAME --backup-file BASENAME --yes`. A remote dry-run only
previews the transfer; local dry-run validates the actual archive.

## Preview consequential operations

```sh
max docker clean --extensive --dry-run
max docker clean --extensive --yes
max setup dev-full --dry-run
max setup apps --dry-run
max uninstall --dry-run
```

Docker cleanup asks for confirmation unless `--yes` is supplied; dry-run prints
the exact commands without contacting Docker. Volumes are preserved. Setup
previews describe the profile changes without installing tools. Before replacing
`.zshrc` or `.gitconfig` from a dotfiles repository, setup preserves the original
as a uniquely named `.maxcli-backup-*` file. Source symlinks are rejected.

Uninstall deactivates only the chosen installation channel. It does not erase
configuration, SSH backups, or shell PATH entries.
