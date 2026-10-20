"""Diagnostic only: how much of the tree's minimal runtime is instrumentation plumbing?

Variants (each run in its own process):
  list      - ordinary_list, minimal (as measured)
  tree      - heterogeneous_finger, detailed_work=False, minimal (as measured)
  tree_nofa - same, but _Tracked.__getattribute__/__setattr__ removed (plain slot access)
  tree_nowr - additionally unwrap @observed/@phase decorators (call originals directly)
Correctness of every output is checked against sorted().
"""
import gc, json, statistics, sys, time
from pathlib import Path

REPO = Path(sys.argv[1])
VARIANT = sys.argv[2]
CASES = sys.argv[3:]
sys.path.insert(0, str(REPO / "src"))

import heterogeneous_finger_backend as hfb
import heterogeneous_finger_split as hfs
from sibling_backend_contract import SiblingBackendSpec
from paper_jordan_sort import paper_jordan_sort_valid

if VARIANT in ("tree_nofa", "tree_nowr"):
    del hfb._Tracked.__getattribute__
    del hfb._Tracked.__setattr__
if VARIANT == "tree_nowr":
    for cls in (hfb.HeterogeneousFingerBackend, hfs.TreeOperations):
        for name, value in list(vars(cls).items()):
            inner = getattr(value, "__wrapped__", None)
            if inner is not None and not isinstance(value, (staticmethod, classmethod, property)):
                setattr(cls, name, inner)

if VARIANT == "list":
    backend = "ordinary_list"
else:
    backend = SiblingBackendSpec(hfb.HeterogeneousFingerBackend, (("detailed_work", False),))

reqdir = REPO / "docs/validation/common_qualification_v2_20261015/qualification/requests"
out = {}
for case in CASES:
    values = json.load(open(reqdir / f"{case}.json"))["values"]
    expected = sorted(values)
    for _ in range(3):
        assert paper_jordan_sort_valid(values, "minimal", backend=backend) == expected
    reps = 7 if len(values) >= 256 else 25
    samples = []
    for _ in range(15):
        gc.collect()
        t0 = time.perf_counter_ns()
        for _ in range(reps):
            r = paper_jordan_sort_valid(values, "minimal", backend=backend)
        samples.append((time.perf_counter_ns() - t0) / reps / 1e6)
        assert r == expected
    out[case] = statistics.median(samples)
print(json.dumps(out))
