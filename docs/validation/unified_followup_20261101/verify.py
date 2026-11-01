"""Independent raw-record and preservation checks for the post-formal follow-up."""
import argparse
import ast
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"experiments")]
from common_input_protocol import source_identity
from input_suite_protocol import environment_equal
from uninstrumented_protocol import require_machine, require_power, BACKENDS


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(path, name="manifest.json"):
    expected=read(path/name)
    actual={str(p.relative_to(path)):sha(p) for p in path.rglob("*") if p.is_file() and p!=path/name}
    assert not any(p.is_symlink() for p in path.rglob("*"))
    assert expected==actual, str(path)
    return len(actual)


def records(path):
    files=sorted((path/"records").glob("*.json.gz"))
    assert [p.name for p in files]==[f"{i:06d}.json.gz" for i in range(len(files))]
    return [json.loads(gzip.decompress(p.read_bytes())) for p in files]


def close(a,b):
    assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10),(a,b)


def check_stats(values, saved):
    q1,_,q3=statistics.quantiles(values,n=4,method="inclusive")
    expected=dict(n=len(values),median=statistics.median(values),q1=q1,q3=q3,iqr=q3-q1,minimum=min(values),maximum=max(values))
    assert set(expected)==set(saved)
    for key,value in expected.items():close(value,saved[key])


def check_comparison(rows,saved):
    assert saved["inputs"]==len(rows)
    for column,key,absolute in [("ratio_first","first_ratio",False),("ratio_second","second_ratio",False),
                                ("ratio_change","signed_ratio_change",False),
                                ("relative_change_percent","signed_relative_change_percent",False),
                                ("relative_change_percent","absolute_relative_change_percent",True)]:
        check_stats([abs(r[column]) if absolute else r[column] for r in rows],saved[key])
    assert saved["first_tree_faster"]==sum(r["ratio_first"]<1 for r in rows)
    assert saved["second_tree_faster"]==sum(r["ratio_second"]<1 for r in rows)
    assert saved["same_direction"]==sum(r["winner_first"]==r["winner_second"] for r in rows)
    assert saved["transitions"]==dict(Counter(r["winner_first"]+"->"+r["winner_second"] for r in rows))


