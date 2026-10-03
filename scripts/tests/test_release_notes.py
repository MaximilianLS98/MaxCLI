"""Exercise release tooling with real disposable Git histories and mocked GitHub calls."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "release_notes.py"
spec = importlib.util.spec_from_file_location("release_notes", SCRIPT)
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Release Test")
        self.git("config", "user.email", "release@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "tag.gpgsign", "false")
        (self.root / "source.py").write_text("# Initial source\n")
        self.commit()
        self.git("tag", "v1.0.0")

    def git(self, *args):
        return notes.git(self.root, *args)

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "-m", "Test change")
        return self.git("rev-parse", "HEAD")

    def entry(self, name="feature.added.md", body="Users can now export their configuration safely."):
        folder = self.root / "release-notes"
        folder.mkdir(exist_ok=True)
        path = folder / name
        path.write_text(body + "\n", encoding="utf-8")
        return path

    def render(self, tag="v1.1.0", ref="HEAD", base=None):
        return notes.render(self.root, ref, tag, base, "owner/repo")

    def test_pr_requires_new_note_including_internal_changes(self):
        with self.assertRaisesRegex(notes.NoteError, "Every PR requires"):
            notes.check(self.root, "main", None)
        self.entry("testing.internal.md", "Refactor test fixtures; no installed CLI behavior changes.")
        self.assertEqual(notes.check(self.root, "main", None), 1)
        self.commit()
        self.assertEqual(notes.check(self.root, "v1.0.0", "HEAD"), 1)
        self.assertIn("no user-facing changes", self.render())
        self.assertNotIn("Refactor test", self.render())

    def test_main_validation_does_not_require_new_note(self):
        self.entry()
        self.assertEqual(notes.check(self.root, None, None), 1)

    def test_existing_entries_cannot_be_edited_deleted_or_renamed(self):
        path = self.entry()
        base = self.commit()
        for operation in ("edit", "delete", "rename"):
            with self.subTest(operation=operation):
                self.git("reset", "--hard", base)
                self.git("clean", "-fd")
                if operation == "edit":
                    path.write_text("Change the historical feature description entirely.\n")
                elif operation == "delete":
                    path.unlink()
                else:
                    path.rename(path.with_name("renamed.added.md"))
                self.entry("new.fixed.md", "Fix a new issue without changing prior release history.")
                with self.assertRaisesRegex(notes.NoteError, "append-only"):
                    notes.check(self.root, base, None)

    def test_merge_base_allows_base_branch_to_gain_other_notes(self):
        self.git("checkout", "-b", "feature")
        self.entry("feature.added.md")
        self.commit()
        self.git("checkout", "main")
        self.entry("parallel.fixed.md", "Fix an unrelated bug on the main branch meanwhile.")
        self.commit()
        self.git("checkout", "feature")
        self.assertEqual(notes.check(self.root, "main", "HEAD"), 1)

    def test_render_uses_committed_target_and_excludes_previous_release(self):
        self.entry("old.added.md", "Previously released behavior must not appear again.")
        self.commit()
        self.git("tag", "v1.1.0")
        self.entry("new.fixed.md", "Fix exporting configuration on computers with Unicode names.")
        self.entry("migration.breaking.md", "Rename the export flag.\n\nUse `--output` instead of `--file`.")
        self.commit()
        self.git("tag", "v1.2.0")
        first = self.render("v1.2.0", "v1.2.0")
        self.entry("later.security.md", "Uncommitted changes must never leak into a published release.")
        self.assertEqual(first, self.render("v1.2.0", "v1.2.0"))
        self.assertNotIn("Previously released", first)
        self.assertNotIn("Uncommitted", first)
        self.assertLess(first.index("Breaking changes"), first.index("Bug fixes"))
        self.assertIn("\n  Use `--output`", first)
        self.assertIn("compare/v1.1.0...v1.2.0", first)

    def test_prereleases_roll_up_since_previous_stable_and_ignore_other_branches(self):
        self.entry("first.added.md", "First feature in this upcoming stable release.")
        self.commit()
        self.git("tag", "v1.1.0-rc.1")
        self.git("checkout", "-b", "unrelated", "v1.0.0")
        (self.root / "unrelated").write_text("other branch")
        self.commit()
        self.git("tag", "v9.0.0")
        self.git("checkout", "main")
        self.entry("second.fixed.md", "Second fix in this upcoming stable release.")
        self.commit()
        self.git("tag", "v1.1.0-rc.2")
        for tag in ("v1.1.0-rc.2", "v1.1.0"):
            with self.subTest(tag=tag):
                rendered = self.render(tag)
                self.assertIn("First feature", rendered)
                self.assertIn("Second fix", rendered)
                self.assertIn("compare/v1.0.0...", rendered)

    def test_numeric_versions_same_commit_tags_and_annotated_tags(self):
        self.entry()
        self.commit()
        self.git("tag", "-a", "v1.9.0", "-m", "Previous stable")
        self.git("tag", "v1.10.0-rc.1")
        self.git("tag", "v1.10.0")
        self.git("tag", "v2.0.0")
        self.assertEqual(notes.previous_tag(self.root, "HEAD", "v1.10.0"), "v1.9.0")
        with self.assertRaisesRegex(notes.NoteError, "No new release-note"):
            self.render("v1.10.0")

    def test_initial_release_without_stable_tags(self):
        self.git("tag", "-d", "v1.0.0")
        self.entry()
        self.commit()
        self.assertIn("export their configuration", self.render("v0.1.0"))
        self.assertNotIn("compare/", self.render("v0.1.0"))

    def test_missing_or_unrelated_baseline_fails(self):
        self.entry()
        self.commit()
        with self.assertRaises(notes.NoteError):
            self.render(base="v99.0.0")
        self.git("checkout", "-b", "other", "v1.0.0")
        (self.root / "other").write_text("Other branch")
        other = self.commit()
        with self.assertRaisesRegex(notes.NoteError, "must be an ancestor"):
            self.render(ref="main", base=other)

    def test_shallow_history_is_rejected(self):
        with tempfile.TemporaryDirectory() as shallow:
            subprocess.run(["git", "clone", "--depth=1", self.root.as_uri(), shallow], check=True, capture_output=True)
            with self.assertRaisesRegex(notes.NoteError, "full history"):
                notes.render(Path(shallow), "HEAD", "v1.1.0", None, None)

    def test_invalid_files_fail_both_worktree_and_snapshot_checks(self):
        for name, body in (
            ("bad.unknown.md", "A sufficiently long description of this change."),
            ("blank.fixed.md", "<!-- Replace this template with your note. -->"),
            ("nested/note.fixed.md", "A valid description in an invalid nested folder."),
        ):
            with self.subTest(name=name):
                self.git("clean", "-fd")
                path = self.root / "release-notes" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body)
                with self.assertRaises(notes.NoteError):
                    notes.entries(self.root)
                self.commit()
                with self.assertRaises(notes.NoteError):
                    notes.entries(self.root, "HEAD")
                self.git("reset", "--hard", "v1.0.0")

    def test_symlinks_rejected(self):
        self.entry().unlink()
        (self.root / "release-notes/link.fixed.md").symlink_to("../source.py")
        for ref in (None, "HEAD"):
            if ref:
                self.commit()
            with self.assertRaisesRegex(notes.NoteError, "regular|symbolic"):
                notes.entries(self.root, ref)

    def test_new_cli_creates_unique_notes_and_rejects_path_traversal(self):
        command = [
            sys.executable,
            str(SCRIPT),
            "new",
            "--type",
            "added",
            "--slug",
            "export-config",
            "--text",
            "Users can export configuration without storing credentials.",
        ]
        first = subprocess.run(command, cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        second = subprocess.run(command, cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        self.assertNotEqual(first, second)
        self.assertTrue((self.root / first).is_file())
        command[command.index("export-config")] = "../escape"
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("lowercase-hyphenated", result.stderr)


class ContentTests(unittest.TestCase):
    def test_placeholders_and_reserved_markers_fail(self):
        for body in (
            "TODO: write the release note before merging.",
            "TBD: explain the internal changes here.",
            "<describe the change to users here>",
            notes.START + "Some otherwise valid release text.",
        ):
            with self.subTest(body=body), self.assertRaises(notes.NoteError):
                notes.validate("change.added.md", body)

    def test_all_documented_types_are_supported(self):
        for category in notes.CATEGORIES:
            self.assertEqual(
                notes.validate(f"change.{category}.md", "Describe a meaningful change or maintenance rationale."), category
            )

    def test_managed_sections_are_idempotent_and_preserve_manual_text(self):
        original = "Installation instructions.\n\n"
        first = notes.managed_body(original, "First generated notes.") + "\n\nThanks to our contributors."
        second = notes.managed_body(first, "Updated generated notes.")
        self.assertTrue(second.startswith(original))
        self.assertTrue(second.endswith("Thanks to our contributors."))
        self.assertNotIn("First generated", second)
        self.assertEqual(second, notes.managed_body(second, "Updated generated notes."))
        for bad in (notes.START, notes.END, notes.END + notes.START, first + notes.START):
            with self.subTest(bad=bad), self.assertRaises(notes.NoteError):
                notes.managed_body(bad, "New notes")

    def test_version_validation(self):
        for tag in ("--help", "v1.2", "v01.2.3", "v1.2.3;echo bad", "v1.2.3\n"):
            with self.subTest(tag=tag), self.assertRaises(notes.NoteError):
                notes.version(tag)
        self.assertEqual(notes.version("v1.2.3-rc.1"), (1, 2, 3))


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("/unused")
        self.resolve = patch.object(notes, "resolve", return_value="sha").start()
        self.api = patch.object(notes, "api").start()
        self.addCleanup(patch.stopall)
        self.url = "https://github.com/owner/repo/releases/tag/v1.2.0"

    def test_new_release_verifies_tag_and_marks_prerelease(self):
        missing = urllib.error.HTTPError("url", 404, "not found", {}, None)
        self.api.side_effect = [{"ref": "refs/tags/v1.2.0-rc.1"}, missing, [], {"html_url": self.url}]
        notes.publish(self.root, "owner/repo", "v1.2.0-rc.1", "Release notes")
        self.assertIn("/git/ref/tags/", self.api.call_args_list[0].args[1])
        payload = self.api.call_args_list[-1].args[2]
        self.assertTrue(payload["prerelease"])
        self.assertEqual(payload["tag_name"], "v1.2.0-rc.1")
        self.assertIn(notes.START, payload["body"])

    def test_existing_release_only_changes_body_and_rerun_does_not_write(self):
        existing = {"id": 12, "body": "Manual installation instructions.", "draft": False, "html_url": self.url}
        self.api.side_effect = [{}, existing, {"html_url": self.url}]
        notes.publish(self.root, "owner/repo", "v1.2.0", "Release notes")
        method, path, payload = self.api.call_args.args
        self.assertEqual((method, path), ("PATCH", "/repos/owner/repo/releases/12"))
        self.assertEqual(set(payload), {"body"})
        self.assertIn("Manual installation instructions.", payload["body"])
        existing["body"] = payload["body"]
        self.api.reset_mock()
        self.api.side_effect = [{}, existing]
        self.assertEqual(notes.publish(self.root, "owner/repo", "v1.2.0", "Release notes"), self.url)
        self.assertEqual(self.api.call_count, 2)

    def test_auth_network_and_missing_remote_tag_errors_never_create_release(self):
        for code, side_effect in ((403, "lookup"), (500, "lookup"), (404, "tag")):
            with self.subTest(code=code, side_effect=side_effect):
                self.api.reset_mock()
                error = urllib.error.HTTPError("url", code, "failure", {}, None)
                self.addCleanup(error.close)
                self.api.side_effect = [error] if side_effect == "tag" else [{}, error]
                with self.assertRaises(urllib.error.HTTPError):
                    notes.publish(self.root, "owner/repo", "v1.2.0", "Notes")
                self.assertTrue(all(call.args[0] == "GET" for call in self.api.call_args_list))

    def test_draft_lookup_is_paginated_and_preserves_draft_state(self):
        missing = urllib.error.HTTPError("url", 404, "not found", {}, None)
        draft = {"id": 23, "tag_name": "v1.2.0", "draft": True, "body": "Draft instructions."}
        self.api.side_effect = [{}, missing, [{"tag_name": "v0.1.0"}] * 100, [draft], {"html_url": self.url}]
        notes.publish(self.root, "owner/repo", "v1.2.0", "Release notes")
        self.assertIn("page=2", self.api.call_args_list[3].args[1])
        method, path, payload = self.api.call_args.args
        self.assertEqual((method, path), ("PATCH", "/repos/owner/repo/releases/23"))
        self.assertEqual(set(payload), {"body"})
        self.assertIn("Draft instructions.", payload["body"])


if __name__ == "__main__":
    unittest.main()
