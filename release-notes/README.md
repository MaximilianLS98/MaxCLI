# Release-note entries

Every PR adds at least one `<unique-slug>.<type>.md` file here. Each file describes
one change in plain Markdown, without YAML headers or a top-level heading.

```sh
python3 scripts/release_notes.py new --type fixed --slug export-paths \
  --text 'Fix configuration exports when the destination path contains spaces.'
```

The helper adds a random suffix so independent agents do not collide. Edit the
resulting file if it needs more detail. Entries must contain at least 20 visible
characters, with no TODO/TBD/FIXME placeholders. All entries are UTF-8 regular,
non-executable files directly in this directory. `README.md` is not an entry.

| Type | Use for |
| --- | --- |
| `breaking` | Incompatible behavior; include migration instructions |
| `added` | New capabilities |
| `changed` | Improvements to existing behavior |
| `fixed` | Bug fixes |
| `deprecated` | Features scheduled for removal and their replacements |
| `removed` | Removed features |
| `security` | Security improvements suitable for public disclosure |
| `internal` | Maintenance with no user-facing effect; explain the rationale |

Write from the user's perspective: what changed, who benefits, and any action
needed. For multi-paragraph notes, write ordinary Markdown; the renderer indents
continuation lines into the same bullet. Do not include generated-section markers.

Entries are append-only once merged. Do not delete them after a release: the
renderer compares the previous stable tag with the release commit to find new
entries. Internal entries are validated and retained but excluded from public
notes. See [agent instructions](../AGENTS.md) and [release guide](../docs/RELEASING.md).
