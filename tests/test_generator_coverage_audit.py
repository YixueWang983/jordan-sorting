"""Tests for Week 7 generator coverage audit."""

import tempfile
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from audit_generator_coverage import (  # noqa: E402
    FIELDS,
    audit_generator_coverage,
    write_audit,
)
from generators import (  # noqa: E402
    FLAT_VALID,
    INCREMENTAL_VALID,
    INVALID_UPPER_CROSSING,
    RANDOM_INVALID,
)


class GeneratorCoverageAuditTests(unittest.TestCase):
    def test_audit_generator_coverage_uses_family_specific_repetitions(self):
        rows = audit_generator_coverage(
            families=[FLAT_VALID, INCREMENTAL_VALID, RANDOM_INVALID],
            sizes=[8],
            randomized_repetitions=2,
            seed=11,
        )

        self.assertEqual(len(rows), 5)
        self.assertEqual(
            sum(1 for row in rows if row["family"] == FLAT_VALID),
            1,
        )
        self.assertEqual(
            sum(1 for row in rows if row["family"] == INCREMENTAL_VALID),
            2,
        )
        self.assertEqual(
            sum(1 for row in rows if row["family"] == RANDOM_INVALID),
            2,
        )
        for row in rows:
            self.assertEqual(set(row.keys()), set(FIELDS))

    def test_audit_records_crossing_severity_for_invalid_family(self):
        rows = audit_generator_coverage(
            families=[INVALID_UPPER_CROSSING],
            sizes=[8],
            randomized_repetitions=1,
            seed=11,
        )

        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["valid"])
        self.assertEqual(rows[0]["invalid_reason"], "upper crossing")
        self.assertGreaterEqual(rows[0]["upper_crossing_pair_count"], 1)
        self.assertGreaterEqual(rows[0]["total_crossing_pair_count"], 1)
        self.assertGreater(rows[0]["crossing_pair_density"], 0)
        self.assertEqual(rows[0]["structural_category"], "invalid")
        self.assertFalse(rows[0]["has_duplicate_values"])
        self.assertEqual(len(rows[0]["sequence_hash"]), 64)

    def test_write_audit_creates_csv(self):
        rows = audit_generator_coverage(
            families=[FLAT_VALID],
            sizes=[8],
            randomized_repetitions=1,
            seed=11,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_csv = Path(tmpdir) / "audit.csv"
            write_audit(rows, output_csv)

            self.assertTrue(output_csv.exists())
            self.assertIn("containment_pair_density", output_csv.read_text())
            self.assertIn("has_duplicate_values", output_csv.read_text())


if __name__ == "__main__":
    unittest.main()