def verify(benchmark, analysis):
    benchmark,analysis=Path(benchmark).resolve(),Path(analysis).resolve()
    manifest(benchmark);manifest(analysis)
    plan=read(HERE/"protocol.json")
    config=read(benchmark/"config.json")
    assert config["plan"]==plan
    assert all(sha(HERE/k)==v for k,v in config["plan_sources_sha256"].items())
    env=read(benchmark/"environment.json")["execution"]
    require_machine(env)
    assert not env["dirty"] and env["gc_enabled"] and env["gc_thresholds"]==[700,10,10]
    assert env["source_sha256"]==source_identity()
    reference=read(ROOT/plan["stability"]["second"]/"environment.json")["execution"]
    environment_equal(env,reference)
    commit_time=int(subprocess.check_output(["git","show","-s","--format=%ct",env["head"]],cwd=ROOT,text=True))
    assert commit_time<=datetime.fromisoformat(env["captured_at"]).timestamp()
    measure=next(n for n in ast.parse((HERE/"benchmark.py").read_text()).body if isinstance(n,ast.FunctionDef) and n.name=="measure")
    loops=[n for n in measure.body if isinstance(n,ast.For)]
    assert len(loops)==1
    calls=[n for n in ast.walk(loops[0]) if isinstance(n,ast.Call)]
    assert len(calls)==1 and isinstance(calls[0].func,ast.Name) and calls[0].func.id=="HeterogeneousFingerBackend"
    assert config["preparation_outside_timer"] and config["generated_methods"]==54
    completion=read(benchmark/"completion.json")
    assert completion["complete"] and completion["sorting_executed"] is False
    raw=records(benchmark)
    schedule=[]
    for kind,count in (("warmup",5),("sample",50)):
        for round_index in range(count):
            names=("instrumented","uninstrumented") if round_index%2==0 else ("uninstrumented","instrumented")
            schedule.extend((kind,round_index,position,name) for position,name in enumerate(names))
    assert len(raw)==len(schedule)==110
    for index,(row,expected) in enumerate(zip(raw,schedule)):
        assert (row["kind"],row["round"],row["position"],row["configuration"])==expected
        assert row["index"]==index and row["status"]=="PASS" and row["power_passed"]
        assert row["constructors"]==256 and row["instance_audit_passed"]
        assert type(row["elapsed_ns"]) is int and row["elapsed_ns"]==row["finish_ns"]-row["start_ns"]>0
        require_power(row["power_before"]);require_power(row["power_after"])
        assert all(b["collections"]>=a["collections"] for a,b in zip(row["gc_stats_before"],row["gc_stats_after"]))
    samples=[r for r in raw if r["kind"]=="sample"]
    summary=read(analysis/"constructor_summary.json")
    arrays={name:[r["elapsed_ns"]/256 for r in samples if r["configuration"]==name] for name in ("instrumented","uninstrumented")}
    assert all(len(v)==50 for v in arrays.values())
    for name,values in arrays.items():check_stats(values,summary["per_configuration"][name])
    for name in arrays:
        counts=[sum(r["gc_stats_after"][g]["collections"]-r["gc_stats_before"][g]["collections"]
                    for r in samples if r["configuration"]==name) for g in range(3)]
        assert counts==summary["automatic_gc_in_timed_sample_batches"][name]
    differences=[b-a for a,b in zip(arrays["instrumented"],arrays["uninstrumented"])]
    ratios=[b/a for a,b in zip(arrays["instrumented"],arrays["uninstrumented"])]
    check_stats(differences,summary["paired_difference_ns"])
    check_stats(ratios,summary["paired_ratio"])
    close(statistics.median(arrays["uninstrumented"])/statistics.median(arrays["instrumented"]),summary["ratio_of_medians"])
    pairs=read(analysis/"constructor_pairs.json")
    for i,pair in enumerate(pairs):
        assert pair["round"]==i
        close(pair["instrumented_ns"],arrays["instrumented"][i]);close(pair["uninstrumented_ns"],arrays["uninstrumented"][i])
        close(pair["difference_ns"],differences[i]);close(pair["ratio"],ratios[i])
    assert len(pairs)==50
    csv_batches=list(csv.DictReader((analysis/"constructor_batches.csv").open()))
    assert len(csv_batches)==110
    for row,csv_row in zip(raw,csv_batches):
        assert csv_row["configuration"]==row["configuration"] and csv_row["kind"]==row["kind"]
        assert int(csv_row["elapsed_ns"])==row["elapsed_ns"]
        close(float(csv_row["ns_per_construction"]),row["elapsed_ns"]/256)
        assert json.loads(csv_row["automatic_collections"])==[b["collections"]-a["collections"] for a,b in zip(row["gc_stats_before"],row["gc_stats_after"])]
    rows=read(analysis/"stability_cases.json")
    suite=read(ROOT/"docs/validation/input_suite_registry_20261101/suite.json")
    expected_entries={e["case_id"]:e for e in suite["entries"] if e["source"] in plan["stability"]["sources"] and e["duplicate_of"] is None}
    assert len(rows)==len(expected_entries)==170 and {r["case_id"] for r in rows}==set(expected_entries)
    for row in rows:
        entry=expected_entries[row["case_id"]]
        assert row["source"]==entry["source"] and row["input_sha256"]==entry["input_sha256"]
        for attempt,label in (("first","first"),("second","second")):
            folder=ROOT/plan["stability"][attempt]/"sources"/row["source"]
            request=read(folder/"requests"/(row["case_id"]+".json"))
            assert request["entry"]["input_sha256"]==row["input_sha256"]
            assert request["measurement"]["batch_size"]==row["batch_size"]
            batches=records(folder/"jobs"/row["case_id"])
            med=[]
            for backend,short in zip(BACKENDS,("list","tree")):
                elapsed=[r["elapsed_ns"]/r["batch_size"] for r in batches if r["kind"]=="sample" and r["backend"]==backend]
                assert len(elapsed)==20
                med.append(statistics.median(elapsed))
                close(med[-1],row[label+"_"+short+"_median_ns"])
            close(med[1]/med[0],row["ratio_"+label])
        close(row["ratio_change"],row["ratio_second"]-row["ratio_first"])
        close(row["relative_change_percent"],100*(row["ratio_second"]/row["ratio_first"]-1))
        for label in ("first","second"):
            r=row["ratio_"+label]
            assert row["winner_"+label]==("tree" if r<1 else "list" if r>1 else "tie")
    stability=read(analysis/"stability_summary.json")
    assert stability["preregistered"] is False and stability["included_in_main_statistics"] is False
    check_comparison(rows,stability["overall"])
    for source in plan["stability"]["sources"]:check_comparison([r for r in rows if r["source"]==source],stability["per_source"][source])
    csv_rows=list(csv.DictReader((analysis/"stability_cases.csv").open()))
    assert len(csv_rows)==170
    for row,saved in zip(rows,csv_rows):
        assert {k:("" if v is None else str(v)) for k,v in row.items()}==saved
    provenance=read(analysis/"provenance.json")
    assert provenance["benchmark_manifest_sha256"]==sha(benchmark/"manifest.json")
    assert all(sha(ROOT/k)==v for k,v in provenance["original_evidence_manifest_sha256"].items())
    formal_files=manifest(ROOT/"docs/validation/unified_formal_20261101","package_manifest.json")
    preflight_files=manifest(ROOT/"docs/validation/unified_preflight_20261101","package_manifest.json")
    return dict(schema="post_formal_followup_verification_v1", verified_at=datetime.now(timezone.utc).isoformat(),
                passed=True, constructor_batches=110, measured_paired_rounds=50,
                stability_inputs=170, constructor_statistics_independently_rebuilt=True,
                stability_ratios_independently_rebuilt=True, csv_matches_json=True,
                original_formal_package_files_verified=formal_files,
                original_preflight_package_files_verified=preflight_files,
                frozen_151_source_files_unchanged=True, same_machine_and_runtime=True,
                protocol_commit=env["head"], protocol_committed_before_measurement=True,
                no_sorting_in_constructor_loop=True, main_statistics_unchanged=True,
                stability_comparison_post_hoc=True, inferential_tests_performed=False)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark",type=Path,required=True)
    parser.add_argument("--analysis",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(verify(args.benchmark,args.analysis),indent=2))
