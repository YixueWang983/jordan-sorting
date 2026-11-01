"""Descriptive constructor analysis and explicitly post-hoc 170-input comparison."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "experiments")]
from committed_records import read_records
from input_suite_registry import load_suite, canonical_cases
from validate_input_suite_run import validate, verify_manifest
from uninstrumented_protocol import BACKENDS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def stats(values):
    ordered = sorted(values)
    def q(p):
        x = (len(ordered)-1)*p
        lo = int(x)
        return ordered[lo] + (ordered[min(lo+1, len(ordered)-1)]-ordered[lo])*(x-lo)
    return dict(n=len(values), median=statistics.median(values), q1=q(.25), q3=q(.75),
                iqr=q(.75)-q(.25), minimum=min(values), maximum=max(values))


def winner(value):
    return "tree" if value < 1 else "list" if value > 1 else "tie"


def comparison_summary(rows):
    return dict(inputs=len(rows),
                first_ratio=stats([r["ratio_first"] for r in rows]),
                second_ratio=stats([r["ratio_second"] for r in rows]),
                signed_ratio_change=stats([r["ratio_change"] for r in rows]),
                absolute_relative_change_percent=stats([abs(r["relative_change_percent"]) for r in rows]),
                signed_relative_change_percent=stats([r["relative_change_percent"] for r in rows]),
                first_tree_faster=sum(r["winner_first"] == "tree" for r in rows),
                second_tree_faster=sum(r["winner_second"] == "tree" for r in rows),
                same_direction=sum(r["winner_first"] == r["winner_second"] for r in rows),
                transitions=dict(sorted(Counter(r["winner_first"]+"->"+r["winner_second"] for r in rows).items())))


def timing(job, expected):
    records = read_records(job)
    medians = {}
    for backend in BACKENDS:
        values = [r["elapsed_ns"] / r["batch_size"] for r in records
                  if r["kind"] == "sample" and r["backend"] == backend and r["status"] == "PASS"]
        assert len(values) == 20
        medians[backend] = statistics.median(values)
        assert math.isclose(medians[backend], expected["groups"][backend]["median_ns_per_call"], rel_tol=1e-12)
    ratio = medians[BACKENDS[1]] / medians[BACKENDS[0]]
    assert math.isclose(ratio, expected["tree_over_list_median"], rel_tol=1e-12)
    return medians[BACKENDS[0]], medians[BACKENDS[1]], ratio


def csv_write(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def analyze(benchmark, output):
    benchmark, output = Path(benchmark).resolve(), Path(output).resolve()
    assert not output.exists()
    protocol = read(HERE / "protocol.json")
    verify_manifest(benchmark)
    assert read(benchmark / "completion.json")["complete"]
    raw = read_records(benchmark)
    assert len(raw) == 110 and all(r["status"] == "PASS" for r in raw)
    sampled = [r for r in raw if r["kind"] == "sample"]
    batches = [dict(index=r["index"], kind=r["kind"], round=r["round"], position=r["position"],
                    configuration=r["configuration"], constructors=r["constructors"],
                    elapsed_ns=r["elapsed_ns"], ns_per_construction=r["elapsed_ns"]/r["constructors"],
                    automatic_collections=[b["collections"]-a["collections"] for a,b in zip(r["gc_stats_before"],r["gc_stats_after"])])
               for r in raw]
    paired = []
    for i in range(50):
        pair = {r["configuration"]: r["elapsed_ns"]/r["constructors"] for r in sampled if r["round"] == i}
        assert set(pair) == {"instrumented", "uninstrumented"}
        paired.append(dict(round=i, instrumented_ns=pair["instrumented"], uninstrumented_ns=pair["uninstrumented"],
                           difference_ns=pair["uninstrumented"]-pair["instrumented"],
                           ratio=pair["uninstrumented"]/pair["instrumented"]))
    construction = dict(
        schema="constructor_descriptive_summary_v1", plan_sha256=sha(HERE/"protocol.json"),
        scope="constructor-path comparison only; not isolated binding cost; not subtracted from formal measurements",
        unit="elapsed_ns/256, one observation per batch",
        per_configuration={name: stats([p[name+"_ns"] for p in paired]) for name in ("instrumented", "uninstrumented")},
        paired_difference_ns=stats([p["difference_ns"] for p in paired]),
        paired_ratio=stats([p["ratio"] for p in paired]),
        ratio_of_medians=statistics.median(p["uninstrumented_ns"] for p in paired)/statistics.median(p["instrumented_ns"] for p in paired),
        automatic_gc_in_timed_sample_batches={name: [sum(r["gc_stats_after"][g]["collections"]-r["gc_stats_before"][g]["collections"]
                                                       for r in sampled if r["configuration"] == name) for g in range(3)]
                                              for name in ("instrumented", "uninstrumented")})
    old_root = ROOT / protocol["stability"]["first"]
    new_root = ROOT / protocol["stability"]["second"]
    protected = {str(p.relative_to(ROOT)): sha(p) for p in (
        ROOT/"docs/validation/unified_preflight_20261101/package_manifest.json",
        ROOT/"docs/validation/unified_formal_20261101/package_manifest.json",
        old_root/"manifest.json", new_root/"manifest.json",
        new_root.parent/"unified_analysis_bca4c1c6_restart_20261101_01/manifest.json")}
    cache = {}
    first = validate(old_root, cache=cache)
    second = validate(new_root, cache=cache)
    assert first["archive_valid"] and not first["complete"] and first["hard_error"]
    assert second["archive_valid"] and second["complete"] and not second["hard_error"]
    sources = protocol["stability"]["sources"]
    assert [s for s,v in first["sources"].items() if v["status"] == "COMPLETE"] == sources
    suite = load_suite()
    rows = []
    for source in sources:
        for entry in canonical_cases(suite, source):
            cid = entry["case_id"]
            requests = [read(p/"sources"/source/"requests"/(cid+".json")) for p in (old_root,new_root)]
            assert all(r["entry"]["input_sha256"] == entry["input_sha256"] for r in requests)
            assert requests[0]["measurement"]["batch_size"] == requests[1]["measurement"]["batch_size"]
            a = timing(old_root/"sources"/source/"jobs"/cid, first["sources"][source]["statistics"][cid])
            b = timing(new_root/"sources"/source/"jobs"/cid, second["sources"][source]["statistics"][cid])
            rows.append(dict(case_id=cid, source=source, n=entry["n"], category=entry["category"], shape=entry["shape"],
                             input_sha256=entry["input_sha256"], batch_size=requests[0]["measurement"]["batch_size"],
                             first_list_median_ns=a[0], first_tree_median_ns=a[1], ratio_first=a[2],
                             second_list_median_ns=b[0], second_tree_median_ns=b[1], ratio_second=b[2],
                             ratio_change=b[2]-a[2], relative_change_percent=100*(b[2]/a[2]-1),
                             winner_first=winner(a[2]), winner_second=winner(b[2])))
    assert len(rows) == protocol["stability"]["expected_inputs"] == 170
    stability = dict(schema="post_hoc_attempt_stability_v1", preregistered=False, included_in_main_statistics=False,
                     interpretation="descriptive comparison of two dependent, fixed sessions only; first failure and restart deviation remain disclosed",
                     selection=protocol["stability"]["selection"], overall=comparison_summary(rows),
                     per_source={s:comparison_summary([r for r in rows if r["source"]==s]) for s in sources})
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    output.mkdir(parents=True, exist_ok=False)
    write(output/"constructor_summary.json", construction)
    write(output/"constructor_pairs.json", paired)
    csv_write(output/"constructor_batches.csv", [{**r,"automatic_collections":json.dumps(r["automatic_collections"])} for r in batches])
    write(output/"stability_summary.json", stability)
    write(output/"stability_cases.json", rows)
    csv_write(output/"stability_cases.csv", rows)
    write(output/"provenance.json", dict(created_at=datetime.now(timezone.utc).isoformat(),
          benchmark_path=str(benchmark), benchmark_manifest_sha256=sha(benchmark/"manifest.json"),
          plan_sources_sha256=read(benchmark/"config.json")["plan_sources_sha256"],
          original_evidence_manifest_sha256=protected, original_evidence_unchanged=True,
          first_validation={k:first[k] for k in ("archive_valid","complete","hard_error")},
          second_validation={k:second[k] for k in ("archive_valid","complete","hard_error")}))
    write(output/"manifest.json", {p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()})
    print(json.dumps(dict(constructor=construction, stability=stability), indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    analyze(args.benchmark,args.output)
