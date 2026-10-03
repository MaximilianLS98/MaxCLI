#!/usr/bin/env python3
"""Create, validate, render, and publish append-only release notes (stdlib only)."""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

DIRECTORY = "release-notes"
CATEGORIES = {
    "breaking": "Breaking changes",
    "added": "New features",
    "changed": "Improvements",
    "fixed": "Bug fixes",
    "deprecated": "Deprecations",
    "removed": "Removals",
    "security": "Security",
    "internal": "Internal changes",
}
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\.([a-z]+)\.md\Z")
VERSION = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*))?\Z")
START = "<!-- maxcli-release-notes:start -->"
END = "<!-- maxcli-release-notes:end -->"


class NoteError(ValueError):
    """An actionable release-note validation error."""


def git(root: Path, *args: str) -> str:
    """Run Git without a shell, raising a readable error on failure."""
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise NoteError(result.stderr.strip() or "Git command failed")
    return result.stdout.rstrip("\n")


def resolve(root: Path, ref: str) -> str:
    """Resolve a ref to a commit, rejecting option injection."""
    return git(root, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")


def version(tag: str) -> tuple[int, int, int]:
    """Validate a version tag and return its numeric release version."""
    match = VERSION.fullmatch(tag)
    if not match:
        raise NoteError(f"Invalid version {tag!r}; use vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-prerelease")
    return int(match[1]), int(match[2]), int(match[3])


def validate(path: str, body: str) -> str:
    """Validate an entry's filename and Markdown; return its category."""
    match = NAME.fullmatch(Path(path).name)
    if not match or match[1] not in CATEGORIES:
        raise NoteError(f"{path}: expected <unique-slug>.<type>.md; types: {', '.join(CATEGORIES)}")
    # Strip comments so a commented template cannot satisfy the requirement.
    visible = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
    if len(visible) < 20 or not re.search(r"[A-Za-z]{3}", visible):
        raise NoteError(f"{path}: write a meaningful description (at least 20 characters)")
    if re.search(r"\b(TODO|TBD|FIXME)\b|<describe[^>]*>", visible, re.I):
        raise NoteError(f"{path}: replace placeholder text with the actual change or internal-change rationale")
    if START in body or END in body:
        raise NoteError(f"{path}: reserved release-note markers are not allowed")
    return match[1]


def entries(root: Path, ref: str | None = None) -> dict[str, str]:
    """Read all notes from a Git snapshot or the working tree, including new files."""
    notes = {}
    if ref is not None:
        sha = resolve(root, ref)
        for record in git(root, "ls-tree", "-r", "-z", sha, "--", DIRECTORY).split("\0"):
            if not record:
                continue
            metadata, path = record.split("\t", 1)
            if path == f"{DIRECTORY}/README.md":
                continue
            mode, kind, blob = metadata.split()
            if mode != "100644" or kind != "blob":
                raise NoteError(f"{path}: notes must be regular, non-executable files")
            notes[path] = git(root, "cat-file", "blob", blob) + "\n"
    else:
        folder = root / DIRECTORY
        for file in sorted(folder.rglob("*")) if folder.exists() else []:
            path = file.relative_to(root).as_posix()
            if path == f"{DIRECTORY}/README.md":
                continue
            if file.is_symlink():
                raise NoteError(f"{path}: notes must not be symbolic links")
            if file.is_dir():
                raise NoteError(f"{path}: put entries directly in {DIRECTORY}/")
            if file.stat().st_mode & 0o111:
                raise NoteError(f"{path}: notes must be non-executable files")
            notes[path] = file.read_text(encoding="utf-8").rstrip("\n") + "\n"
    for path, body in notes.items():
        if Path(path).parent.as_posix() != DIRECTORY:
            raise NoteError(f"{path}: put entries directly in {DIRECTORY}/")
        validate(path, body)
    return notes


def additions(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Require historical entries to be immutable and return new entry paths."""
    for path, body in before.items():
        if after.get(path) != body:
            raise NoteError(f"{path}: existing notes are append-only; restore it and add a new entry")
    return sorted(after.keys() - before.keys())


def check(root: Path, base: str | None, head: str | None) -> int:
    """Validate notes, requiring additions against the PR merge base when supplied."""
    after = entries(root, head)
    if base is None:
        return len(after)
    ancestor = git(root, "merge-base", resolve(root, base), resolve(root, head or "HEAD"))
    added = additions(entries(root, ancestor), after)
    if not added:
        raise NoteError("Every PR requires a new release note. Run: python3 scripts/release_notes.py new --help")
    return len(added)


def previous_tag(root: Path, ref: str, tag: str) -> str | None:
    """Find the highest earlier reachable stable version, never a prerelease."""
    current = version(tag)
    candidates = []
    for candidate in git(root, "tag", "--merged", resolve(root, ref)).splitlines():
        match = VERSION.fullmatch(candidate)
        if match and match[4] is None and version(candidate) < current:
            candidates.append(candidate)
    return max(candidates, key=version) if candidates else None


def render(root: Path, ref: str, tag: str, base: str | None, repository: str | None) -> str:
    """Render only entries added since an ancestor tag, from committed snapshots."""
    version(tag)
    if git(root, "rev-parse", "--is-shallow-repository") == "true":
        raise NoteError("Release rendering needs full history and tags; run git fetch --unshallow --tags")
    target = resolve(root, ref)
    baseline = base if base is not None else previous_tag(root, target, tag)
    before = {}
    if baseline is not None:
        ancestor = resolve(root, baseline)
        if git(root, "merge-base", ancestor, target) != ancestor:
            raise NoteError(f"{baseline}: release baseline must be an ancestor of {ref}")
        before = entries(root, ancestor)
    after = entries(root, target)
    added = additions(before, after)
    if not added:
        raise NoteError("No new release-note entries in this release range; refusing to publish empty notes")
    lines = [f"## What's changed in {tag}", ""]
    public = False
    for category, heading in CATEGORIES.items():
        if category == "internal":
            continue
        bodies = [after[path].strip() for path in added if validate(path, after[path]) == category]
        if bodies:
            public = True
            lines.extend([f"### {heading}", ""])
            for body in bodies:
                lines.extend(["- " + body.replace("\n", "\n  "), ""])
    if not public:
        lines.extend(["Maintenance release with no user-facing changes.", ""])
    if repository:
        validate_repository(repository)
        if baseline:
            url = f"https://github.com/{repository}/compare/{urllib.parse.quote(baseline, safe='')}...{urllib.parse.quote(tag, safe='')}"
            lines.extend([f"[Full changelog]({url})", ""])
    return "\n".join(lines)


def managed_body(existing: str, notes: str) -> str:
    """Replace just our generated section, preserving manually written release text."""
    block = f"{START}\n{notes.strip()}\n{END}"
    if START not in existing and END not in existing:
        return f"{existing.rstrip()}\n\n{block}".lstrip()
    if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(START) > existing.index(END):
        raise NoteError("Release body has malformed generated-section markers; refusing to overwrite it")
    start, end = existing.index(START), existing.index(END) + len(END)
    return existing[:start] + block + existing[end:]


def validate_repository(repository: str) -> None:
    """Require an owner/name repository identifier before constructing API paths."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise NoteError("Repository must be in owner/name format")


def api(method: str, path: str, payload: dict | None = None) -> dict | list:
    """Call GitHub's REST API; only the caller decides whether a 404 is expected."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise NoteError("Set GH_TOKEN or GITHUB_TOKEN to publish release notes")
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not isinstance(result, (dict, list)):
        raise NoteError("Unexpected GitHub API response: expected an object or list")
    return result


def find_release(prefix: str, tag: str) -> dict | None:
    """Find a published release or a draft, including drafts beyond the first page."""
    try:
        release = api("GET", f"{prefix}/releases/tags/{urllib.parse.quote(tag, safe='')}")
        if not isinstance(release, dict):
            raise NoteError("Unexpected GitHub release response")
        return release
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        error.close()
    # The tag lookup only returns published releases. Writers can discover drafts
    # through the list endpoint; never publish a second release over an existing draft.
    page = 1
    while True:
        releases = api("GET", f"{prefix}/releases?per_page=100&page={page}")
        if not isinstance(releases, list) or any(not isinstance(release, dict) for release in releases):
            raise NoteError("Unexpected GitHub release list response")
        for release in releases:
            if isinstance(release, dict) and release["tag_name"] == tag:
                return release
        if len(releases) < 100:
            return None
        page += 1


def release_url(release: dict | list) -> str:
    """Extract the URL from a verified release object."""
    url = release.get("html_url") if isinstance(release, dict) else None
    if not isinstance(url, str):
        raise NoteError("Unexpected GitHub release response: missing html_url")
    return url


def publish(root: Path, repository: str, tag: str, notes: str) -> str:
    """Create a release for an existing tag or idempotently refresh its notes."""
    version(tag)
    validate_repository(repository)
    resolve(root, f"refs/tags/{tag}")
    prefix = f"/repos/{repository}"
    # Verify the remote tag as well; the release API otherwise silently creates tags.
    api("GET", f"{prefix}/git/ref/tags/{urllib.parse.quote(tag, safe='')}")
    existing = find_release(prefix, tag)
    if existing is not None:
        body = managed_body(existing.get("body") or "", notes)
        if body == (existing.get("body") or ""):
            return release_url(existing)
        release = api("PATCH", f"{prefix}/releases/{existing['id']}", {"body": body})
    else:
        release = api(
            "POST",
            f"{prefix}/releases",
            {
                "tag_name": tag,
                "name": tag,
                "body": managed_body("", notes),
                "prerelease": "-" in tag,
            },
        )
    return release_url(release)


def main() -> int:
    """Expose dependency-free authoring, PR validation, preview, and publishing commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="Create a uniquely named note; no PR number needed")
    new.add_argument("--type", choices=CATEGORIES, required=True)
    new.add_argument("--slug", required=True, help="Short lowercase-hyphenated change name")
    new.add_argument("--text", required=True, help="User-facing Markdown, or rationale for an internal change")
    validate_parser = sub.add_parser("check", help="Validate all entries and optionally require a new PR entry")
    validate_parser.add_argument("--base", help="PR base ref; compared from the merge base")
    validate_parser.add_argument("--head", help="Check a committed snapshot instead of the working tree")
    preview = sub.add_parser("render", help="Render committed entries since the previous stable version")
    preview.add_argument("--ref", default="HEAD")
    preview.add_argument("--version", required=True)
    preview.add_argument("--base", help="Override the previous stable tag (must be an ancestor)")
    preview.add_argument("--repo", help="owner/name for a full-changelog link")
    preview.add_argument("--output", type=Path)
    upload = sub.add_parser("publish", help="Publish a rendered notes file to an existing GitHub tag")
    upload.add_argument("--tag", required=True)
    upload.add_argument("--repo", required=True)
    upload.add_argument("--notes", required=True, type=Path)
    args = parser.parse_args()
    try:
        root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
        if args.command == "new":
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
                raise NoteError("Use a lowercase-hyphenated --slug")
            name = f"{args.slug}-{uuid.uuid4().hex[:12]}.{args.type}.md"
            path = f"{DIRECTORY}/{name}"
            validate(path, args.text)
            (root / DIRECTORY).mkdir(exist_ok=True)
            with (root / path).open("x", encoding="utf-8") as stream:
                stream.write(args.text.strip() + "\n")
            print(path)
        elif args.command == "check":
            count = check(root, args.base, args.head)
            print(f"Release notes valid: {count} {'new ' if args.base else ''}entries")
        elif args.command == "render":
            notes = render(root, args.ref, args.version, args.base, args.repo)
            if args.output:
                args.output.write_text(notes, encoding="utf-8")
            else:
                print(notes, end="")
        elif args.command == "publish":
            notes = args.notes.read_text(encoding="utf-8").strip()
            if not notes or START in notes or END in notes:
                raise NoteError("Notes file must contain rendered Markdown without managed-section markers")
            print(publish(root, args.repo, args.tag, notes))
    except (NoteError, OSError, UnicodeError, urllib.error.URLError) as error:
        print(f"Release notes error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
