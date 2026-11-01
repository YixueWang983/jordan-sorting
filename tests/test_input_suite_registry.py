"""Input-only checks: no backend, oracle, qualification or timing is executed."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
import input_suite_registry as registry
import validate_input_suite as checker


def synthetic(case_id, values):
    ranks = registry.rank_normalize(values)
    return dict(case_id=case_id, values=values, rank_sequence=ranks, rank_sha256=registry.digest(ranks))


class InputSuiteTests(unittest.TestCase):
    def test_shifted_values_share_identity_but_mirrors_remain_distinct(self):
        rows = [synthetic("common--first", [1, 3, 2]),
                synthetic("seeded--shifted", [0, 2, 1]),
                synthetic("common--mirror", [3, 1, 2])]
        registry.assign_canonical(rows)
        self.assertEqual(rows[1]["canonical_case_id"], "common--first")
        self.assertEqual(rows[1]["duplicate_of"], "common--first")
        self.assertEqual(rows[2]["membership_status"], "CANONICAL")
        self.assertEqual(rows[1]["values"], [0, 2, 1])

    def test_rank_validation_rejects_non_distinct_or_non_integer_inputs(self):
        for values in ([], [1, 1], [True, 2], [1.0, 2], "123"):
            with self.subTest(values=values), self.assertRaises(ValueError):
                registry.rank_normalize(values)
        self.assertEqual(registry.rank_normalize([-5, 20, 0]), [1, 3, 2])

    def test_tampered_rank_identity_and_duplicate_ids_are_rejected(self):
        row = synthetic("common--first", [1, 3, 2])
        bad = copy.deepcopy(row)
        bad["rank_sequence"] = [1, 2, 3]
        with self.assertRaisesRegex(ValueError, "invalid normalized"):
            registry.assign_canonical([bad])
        with self.assertRaisesRegex(ValueError, "duplicate global"):
            registry.assign_canonical([row, copy.deepcopy(row)])

    def test_frozen_source_hash_rejects_even_whitespace_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / registry.REGISTRATION_PATH
            p.parent.mkdir(parents=True)
            p.write_bytes((ROOT / registry.REGISTRATION_PATH).read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "fixed source changed"):
                registry.load_documents(root)

    def test_all_memberships_and_exclusions_match_frozen_documents(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "inventory"
            suite = registry.write_bundle(out)
            report = checker.validate_bundle(out)
            self.assertTrue(report["inventory_valid"])
            self.assertEqual((report["checked_included"], report["checked_excluded"]), (302, 8))
            self.assertEqual(len(registry.canonical_cases(suite)), 302)
            self.assertEqual(len(registry.canonical_cases(suite, "seeded")), 32)
            seeded = [e for e in suite["entries"] if e["source"] == "seeded"]
            self.assertEqual([e["source_index"] for e in seeded],
                             [i for i in range(40) if i not in (6, 7, 14, 15, 22, 23, 30, 31)])
            self.assertTrue(all(min(e["values"]) == 0 and min(e["rank_sequence"]) == 1 for e in seeded))
            self.assertEqual({e["n"] for e in suite["exclusions"]}, {1500})
            self.assertEqual({e["smaller_side_k"] for e in suite["entries"]
                              if e["construction_family"] == "values_for"}, {1, 3, 7, 19, 30, 62, 126})
            self.assertTrue(all(e["smaller_side_k"] is None for e in suite["entries"] if e["shape"] == "repeated"))
            with self.assertRaises(FileExistsError):
                registry.write_bundle(out)

    def test_checker_rejects_metadata_tampering_even_with_recomputed_suite_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "inventory"
            suite = registry.write_bundle(out)
            suite["entries"][0]["source_index"] += 1
            suite["suite_sha256"] = registry.digest({k: v for k, v in suite.items() if k != "suite_sha256"})
            (out / "suite.json").write_text(json.dumps(suite))
            with self.assertRaisesRegex(ValueError, "source mismatch"):
                checker.validate_bundle(out)

    def test_checker_rejects_false_qualification_state(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "inventory"
            registry.write_bundle(out)
            path = out / "initial_execution_state.json"
            states = json.loads(path.read_text())
            first = next(iter(states["cases"].values()))
            first["stages"]["qualification"] = "PASS"
            path.write_text(json.dumps(states))
            with self.assertRaisesRegex(ValueError, "NOT_RUN"):
                checker.validate_bundle(out)

    def test_checker_does_not_trust_exported_counts_or_mapping(self):
        for filename, key in (("summary.json", "canonical_inputs"), ("deduplication.json", "mappings")):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                out = Path(temp) / "inventory"
                registry.write_bundle(out)
                path = out / filename
                data = json.loads(path.read_text())
                data[key] = 301 if key == "canonical_inputs" else []
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "summary reconstruction|deduplication export"):
                    checker.validate_bundle(out)

    def test_loading_and_validation_do_not_import_experimental_execution_modules(self):
        code = (
            "import sys,tempfile; from pathlib import Path; "
            "sys.path.insert(0, 'experiments'); "
            "import input_suite_registry as r; import validate_input_suite as v; "
            "t=tempfile.TemporaryDirectory(); p=Path(t.name)/'suite'; "
            "r.write_bundle(p); v.validate_bundle(p); "
            "forbidden=('paper_jordan','oracle','generators','heterogeneous_finger_backend',"
            "'qualify_common_inputs_v2','matched_measurement'); "
            "assert not any(x in sys.modules for x in forbidden); t.cleanup()"
        )
        subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
