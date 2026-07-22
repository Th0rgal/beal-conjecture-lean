#!/usr/bin/env python3
"""Temporary-repository tests for the checkpoint validator's fail-closed rules."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "check_research_checkpoints.py"


class CheckpointValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Checkpoint Test"], cwd=self.root, check=True)
        source = self.root / "stable" / "artifact.txt"
        source.parent.mkdir()
        source.write_bytes(b"historical artifact\n")
        self.git("add", "."); self.git("commit", "-qm", "source")
        self.source = self.git("rev-parse", "HEAD").stdout.decode().strip()
        (self.root / "current.txt").write_text("current\n", encoding="utf-8")
        self.git("add", "."); self.git("commit", "-qm", "current")
        self.base_branch = self.git("branch", "--show-current").stdout.decode().strip()
        self.write_manifest()

    def tearDown(self): self.temp.cleanup()
    def git(self, *args): return subprocess.run(["git", *args], cwd=self.root, check=True, stdout=subprocess.PIPE)
    def manifest(self):
        digest = hashlib.sha256(b"historical artifact\n").hexdigest()
        return {"schema_version": 1, "id": "valid", "status": "historical-source", "source_commit": self.source,
                "artifacts": [{"path": "stable/artifact.txt", "sha256": digest}],
                "verification_commands": [f"git show {self.source}:stable/artifact.txt | sha256sum"],
                "non_claims": ["A checkpoint is not a theorem claim."],
                "trust_boundary_evidence": ["python3 scripts/check_trusted_boundary.py"],
                "validation_evidence": ["python3 scripts/check_research_checkpoints.py"], "last_audit": "2026-07-21"}
    def write_manifest(self, data=None):
        directory = self.root / "Research" / "checkpoints"; directory.mkdir(parents=True, exist_ok=True)
        (directory / "valid.json").write_text(json.dumps(data or self.manifest()), encoding="utf-8")
    def check(self):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def test_valid_historical_checkpoint(self): self.assertEqual(self.check().returncode, 0)
    def test_rejects_bad_hash(self):
        data = self.manifest(); data["artifacts"][0]["sha256"] = "0" * 64; self.write_manifest(data)
        self.assertNotEqual(self.check().returncode, 0)
    def test_rejects_self_reference(self):
        data = self.manifest(); data["source_commit"] = self.git("rev-parse", "HEAD").stdout.decode().strip(); self.write_manifest(data)
        self.assertNotEqual(self.check().returncode, 0)
    def test_rejects_unreachable_commit(self):
        self.git("checkout", "-q", "--orphan", "detached-source")
        (self.root / "orphan.txt").write_text("orphan\n", encoding="utf-8"); self.git("add", "."); self.git("commit", "-qm", "orphan")
        orphan = self.git("rev-parse", "HEAD").stdout.decode().strip(); self.git("checkout", "-q", self.base_branch)
        data = self.manifest(); data["source_commit"] = orphan; self.write_manifest(data)
        self.assertNotEqual(self.check().returncode, 0)
    def test_rejects_schema_status_path_and_duplicate_id(self):
        cases = []
        bad_schema = self.manifest(); bad_schema["schema_version"] = 2; cases.append(bad_schema)
        bad_status = self.manifest(); bad_status["status"] = "claimed-solved"; cases.append(bad_status)
        bad_path = self.manifest(); bad_path["artifacts"][0]["path"] = "../unsafe"; cases.append(bad_path)
        bad_sha = self.manifest(); bad_sha["source_commit"] = "abc"; cases.append(bad_sha)
        for data in cases:
            self.write_manifest(data)
            self.assertNotEqual(self.check().returncode, 0)
        self.write_manifest(self.manifest())
        duplicate = self.manifest(); duplicate["artifacts"] = [{"path": "stable/artifact.txt", "sha256": hashlib.sha256(b"historical artifact\n").hexdigest()}]
        (self.root / "Research" / "checkpoints" / "duplicate.json").write_text(json.dumps(duplicate), encoding="utf-8")
        self.assertNotEqual(self.check().returncode, 0)
    def test_rejects_duplicate_json_key(self):
        manifest = json.dumps(self.manifest())
        manifest = manifest.replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,', 1)
        (self.root / "Research" / "checkpoints" / "valid.json").write_text(manifest, encoding="utf-8")
        self.assertNotEqual(self.check().returncode, 0)


if __name__ == "__main__": unittest.main()
