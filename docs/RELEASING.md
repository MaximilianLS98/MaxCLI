# Release notes and GitHub releases

## Contributor and agent contract

Every PR adds a release-note entry, including documentation and maintenance PRs.
[AGENTS.md](../AGENTS.md) is the agent completion contract, and
[release-notes/README.md](../release-notes/README.md) documents the entry format.
The tool needs only Python 3.10+ and Git; it does not install or import MaxCLI.

```sh
python3 scripts/release_notes.py new --type added --slug export-config \
  --text 'Export configuration to a chosen file for easier backups.'
python3 scripts/release_notes.py check --base origin/main
python3 -m unittest discover -s scripts/tests -v
```

Local checks include untracked files. CI checks the committed PR head against its
merge base with the target branch, so unrelated changes on that branch do not
cause false failures. Existing entries cannot be edited, removed, or renamed;
new entries on the PR can be revised freely before merging. A follow-up entry
records any correction to a merged note. Even notes-only PRs need a new entry.

The CI job runs on all PRs, including forks, without path filters or secrets.
It checks entry presence and syntax; reviewers remain responsible for accuracy,
coverage of all changes, and correct use of `internal`.

## Repository enforcement setup

After this workflow is available, add **Release notes / validate** as a required
status check in the repository's ruleset or branch protection for `main` (and
any maintained release branches). Require PRs before merging. Keep any existing
required checks. Without this repository setting, the job reports failure but
GitHub may still allow a merge; administrator bypasses remain a repository policy.
This PR does not change repository protection or Actions permissions.

## Publish a release

There was no automated GitHub release workflow before this system. The new
`GitHub release` workflow supports three entry points:

- Push a version tag such as `v1.1.0` or `v1.1.0-rc.1`: assemble notes and create
  the GitHub release. Prerelease suffixes set GitHub's prerelease flag.
- Publish a release through the GitHub UI: automatically add the generated notes
  to its body, preserving manually written text.
- Run the workflow manually with an **existing** version tag: create a missing
  release or refresh the generated section. Existing drafts remain drafts.

The tag must contain this tooling and its workflow. Historical releases from
before adoption are not rewritten automatically. The workflow checks out the
exact tag, fetches full history, runs tooling tests, and uploads the generated
Markdown as a workflow artifact before publishing. Only the publishing job has
`contents: write`; PR checks have read-only access. The repository must permit
GitHub Actions to write releases using its `GITHUB_TOKEN`.

Example, after merging changes and choosing a version:

```sh
git switch main
git pull --ff-only
git fetch --tags
# Preview the committed changes; this does not create or publish a release.
python3 scripts/release_notes.py render --ref HEAD --version v1.1.0 \
  --repo MaximilianLS98/MaxCLI --output /tmp/maxcli-release-notes.md
# Review the file, then create and push the chosen version tag.
git tag -a v1.1.0 -m 'MaxCLI v1.1.0'
git push origin v1.1.0
```

This workflow manages GitHub release notes. It does not bump package versions,
build/upload packages, or publish to PyPI. Update package versions as appropriate
before tagging. A tag pushed using another workflow's `GITHUB_TOKEN` does not
trigger another workflow; that workflow should explicitly dispatch `release.yml`
with the tag input. See GitHub's [workflow trigger documentation](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow).

## Which entries are included?

Rendering reads Git snapshots, so local uncommitted edits cannot leak into a
release. It selects the highest numerically earlier **stable** `vMAJOR.MINOR.PATCH`
tag reachable from the target commit. Tags on unrelated branches, future
versions, and prerelease tags are excluded as baselines. Annotated and lightweight
tags are both supported, including multiple version tags on the same commit.

Prereleases and their eventual stable release all accumulate entries since the
previous stable release. Thus `v1.1.0-rc.2` and `v1.1.0` include the complete changes
since `v1.0.0`, not just changes since the previous release candidate.

With no earlier stable tag, all entries at the target commit are included. On
adoption, releases include entries recorded since this system was introduced;
older changes are not invented from commit messages. Existing releases/tags
(such as `v1.0.0`) can serve as baselines even though they have no entry directory.

Public entries are grouped in a fixed order, with breaking changes first, and
sorted by filename within each group. Internal-only releases say “Maintenance
release with no user-facing changes.” A range with no new entries fails rather
than silently publishing an empty release. Invalid entries, shallow history,
missing refs, and mutations of baseline entries also fail.

For a special comparison, preview with an explicit ancestor baseline:

```sh
python3 scripts/release_notes.py render --ref v1.2.0 --version v1.2.0 \
  --base v1.0.0 --repo MaximilianLS98/MaxCLI
```

## Reruns and recovery

Generated text is enclosed in `<!-- maxcli-release-notes:start -->` and
`<!-- maxcli-release-notes:end -->`. Reruns replace only that section; text outside
it, release assets, titles, and draft/prerelease settings are preserved. If no
section exists, it is appended. Malformed/duplicate markers fail safely. Avoid
editing inside the section: a rerun will regenerate it. Runs for the same tag are
serialized, and identical notes cause no API update.

If publication fails, inspect the workflow's generated-notes artifact, correct
the underlying problem, then rerun the workflow. Authentication/network errors
are not treated as “release missing.” Both local and remote tags must exist;
the publisher never intentionally creates a tag. Do not retag a published
release to change notes; use a new version or add manual errata outside the
managed section. No cleanup commit or release-note deletion is needed.
