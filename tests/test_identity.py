import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from verified_pipeline.cli import main
from verified_pipeline.identity import sha256_file, stage_run_id


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "schema_version": 1,
            "stage": "render",
            "code_commits": {"pipeline": "a" * 40, "tools": "b" * 40},
            "input_sha256": {"mesh": "c" * 64},
            "parameters": {"fps": 30, "settings": {"size": 0.7}},
            "upstream_run_ids": [],
        }

    def test_order_independent_and_sensitive_to_material_change(self):
        same = json.loads(json.dumps(self.spec, sort_keys=True))
        self.assertEqual(stage_run_id(self.spec), stage_run_id(same))
        changed = copy.deepcopy(self.spec)
        changed["parameters"]["settings"]["size"] = 0.9
        self.assertNotEqual(stage_run_id(self.spec), stage_run_id(changed))

    def test_changed_input_or_upstream_invalidates_identity(self):
        baseline = stage_run_id(self.spec)
        changed = copy.deepcopy(self.spec)
        changed["input_sha256"]["mesh"] = "d" * 64
        self.assertNotEqual(baseline, stage_run_id(changed))
        changed = copy.deepcopy(self.spec)
        changed["upstream_run_ids"] = ["e" * 64]
        self.assertNotEqual(baseline, stage_run_id(changed))

    def test_invalid_spec_fails_closed(self):
        for edit in (
            lambda x: x.update(extra="silent_default"),
            lambda x: x["parameters"].update(bad=math.nan),
            lambda x: x["code_commits"].update(tools="not-a-commit"),
            lambda x: x.update(upstream_run_ids=["e" * 64, "e" * 64]),
            lambda x: x.update(schema_version=True),
        ):
            changed = copy.deepcopy(self.spec)
            edit(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                stage_run_id(changed)

    def test_source_check_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.py"
            path.write_bytes(b"first")
            expected = sha256_file(path)
            self.assertEqual(main(["check-source", str(path), expected]), 0)
            path.write_bytes(b"second")
            self.assertEqual(main(["check-source", str(path), expected]), 2)


if __name__ == "__main__":
    unittest.main()
