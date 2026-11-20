"""Replay saved records to verify the supplement and produce its descriptive results."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from statistics import median

from baseline_comparison import CANDIDATES, METHODS, TARGET_NS, digest, inputs, reference, require
from run_baseline_comparison import load_completed, read_json
from uninstrumented_protocol import require_power


class Records:
    def __init__(self, stream):
        self.stream = stream
        self.case = {}
        self.output_sha = None

    def bind(self, index, case):
        self.case = dict(index=index, case=case["case_id"], input_sha256=case["input_sha256"], n=case["n"])
        self.output_sha = digest(reference(case["values"]))

    def get(self, **fields):
        row = json.loads(next(self.stream))
        for k, v in (self.case | fields).items():
            require(row.get(k) == v, f"unexpected {k} in {row.get('case')}: {row.get(k)} vs {v}")
        return row

    def batch(self, **fields):
        row = self.get(**fields, output_sha256=self.output_sha)
        require(row["elapsed_ns"] == row["end_ns"] - row["start_ns"] > 0
                and row["verified_calls"] == row["B"], "invalid batch timing or verification")
        return row

    def power(self, stage, side):
        require_power(self.get(phase=stage, kind="power", side=side))


def preparation(path, cases):
    manifest = load_completed(path)
    cfg = read_json(path / "config.json")
    require(cfg["mode"] == "prepare" and cfg["case_order"] == [c["case_id"] for c in cases], "preparation config")
    selected = read_json(path / "calibration.json")
    counts, estimate_ns = {}, 0
    with (path / "records.jsonl").open() as stream:
        records = Records(stream)
        for stage in ("correctness", "comparisons", "calibration"):
            for i, case in enumerate(cases):
                records.bind(i, case)
                cid = case["case_id"]
                if stage == "calibration":
                    records.power(stage, "before")
                for method in METHODS:
                    fields = dict(phase=stage, method=method)
                    if stage == "correctness":
                        row = records.get(**fields, kind="output", output_sha256=records.output_sha)
                        require(row["output"] == reference(case["values"]), "incorrect qualification output")
                    elif stage == "comparisons":
                        keys = records.get(**fields, kind="counts", output_sha256=records.output_sha)["counts"]
                        require(all(type(v) is int and v >= 0 for v in keys.values())
                                and keys["total"] == sum(keys[k] for k in ("lt", "le", "gt", "ge"))
                                and keys["sentinel"] <= keys["total"], "comparison count")
                        counts[cid, method] = keys["total"]
                    else:
                        for b in CANDIDATES:
                            rows = [records.batch(**fields, kind="candidate", round=r, B=b) for r in range(3)]
                            duration = median(x["elapsed_ns"] for x in rows)
                            wall = median(x["wall_ns"] for x in rows)
                            records.get(**fields, kind="candidate_summary", B=b, median_ns=duration,
                                        target_ns=TARGET_NS, selected=duration >= TARGET_NS)
                            if b == 1:
                                estimate_ns += 5 * wall
                            if duration >= TARGET_NS:
                                require(selected[cid][method] == dict(B=b, median_ns=duration, median_wall_ns=wall),
                                        "chosen B or median mismatch")
                                estimate_ns += 20 * wall
                                break
                        else:
                            raise ValueError("calibration exhausted")
                if stage == "calibration":
                    records.power(stage, "after")
        require(stream.readline() == "", "trailing preparation records")
    return manifest, cfg, selected, counts, estimate_ns / 60e9


def formal(path, cases, prep_manifest, prep_cfg, selected):
    load_completed(path)
    cfg = read_json(path / "config.json")
    require(cfg["mode"] == "formal" and cfg["preparation_manifest"] == digest(prep_manifest)
            and cfg["identity"] == prep_cfg["identity"] and cfg["case_order"] == prep_cfg["case_order"],
            "formal configuration differs from preparation")
    times = {}
    with (path / "records.jsonl").open() as stream:
        records = Records(stream)
        for i, case in enumerate(cases):
            records.bind(i, case)
            records.power("formal", "before")
            samples = defaultdict(list)
            for kind, rounds in (("warmup", 5), ("sample", 20)):
                for r in range(rounds):
                    for pos in range(5):
                        m = METHODS[(i+r+pos) % 5]
                        b = 1 if kind == "warmup" else selected[case["case_id"]][m]["B"]
                        row = records.batch(phase="formal", kind=kind, round=r, position=pos, method=m, B=b)
                        if kind == "sample":
                            samples[m].append(row["elapsed_ns"]/b)
            records.power("formal", "after")
            for m in METHODS:
                times[case["case_id"], m] = median(samples[m])
        require(stream.readline() == "", "trailing formal records")
    return times


def report(output, cases, counts, times):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output.mkdir(parents=True, exist_ok=False)
    lengths = sorted({c["n"] for c in cases})
    for metric, filename, label in ((times, "runtime", "Median time per sort (µs)"),
                                     (counts, "comparisons", "Median key comparisons per element")):
        fig, ax = plt.subplots(figsize=(8, 5))
        for method in METHODS:
            ys = []
            for n in lengths:
                values = [metric[c["case_id"], method] for c in cases if c["n"] == n]
                ys.append(median(values) / (1000 if filename == "runtime" else n))
            ax.plot(lengths, ys, marker=".", label="sorted (CPython reference)" if method == "sorted" else method)
        ax.set_xscale("log", base=2)
        if filename == "runtime":
            ax.set_yscale("log")
        ax.set(xlabel="Input length n", ylabel=label)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(output / (filename + ".pdf"))
        plt.close(fig)
    bins = (("32/33", 32, 33), ("64–70", 64, 70), ("128/129", 128, 129),
            ("256/257", 256, 257), ("512/513", 512, 513), ("All", 32, 513))
    with (output / "size_bands.csv").open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["band", "inputs", *[m+"_ratio" for m in METHODS],
                         *[j+"_faster_than_"+b for j in METHODS[:2] for b in METHODS[2:4]]])
        for label, lo, hi in bins:
            ids = [c["case_id"] for c in cases if lo <= c["n"] <= hi]
            ratios = [median(times[i,m] / times[i,METHODS[0]] for i in ids) for m in METHODS]
            wins = [sum(times[i,j] < times[i,b] for i in ids) for j in METHODS[:2] for b in METHODS[2:4]]
            writer.writerow([label, len(ids), *ratios, *wins])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--formal", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if bool(args.formal) != bool(args.output):
        parser.error("provide both --formal and --output for reporting")
    cases = inputs()
    manifest, cfg, selected, counts, minutes = preparation(args.preparation, cases)
    print(f"Verified {len(counts)} combinations. Estimated warm-up and sample wall time: {minutes:.1f} min "
          "(plus power checks, journal and session setup).")
    if args.formal:
        times = formal(args.formal, cases, manifest, cfg, selected)
        report(args.output, cases, counts, times)
