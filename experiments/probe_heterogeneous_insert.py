"""Small deterministic WORK probe for the partial heterogeneous backend.

No wall-clock measurement, Jordan input qualification or full-contract
acceptance. Raw per-operation records and a separately checked model are saved
so the reported totals can be independently recomputed.
"""

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from heterogeneous_finger_backend import HeterogeneousFingerBackend  # noqa: E402
from paper_execution_policy import COUNTERS_ONLY_POLICY  # noqa: E402
from sibling_list_backend import LEFT, RIGHT, UPPER, PairRecord  # noqa: E402


def directions(pattern, n):
    generator = random.Random(20261012)
    for step in range(1, n):
        if pattern == "left":
            yield LEFT
        elif pattern == "right":
            yield RIGHT
        elif pattern == "alternating":
            yield LEFT if step % 2 else RIGHT
        else:
            yield generator.choice((LEFT, RIGHT))


def probe(pattern, n, stream):
    points = {}
    backend = HeterogeneousFingerBackend(points.__getitem__, execution_policy=COUNTERS_ONLY_POLICY)
    case = f"{pattern}-{n}"
    total = dict.fromkeys(backend.work.FIELDS, 0)
    insertion_total = total.copy()
    insertion_max = total.copy()

    def record(step, side):
        item = backend.work.last_operation
        if item["status"] != "ok":
            raise RuntimeError("cannot record a failed operation as accepted")
        stream.write(json.dumps({"case": case, "step": step, "side": side, **item}, sort_keys=True) + "\n")
        for key, value in item["work"].items():
            total[key] += value
            if item["operation"] == "insert_boundary":
                insertion_total[key] += value
                insertion_max[key] = max(insertion_max[key], value)

    backend.register_pair(PairRecord(-1, None, None, None, UPPER, is_dummy=True))
    record(-1, None)
    model = deque()
    low, high = 0, 1
    for step, side in enumerate([None, *directions(pattern, n)]):
        pair_id = 2 * (step + 1)
        first_id, second_id = pair_id - 1, pair_id
        if side == LEFT:
            low -= 3
            a, b = low, low+1
        elif side == RIGHT:
            high += 3
            a, b = high-1, high
        else:
            a, b = low, high
        points[first_id], points[second_id] = (b, a) if step % 2 else (a, b)
        pair = PairRecord(pair_id, pair_id, first_id, second_id, UPPER)
        backend.register_pair(pair)
        record(step, side)
        if side is None:
            list_id = backend.make_list(pair_id, -1)
            model.append(pair_id)
        else:
            anchor = model[0] if side == LEFT else model[-1]
            if backend.insert_boundary(pair_id, anchor, side) != list_id:
                raise RuntimeError("insertion changed the live list id")
            model.appendleft(pair_id) if side == LEFT else model.append(pair_id)
        record(step, side)

    # Full verification is deliberately outside the normal operation bucket.
    actual = backend.materialize_audit()
    if actual != ((-1, tuple(model)),):
        raise RuntimeError("tree/model mismatch")
    if backend.work.snapshot()["operations"] != total:
        raise RuntimeError("raw per-operation records do not sum to actual totals")
    return {
        "case": case, "items": n, "inserts": n-1, "model_and_structure_passed": True,
        "operation_totals": total, "insertion_totals": insertion_total,
        "maximum_single_insertion": insertion_max,
        "queries": backend.work.snapshot()["queries"],
        "audit": backend.work.snapshot()["audit"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[64, 256, 1024])
    args = parser.parse_args(argv)
    if any(n < 1 for n in args.sizes) or len(set(args.sizes)) != len(args.sizes):
        parser.error("sizes must be distinct positive integers")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    raw = args.output_dir / "operation_work.jsonl"
    with raw.open("w") as stream:
        cases = [probe(pattern, size, stream) for size in args.sizes
                 for pattern in ("left", "right", "alternating", "seeded")]
    result = {
        "scope": "partial_make_insert_only", "contract_acceptance_passed": False,
        "backend_ready_for_timing": False, "sorting_ready": False,
        "metrics_schema": HeterogeneousFingerBackend.metrics_schema,
        "seed_for_seeded_histories": 20261012, "cases": cases,
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "source_sha256": {str(p.relative_to(PROJECT_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (PROJECT_ROOT / "src/heterogeneous_finger_backend.py",
                                    PROJECT_ROOT / "src/sibling_backend_contract.py", Path(__file__))},
    }
    (args.output_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"scope": result["scope"], "cases_passed": len(cases),
                      "backend_ready_for_timing": False, "output_dir": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
