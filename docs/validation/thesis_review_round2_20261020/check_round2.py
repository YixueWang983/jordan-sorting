"""Read-only frozen-file, generator and textual-condition checks; no sorting."""
import sys

if sys.flags.optimize:
    raise RuntimeError("Run evidence checks without Python optimization")

import ast
import hashlib
import json
from pathlib import Path
import random
import subprocess

D = Path(__file__).resolve().parent
R = D.parents[2]
OLD = D.parent / "thesis_revision_20261020"
BASE = "2da8b662bf3c50c1bd51ee85ed2215a72a34f7c7"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


frozen = ["src", "experiments", "tests", "data", "results",
          "docs/validation/thesis_revision_20261020"]
frozen_files = {}
for folder in frozen:
    raw = subprocess.check_output(["git", "ls-tree", "-r", "-z", BASE, "--", folder], cwd=R)
    entries = [entry for entry in raw.split(b"\0") if entry]
    for entry in entries:
        meta, name = entry.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        assert kind == "blob" and mode in ("100644", "100755")
        path = R / name.decode()
        assert path.is_file() and not path.is_symlink()
        content = path.read_bytes()
        actual = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        assert actual == oid, f"Frozen file changed: {name.decode()}"
    frozen_files[folder] = len(entries)
for name, digest in read(OLD / "SHA256SUMS.json").items():
    assert sha(OLD / name) == digest, f"Old sealed evidence changed: {name}"
old_outputs = {}
for name in ("output/pdf/jordan_thesis_supervisor_review_20261020.pdf",
             "output/packages/jordan_supervisor_review_20261020.zip"):
    content = subprocess.check_output(["git", "show", BASE + ":" + name], cwd=R)
    assert (R / name).read_bytes() == content
    old_outputs[name] = hashlib.sha256(content).hexdigest()

# Reconstruct the already saved values from the recorded sequential RNG schedule.
# Loading just this reviewed definition avoids executing the supplied script's
# CLI/imports, which would otherwise start a separate sorting campaign.
generator = OLD / "external_review/random_jordan_stress2.py"
module = ast.parse(generator.read_text())
definition = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "generate")
namespace = {}
exec(compile(ast.Module(body=[definition], type_ignores=[]), str(generator), "exec"), namespace)
values = read(OLD / "local_supplement/inputs.json")
protocol = read(OLD / "local_supplement/protocol.json")
specs = protocol["stress"]
expected_specs = [
    dict(case=f"stress-{seed}-{n}-{bias}", seed=seed, n=n, bias=bias, checked=False)
    for seed in (11, 12, 13, 14)
    for n in (128, 512, 513, 1500)
    for bias in (.05, .25)
] + [
    dict(case=f"checked-{seed}-{n}", seed=seed, n=n, bias=.1, checked=True)
    for seed in (21, 22)
    for n in (32, 33, 64, 70)
]
assert specs == expected_specs
streams = {}
for spec in specs:
    rng = streams.setdefault(spec["seed"], random.Random(spec["seed"]))
    assert namespace["generate"](spec["n"], rng, spec["bias"]) == values[spec["case"]]

proof = (R / "thesis/appendix/backend_argument.tex").read_text()
assert "bracket all other finite endpoints" in proof
assert "locality lemma (a)--(b)" in proof
assert "beyond $z_j$ empty, so the owner has at most one group" in proof
assert "Header fingers reference leaves $a,d$ (arrows omitted)" in proof
implementation = (R / "thesis/chapters/implementation.tex").read_text()
assert "supplied gap-based" not in implementation
assert "same-parity arc has exactly one endpoint" in implementation
assert "Seeds 11--14" in implementation and "seeds 21--22" in implementation
appendix = (R / "thesis/appendix/claim_traceability.tex").read_text()
assert "Supplementary Reviewer Material" not in appendix
assert "The author directs the research; OpenAI Codex is used as an assistant" in appendix
assert "personal reflection" in appendix and "remain to be finalized" in appendix
assert "not a percentage of authorship" in appendix
for name, count in (("formal_common_recheck.json", 140), ("formal_targeted_recheck.json", 12)):
    report = read(D / name)
    assert report["archive_valid"] is True and report["complete"] is True
    assert report["stage"] == "formal" and report["inputs"] == count
testlog = (D / "unittest.log").read_text()
assert "\nRan 805 tests in " in testlog and testlog.rstrip().endswith("\nOK")
print(json.dumps(dict(
    scope="frozen_files_generator_and_round2_text", baseline=BASE,
    frozen_files_checked=frozen_files, old_manifest_verified_files=len(read(OLD / "SHA256SUMS.json")),
    old_outputs=old_outputs, generator_sha256=sha(generator),
    generator_inputs_recreated=40, sorter_executed=False,
    formal_archives_valid=True, unittest_methods=805,
    checker_sha256=sha(Path(__file__)), ai_declaration_finalized=False,
    mathematical_certification=False), indent=2))
