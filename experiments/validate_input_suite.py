"""Independently audit a saved input inventory against fixed source documents.

No generator, oracle, sorting implementation or experimental runner is imported.
Saved summaries and canonical assignments are checked, not trusted.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from input_suite_registry import (
    ROOT, FILE_SHA256, SOURCES, SOURCE_ORDER, GEO_PATH, SEED_BASE,
    REGISTRATION_PATH, REGISTRATION_COMMIT, SCHEMA, STAGES,
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def audit_entry(entry, source, index, record, values, excluded):
    """Compare every preserved field to its original record, without the loader."""
    old = source.kind == "selection"
    spec = record["spec"] if old else record
    cid = spec["case"]
    pointer = f"/{'stress' if source.kind == 'seeded' else 'cases'}/{index}"
    value_file = SEED_BASE + "/inputs.json" if source.kind == "seeded" else source.path
    value_pointer = ("/" + cid.replace("~", "~0").replace("/", "~1") if source.kind == "seeded"
                     else pointer + ("/values" if old else "/rank_sequence"))
    require(type(values) is list and all(type(v) is int for v in values)
            and len(set(values)) == len(values), "invalid archived numeric values")
    # Independent rank reconstruction; do not use the registry's rank function.
    ordered = sorted(values)
    ranks = [ordered.index(v) + 1 for v in values]
    n = len(values)
    require(n == (spec["target_n"] if source.kind == "geometric" else spec["n"]), "source size")
    metadata = ({k: v for k, v in record.items() if k != "values"} if old else
                {k: record[k] for k in ("case", "target_n", "index", "seed",
                                       "rank_sequence_sha256", "intersection_count", "status")}
                if source.kind == "geometric" else dict(spec))
    family, shape, k = None, None, None
    if source.name == "common":
        family = {"strict_flat": "increasing_flat", "low_nesting_valid": "low_nesting_block",
                  "medium_nesting_valid": "medium_nesting_block", "nested_heavy_valid": "nested_suffix"}[
                      spec["requested_category"]]
    elif source.name == "targeted_split":
        family, shape, k = "values_for", "targeted", spec["k"]
        require(n in (128, 129) and k in (3, 7, 19), "targeted parameters")
    elif source.name == "structural":
        shape = spec["shape"]
        family = "repeated" if shape == "repeated" else "values_for"
        k = None if shape == "repeated" else 1 if shape == "skew" else (n - n % 2 - 6) // 4
        require(shape in ("balanced", "skew", "repeated")
                and n in (128, 129, 256, 257, 512, 513)
                and spec["mirror"] == bool(n % 2), "structural parameters")
    elif source.name == "geometric":
        family = "grid_tree_corridor_polygon"
        require(record["intersection_count"] == n and sha(values) == record["rank_sequence_sha256"],
                "geometric rank identity")
    else:
        family = "seeded_legal_gap"
    expected = dict(case_id=source.name + "--" + cid, source=source.name,
                    original_case_id=cid, source_index=index,
                    legacy_dataset="structural_split" if source.name == "structural" else source.name,
                    values=values, n=n, input_sha256=sha(values), rank_sequence=ranks, rank_sha256=sha(ranks),
                    construction_family=family, shape=shape, smaller_side_k=k,
                    seed=spec.get("seed"), bias=spec.get("bias") if source.name == "seeded" else None,
                    mirror=spec.get("mirror") if old else None, base_id=spec.get("base_id") if old else None,
                    category=spec.get("requested_category") if old else None,
                    source_metadata=metadata,
                    provenance=dict(source_file=source.path, source_file_sha256=FILE_SHA256[source.path],
                                    record_pointer=pointer, record_sha256=sha(record),
                                    values_file=value_file, values_file_sha256=FILE_SHA256[value_file],
                                    values_pointer=value_pointer))
    if old:
        require(sha(values) == record["input_sha256"] and sha(ranks) == record["rank_sha256"]
                and record["profile"]["category"] == spec["requested_category"], "legacy identity/category")
    mutable = {"membership_status", "canonical_case_id", "duplicate_of"}
    if excluded:
        expected.update(exclusion_reason="addendum_section_1_n1500",
                        exclusion_reference=REGISTRATION_PATH + "#1")
    require(set(entry) == set(expected) | mutable, "unexpected/missing inventory fields: " + cid)
    for field, wanted in expected.items():
        require(sha(entry[field]) == sha(wanted), f"source mismatch: {source.name}/{cid}/{field}")
    return tuple(ranks)


def validate_bundle(output, root=ROOT):
    output, root = Path(output), Path(root)
    documents = {}
    for path, expected in FILE_SHA256.items():
        raw = (root / path).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, "fixed source bytes: " + path)
        if path.endswith(".json"):
            documents[path] = json.loads(raw)
    suite = read(output / "suite.json")
    payload = {k: v for k, v in suite.items() if k != "suite_sha256"}
    require(suite["suite_sha256"] == sha(payload), "suite digest")
    require(suite["schema"] == SCHEMA and suite["scope"] == "input_inventory_only"
            and suite["source_order"] == list(SOURCE_ORDER), "suite identity/order")
    require(suite["registration"] == dict(path=REGISTRATION_PATH, commit=REGISTRATION_COMMIT,
                                         sha256=FILE_SHA256[REGISTRATION_PATH]), "registration binding")
    require(suite["source_files"] == FILE_SHA256, "source file bindings")
    require(suite["legacy_selections"] == {s.name: s.selection_sha256 for s in SOURCES if s.selection_sha256},
            "legacy selection bindings")
    require(suite["deduplication_rule"] ==
            "first source/index, normalized full rank sequence; no mirror equivalence", "deduplication rule")

    expected, omitted = [], []
    for source in SOURCES:
        doc = documents[source.path]
        if source.kind == "selection":
            require(doc["selection_sha256"] == source.selection_sha256
                    and sha(doc["cases"]) == source.selection_sha256 and doc["deficits"] == [],
                    "legacy selection identity")
        records = doc["stress"] if source.kind == "seeded" else doc["cases"]
        for index, record in enumerate(records):
            values = (record["values"] if source.kind == "selection" else record["rank_sequence"]
                      if source.kind == "geometric" else documents[SEED_BASE + "/inputs.json"][record["case"]])
            row = (source, index, record, values)
            (omitted if source.name == "seeded" and record["n"] == 1500 else expected).append(row)
        require(sum(row[0].name == source.name for row in expected) == source.count, "source count")
    require(len(expected) == len(suite["entries"]) == 302
            and len(omitted) == len(suite["exclusions"]) == 8, "inventory count")
    require({r[2]["case"] for r in omitted} ==
            {f"stress-{seed}-1500-{bias}" for seed in range(11, 15) for bias in ("0.05", "0.25")},
            "excluded identities")

    seen, ids, checks, mapping = {}, set(), [], []
    by_source = {name: [] for name in SOURCE_ORDER}
    for entry, (source, index, record, values) in zip(suite["entries"], expected, strict=True):
        ranks = audit_entry(entry, source, index, record, values, False)
        require(entry["case_id"] not in ids, "global id collision")
        ids.add(entry["case_id"])
        previous = seen.get(ranks)
        owner = previous["case_id"] if previous else entry["case_id"]
        require(entry["canonical_case_id"] == owner
                and entry["duplicate_of"] == (owner if previous else None)
                and entry["membership_status"] == ("DUPLICATE" if previous else "CANONICAL"),
                "canonical precedence: " + entry["case_id"])
        if previous is None:
            seen[ranks] = entry
        by_source[source.name].append((entry, previous))
        mapping.append({k: entry[k] for k in ("case_id", "source", "source_index", "canonical_case_id",
                                            "duplicate_of", "rank_sha256", "membership_status")})
        checks.append(dict(case_id=entry["case_id"], source_index=index, input_sha256=sha(values),
                           source_values_equal=True, source_order_equal=True, source_metadata_equal=True,
                           normalized_identity_equal=True, membership="included"))
    for entry, (source, index, record, values) in zip(suite["exclusions"], omitted, strict=True):
        audit_entry(entry, source, index, record, values, True)
        require(entry["membership_status"] == "EXCLUDED" and entry["canonical_case_id"] is None
                and entry["duplicate_of"] is None, "excluded case state")
        checks.append(dict(case_id=entry["case_id"], source_index=index, input_sha256=sha(values),
                           source_values_equal=True, source_order_equal=True, source_metadata_equal=True,
                           normalized_identity_equal=True, membership="excluded"))
    per_source = {}
    for name, rows in by_source.items():
        duplicates = [(e, owner) for e, owner in rows if owner is not None]
        per_source[name] = dict(entries=len(rows), duplicate_entries=len(duplicates),
                                canonical_inputs=len(rows)-len(duplicates),
                                within_source_duplicates=sum(o["source"] == name for _, o in duplicates),
                                cross_source_duplicates=sum(o["source"] != name for _, o in duplicates),
                                excluded_entries=sum(row[0].name == name for row in omitted),
                                sizes=dict(sorted(Counter(str(e["n"]) for e, _ in rows).items(),
                                                  key=lambda x: int(x[0]))),
                                construction_families=dict(sorted(Counter(e["construction_family"]
                                                                         for e, _ in rows).items())))
    summary = dict(schema="input_suite_inventory_summary_v1", suite_sha256=suite["suite_sha256"],
                   source_order=list(SOURCE_ORDER), per_source=per_source,
                   entries=len(expected), canonical_inputs=len(seen), duplicate_entries=len(expected)-len(seen),
                   excluded_entries=len(omitted), max_n=max(len(row[3]) for row in expected),
                   qualification_performed=False, calibration_performed=False, timing_performed=False)
    require(read(output / "summary.json") == summary, "summary reconstruction")
    require(read(output / "deduplication.json") ==
            dict(suite_sha256=suite["suite_sha256"], mappings=mapping), "deduplication export")
    require(read(output / "exclusions.json") ==
            dict(suite_sha256=suite["suite_sha256"], entries=suite["exclusions"]), "exclusion export")
    states = read(output / "initial_execution_state.json")
    require(states == dict(schema="input_suite_initial_execution_state_v1", suite_sha256=suite["suite_sha256"],
                           scope="not_run_template_only",
                           cases={e["case_id"]: dict(canonical_case_id=e["canonical_case_id"],
                                                    stages={s: "NOT_RUN" for s in STAGES})
                                  for e in suite["entries"]}), "execution state must remain NOT_RUN")
    return dict(schema="input_suite_source_audit_v1", inventory_valid=True,
                scope="source_data_comparison_only", suite_sha256=suite["suite_sha256"],
                checked_included=len(expected), checked_excluded=len(omitted), per_source=per_source,
                checks=checks, qualification_performed=False, calibration_performed=False, timing_performed=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate_bundle(args.input)
    if args.report:
        with args.report.open("x") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}, ensure_ascii=False, indent=2))
