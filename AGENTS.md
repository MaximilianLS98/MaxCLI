# Agent instructions

## Release notes are part of every change

A task is not complete until its release-note entry is committed with the change.
This applies to every agent and every PR, including fixes, refactors, tests,
documentation, dependencies, and CI work.

1. Add one entry per independently describable change in `release-notes/`.
   Create entries as you implement changes, rather than leaving them to a release agent.
2. Use the helper (Python 3.10+, standard library only):

   ```sh
   python3 scripts/release_notes.py new --type added --slug useful-feature \
     --text 'Describe the concrete behavior users can now rely on.'
   ```

3. Choose `breaking`, `added`, `changed`, `fixed`, `deprecated`, `removed`, or
   `security` for user-facing changes. Explain migration steps in `breaking` notes.
   For changes with no user-facing impact, use `internal` and explain what changed
   **and why no public note is needed**. Internal entries satisfy CI but are omitted
   from the public release body. Do not use them to hide user-visible changes.
4. Edit your new entry into accurate, user-facing Markdown. Do not leave placeholders,
   disclose credentials, or describe unimplemented behavior. No PR number is required.
5. Before committing, run:

   ```sh
   python3 scripts/release_notes.py check --base origin/main
   python3 -m unittest discover -s scripts/tests -v
   ```

   Use the actual target branch instead of `origin/main` for stacked/maintenance PRs.
6. Include the new entry in the commit and mention it in the PR checklist.
   Never edit, rename, or remove entries already present on the target branch;
   add a follow-up correction instead. Entries remain in Git after release.

The `Release notes / validate` CI job rejects missing, malformed, and modified
historical entries. Reviewers must still check that entries cover every change
and that `internal` is appropriate. See [the release guide](docs/RELEASING.md)
for release assembly and maintainer setup.
