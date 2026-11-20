from collections import Counter
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
from baseline_comparison import CountedKey, METHODS, count_call, reference, rotation, sort_methods


class BaselineComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.methods = sort_methods()

    def test_integer_and_wrapped_calls(self):
        for seq in ([], [1], [2, 1], [1, 6, 2, 5, 3, 4], list(range(17, 0, -1))):
            for name, sort in self.methods.items():
                with self.subTest(seq=seq, method=name):
                    expected = reference(seq)
                    self.assertEqual(sort(seq), expected)
                    counts = count_call(sort, seq, expected)
                    self.assertEqual(counts["total"], sum(counts[k] for k in ("lt", "le", "gt", "ge")))

    def test_merge_hand_count(self):
        self.assertEqual(count_call(self.methods["merge_sort"], [3, 1, 2], [1, 2, 3]),
                         dict(lt=0, le=3, gt=0, ge=0, sentinel=0, total=3))

    def test_reflection_and_equality(self):
        counts = Counter()
        key = CountedKey(3, counts)
        self.assertEqual({key: "value"}[3], "value")
        self.assertFalse(key != 3)
        self.assertIs(key.__lt__(object()), NotImplemented)
        self.assertFalse(counts)
        self.assertTrue(float("-inf") < key <= float("inf"))
        self.assertTrue(key >= key)
        self.assertFalse(key < 3)
        self.assertEqual(counts, Counter(gt=1, le=1, ge=1, lt=1, sentinel=2))

    def test_balanced_rotation(self):
        for i in range(5):
            order = [rotation(i, r) for r in range(20)]
            for column in zip(*order):
                self.assertEqual(Counter(column), {m: 4 for m in METHODS})


class MeasurementTests(unittest.TestCase):
    def test_calibration_crosses_old_cap_and_selects_first_median(self):
        from unittest.mock import Mock, patch
        from run_baseline_comparison import calibration, digest
        log = Mock(location={})
        values = [1]
        case = {"values": values, "input_sha256": digest(values)}
        def fake_batch(sort, seq, expected, size, sha):
            t = size * 50_000
            return dict(elapsed_ns=t, wall_ns=t+1000)
        with patch("run_baseline_comparison.batch", side_effect=fake_batch):
            result = calibration(log, "sorted", sorted, case, values, digest(values))
        self.assertEqual(result["B"], 256)

    def test_threshold_exhaustion(self):
        from unittest.mock import Mock, patch
        from run_baseline_comparison import calibration, digest
        values = [1]
        case = {"values": values, "input_sha256": digest(values)}
        with patch("run_baseline_comparison.batch", return_value=dict(elapsed_ns=1, wall_ns=2)) as fake:
            with self.assertRaisesRegex(ValueError, "no qualifying B"):
                calibration(Mock(location={}), "sorted", sorted, case, values, digest(values))
        self.assertEqual(fake.call_count, 21 * 3)
        self.assertEqual(fake.call_args.args[3], 1 << 20)

    def test_every_output_is_checked(self):
        from unittest.mock import Mock
        from run_baseline_comparison import batch, digest
        sort = Mock(side_effect=[[2], [1], [1]])
        with self.assertRaisesRegex(ValueError, "batch call 0"):
            batch(sort, [1], [1], 3, digest([1]))

    def test_synthetic_session_replays_against_preparation(self):
        import tempfile
        from unittest.mock import patch
        import analyze_baseline_comparison as analysis
        import run_baseline_comparison as run

        values = [3, 1, 2]
        cases = [dict(case_id="fixture", values=values, input_sha256=run.digest(values), n=3)]
        def synthetic_batch(sort, original, expected, size, sha):
            self.assertEqual(sort(original), expected)
            return dict(B=size, start_ns=0, end_ns=10_000_000, elapsed_ns=10_000_000,
                        verified_calls=size, output_sha256=sha, wall_ns=12_000_000)
        def synthetic_power(log, side):
            log.row(kind="power", side=side, time=run.utc(), power="Now drawing from 'AC Power'",
                    power_settings="lowpowermode 0", power_source="AC Power", lowpowermode="0")

        with tempfile.TemporaryDirectory() as temp:
            prep = Path(temp) / "prep"
            formal = Path(temp) / "formal"
            with patch.object(run, "identity", return_value={"synthetic": True}), \
                    patch.object(run, "inputs", return_value=cases), \
                    patch.object(run, "batch", synthetic_batch), \
                    patch.object(run.Journal, "power", synthetic_power):
                run.execute("prepare", prep, None)
                run.execute("formal", formal, prep)
            manifest, cfg, chosen, counts, estimate = analysis.preparation(prep, cases)
            times = analysis.formal(formal, cases, manifest, cfg, chosen)
            self.assertEqual(counts["fixture", "merge_sort"], 3)
            self.assertEqual(times["fixture", "sorted"], 10_000_000)
            self.assertGreater(estimate, 0)
            chosen["fixture"]["sorted"]["B"] = 2
            with self.assertRaisesRegex(ValueError, "unexpected B"):
                analysis.formal(formal, cases, manifest, cfg, chosen)
