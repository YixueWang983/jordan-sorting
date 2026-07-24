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
    SUMMARY_FIELDS,
    audit_generator_coverage,
    generate_mutation_based_invalid_with_metadata,
    generate_random_invalid_with_metadata,
    generate_sequence_with_metadata,
    summarize_audit_rows,
    write_audit,
    write_audit_config,
    write_audit_manifest,
    write_audit_summary,
)
from generators import (  # noqa: E402
    FLAT_VALID,
    INCREMENTAL_VALID,
    INVALID_LOWER_CROSSING,
    INVALID_UPPER_CROSSING,
    MUTATION_BASED_INVALID,
    NESTED_VALID,
    RANDOM_INVALID,
    generate_sequence,
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

    def test_random_invalid_metadata_records_attempts_and_seed(self):
        seq, metadata = generate_random_invalid_with_metadata(8, seed=101)

        self.assertEqual(len(seq), 8)
        self.assertGreaterEqual(metadata["attempts_until_invalid"], 1)
        self.assertGreaterEqual(metadata["oracle_calls"], 1)
        self.assertNotEqual(metadata["accepted_seed"], "")

    def test_mutation_invalid_metadata_records_base_and_swap(self):
        seq, metadata = generate_mutation_based_invalid_with_metadata(8, seed=101)

        self.assertEqual(len(seq), 8)
        self.assertEqual(len(metadata["base_sequence_hash"]), 64)
        self.assertGreaterEqual(metadata["mutation_attempts"], 1)
        self.assertIsInstance(metadata["swap_i"], int)
        self.assertIsInstance(metadata["swap_j"], int)

    def test_summarize_audit_rows_records_duplicate_case_count(self):
        rows = audit_generator_coverage(
            families=[FLAT_VALID, INCREMENTAL_VALID],
            sizes=[8],
            randomized_repetitions=2,
            seed=11,
        )
        summaries = summarize_audit_rows(rows)

        self.assertEqual({row["family"] for row in summaries}, {FLAT_VALID, INCREMENTAL_VALID})
        for row in summaries:
            self.assertEqual(set(row.keys()), set(SUMMARY_FIELDS))
            self.assertGreaterEqual(row["unique_case_count"], 1)
            self.assertGreaterEqual(row["duplicate_case_count"], 0)
            self.assertIn("category_distribution", row)
            self.assertIn("invalid_reason_distribution", row)

    def test_metadata_generators_match_production_generators(self):
        families = [
            FLAT_VALID,
            NESTED_VALID,
            INCREMENTAL_VALID,
            INVALID_UPPER_CROSSING,
            INVALID_LOWER_CROSSING,
            RANDOM_INVALID,
            MUTATION_BASED_INVALID,
        ]

        for family in families:
            for n in [8, 9]:
                with self.subTest(family=family, n=n):
                    seed = 2000 + n
                    expected = generate_sequence(family, n, seed=seed)
                    actual, metadata = generate_sequence_with_metadata(
                        family,
                        n,
                        seed=seed,
                    )

                    self.assertEqual(actual, expected)
                    self.assertEqual(set(metadata.keys()), {
                        "total_attempts",
                        "oracle_calls",
                        "fallback_count",
                        "accepted_random_extensions",
                        "safe_extensions",
                        "attempts_until_invalid",
                        "accepted_seed",
                        "base_sequence_hash",
                        "base_seed",
                        "swap_i",
                        "swap_j",
                        "mutation_attempts",
                    })

    def test_write_audit_creates_csv(self):
        rows = audit_generator_coverage(
            families=[FLAT_VALID],
            sizes=[8],
            randomized_repetitions=1,
            seed=11,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_csv = Path(tmpdir) / "audit.csv"
            summary_csv = Path(tmpdir) / "audit_summary.csv"
            config_json = Path(tmpdir) / "audit_config.json"
            manifest_json = Path(tmpdir) / "audit_manifest.json"
            write_audit_config(
                config_json,
                run_id="audit_test",
                families=[FLAT_VALID],
                sizes=[8],
                randomized_repetitions=1,
                seed=11,
            )
            write_audit(rows, output_csv)
            write_audit_summary(summarize_audit_rows(rows), summary_csv)
            write_audit_manifest(
                manifest_json,
                run_id="audit_test",
                config_json=config_json,
                output_csv=output_csv,
                summary_csv=summary_csv,
                rows=rows,
                summary_rows=summarize_audit_rows(rows),
            )

            self.assertTrue(output_csv.exists())
            self.assertTrue(summary_csv.exists())
            self.assertTrue(config_json.exists())
            self.assertTrue(manifest_json.exists())
            self.assertIn("containment_pair_density", output_csv.read_text())
            self.assertIn("has_duplicate_values", output_csv.read_text())
            self.assertIn("duplicate_case_count", summary_csv.read_text())
            self.assertIn("coverage_audit_csv", manifest_json.read_text())


if __name__ == "__main__":
    unittest.main()
