"""Exercise archival/public revision lookup against actual Git trees."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import replay_historical_gpt as replay


class PublicSourceRevisionTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="source-revision-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.git("init", "--initial-branch=main")
        (self.root / "producer.py").write_text("print('recorded producer')\n")
        self.git("add", "producer.py")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-m", "recorded producer")
        self.revision = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        (self.root / "producer.py").write_text("print('different producer')\n")
        self.git("add", "producer.py")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-m", "different producer")
        self.different_revision = self.git("rev-parse", "HEAD")
        self.mapping = {"schema": 1, "revisions": [{
            "archival_commit": replay.PIN, "public_commit": self.revision,
            "archival_tree": self.tree, "public_tree": self.tree}]}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root,
                                       stderr=subprocess.DEVNULL, text=True).strip()

    def resolve(self):
        (self.root / "PUBLIC_SOURCE_REVISIONS.json").write_text(json.dumps(self.mapping))
        with patch.object(replay, "ROOT", self.root):
            return replay.producer_revision()

    def test_resolves_real_public_tree_without_old_commit_object(self):
        missing = subprocess.run(["git", "cat-file", "-e", replay.PIN], cwd=self.root,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(self.resolve(), self.revision)

    def test_rejects_actual_revision_with_different_tree(self):
        self.mapping["revisions"][0]["public_commit"] = self.different_revision
        with self.assertRaisesRegex(ValueError, "pinned archival tree"):
            self.resolve()

    def test_rejects_declared_tree_change(self):
        self.mapping["revisions"][0]["public_tree"] = self.git(
            "rev-parse", self.different_revision + "^{tree}")
        with self.assertRaisesRegex(ValueError, "differs from the archival tree"):
            self.resolve()

    def test_rejects_missing_or_duplicate_archival_mapping(self):
        for rows in [[], self.mapping["revisions"] * 2]:
            with self.subTest(rows=len(rows)):
                self.mapping["revisions"] = rows
                with self.assertRaisesRegex(ValueError, "exactly one"):
                    self.resolve()

    def test_rejects_unknown_map_schema(self):
        self.mapping["schema"] = 2
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.resolve()


if __name__ == "__main__":
    unittest.main()
