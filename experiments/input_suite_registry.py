"""Read the preregistered input suite; never import or execute sorting code.

This module only reads fixed files, normalizes ranks for identity, and publishes
an inventory. It does not generate inputs or grant qualification/timing status.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "jordan_input_suite_v1"
REGISTRATION_PATH = "docs/plan/uninstrumented_rerun_addendum_20261101.md"
REGISTRATION_COMMIT = "afbbff68525b112ad9bc03c163b435ca74590212"
GEO_PATH = "docs/development/geometric_generator_probe_20261101.json"
SEED_BASE = "docs/validation/thesis_revision_20261020/local_supplement"
STAGES = ("equivalence", "qualification", "calibration", "formal", "independent_validation")
FILE_SHA256 = {
    REGISTRATION_PATH: "e5283514add2f650a0e84efd3ae901584a94b2daa5dfb275d3f40b5aa6dcd9ee",
    "docs/validation/common_qualification_20261015/qualification/selected.json":
        "d0be513508990a8dbaed184e4538876782251ccfa335c5bfc1fc6f3edf6fcaeb",
    "docs/validation/split_trace_followup_20261015/qualification/selected.json":
        "d91c819c82f03208b841a2cbf9cc3777da76b5ec72968578482c1a63f43030f6",
    "docs/validation/structural_split_formal_20261101/preselected_inputs.json":
        "6da5ae135453056f34ba4dab605cad14f2a6b006a32ecca2aa7f1d1706c5a5dc",
    GEO_PATH: "59e86ceb97c38ea95620bed290edc45842c9f569a5566a2559bfe2108ae2fd25",
    "experiments/probe_geometric_inputs.py":
        "47647d2a7bf0185cd85316a89d6efd717de2c326a8b09db53b72e9bc9588a5cb",
    SEED_BASE + "/protocol.json":
        "60d9ba5429a33b01ef5b5747965e2564df5f78c8debeea2c4ac8407844f9fc9a",
    SEED_BASE + "/inputs.json":
        "25f215b3ee3de92ab1b5d5c1a209065052003ff08fa8709e99457915a233a032",
}
COMMON_FAMILIES = {
    "strict_flat": "increasing_flat",
    "low_nesting_valid": "low_nesting_block",
    "medium_nesting_valid": "medium_nesting_block",
    "nested_heavy_valid": "nested_suffix",
}


@dataclass(frozen=True)
class SourceSpec:
    name: str
    path: str
    count: int
    kind: str
    selection_sha256: str | None = None


SOURCES = (
    SourceSpec("common", "docs/validation/common_qualification_20261015/qualification/selected.json",
               140, "selection", "c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b"),
    SourceSpec("targeted_split", "docs/validation/split_trace_followup_20261015/qualification/selected.json",
               12, "selection", "357220a65f52059df647be4189531e981bbef0e2aa13fd744d19ce40819c0454"),
    SourceSpec("structural", "docs/validation/structural_split_formal_20261101/preselected_inputs.json",
               18, "selection", "e91e7a3ecfdc1506b621d7e7b286b3830f0bf48a993b279eb3f15902a914cf3b"),
    SourceSpec("geometric", GEO_PATH, 100, "geometric"),
    SourceSpec("seeded", SEED_BASE + "/protocol.json", 32, "seeded"),
)
SOURCE_ORDER = tuple(s.name for s in SOURCES)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rank_normalize(values):
    require(type(values) is list and bool(values), "input must be a nonempty list")
    require(all(type(x) is int for x in values), "input values must be integers, not booleans")
    require(len(set(values)) == len(values), "input values must be distinct")
    ranks = {x: i + 1 for i, x in enumerate(sorted(values))}
    return [ranks[x] for x in values]


def load_documents(root=ROOT):
    documents = {}
    for relative, expected in FILE_SHA256.items():
        raw = (Path(root) / relative).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, "fixed source changed: " + relative)
        if relative.endswith(".json"):
            documents[relative] = json.loads(raw)
    return documents


def _pointer_key(key):
    return key.replace("~", "~0").replace("/", "~1")


def _entry(source, index, original_id, values, metadata, record, pointer, values_file, values_pointer):
    ranks = rank_normalize(values)
    return dict(
        case_id=source.name + "--" + original_id, source=source.name,
        original_case_id=original_id, source_index=index,
        legacy_dataset="structural_split" if source.name == "structural" else source.name,
        values=list(values), n=len(values), input_sha256=digest(values),
        rank_sequence=ranks, rank_sha256=digest(ranks),
        construction_family=None, shape=None, smaller_side_k=None,
        seed=None, bias=None, mirror=None, base_id=None, category=None,
        source_metadata=metadata,
        provenance=dict(source_file=source.path, source_file_sha256=FILE_SHA256[source.path],
                        record_pointer=pointer, record_sha256=digest(record),
                        values_file=values_file, values_file_sha256=FILE_SHA256[values_file],
                        values_pointer=values_pointer),
    )


def load_source(source, documents):
    """Return included and explicitly excluded memberships in original order."""
    included, excluded = [], []
    data = documents[source.path]
    if source.kind == "selection":
        require(data["deficits"] == [] and data["selection_sha256"] == source.selection_sha256
                and digest(data["cases"]) == source.selection_sha256, "selection identity changed")
        for index, case in enumerate(data["cases"]):
            spec = case["spec"]
            pointer = f"/cases/{index}"
            metadata = {k: v for k, v in case.items() if k != "values"}
            e = _entry(source, index, spec["case"], case["values"], metadata, case,
                       pointer, source.path, pointer + "/values")
            require(e["n"] == spec["n"] and e["input_sha256"] == case["input_sha256"]
                    and e["rank_sha256"] == case["rank_sha256"], "archived input identity mismatch")
            e.update(seed=spec.get("seed"), mirror=spec.get("mirror"),
                     base_id=spec.get("base_id"), category=spec["requested_category"])
            require(e["category"] == case["profile"]["category"], "archived category mismatch")
            if source.name == "common":
                e["construction_family"] = COMMON_FAMILIES[e["category"]]
            elif source.name == "targeted_split":
                e.update(construction_family="values_for", shape="targeted", smaller_side_k=spec["k"])
            else:
                shape = spec["shape"]
                require(shape in ("balanced", "skew", "repeated"), "unknown structural shape")
                k = ((e["n"] - e["n"] % 2 - 6) // 2) // 2 if shape == "balanced" else 1
                e.update(construction_family="repeated" if shape == "repeated" else "values_for",
                         shape=shape, smaller_side_k=None if shape == "repeated" else k)
            included.append(e)
    elif source.kind == "geometric":
        require(data["timing_collected"] is False and len(data["cases"]) == 100, "probe inventory changed")
        fields = ("case", "target_n", "index", "seed", "rank_sequence_sha256", "intersection_count", "status")
        for index, case in enumerate(data["cases"]):
            pointer = f"/cases/{index}"
            e = _entry(source, index, case["case"], case["rank_sequence"],
                       {k: case[k] for k in fields}, case, pointer, source.path, pointer + "/rank_sequence")
            require(e["n"] == case["target_n"] == case["intersection_count"]
                    and e["rank_sha256"] == case["rank_sequence_sha256"], "geometric input identity mismatch")
            e.update(construction_family="grid_tree_corridor_polygon", seed=case["seed"])
            included.append(e)
    elif source.kind == "seeded":
        values_file = SEED_BASE + "/inputs.json"
        require(data["inputs_sha256"] == FILE_SHA256[values_file] and len(data["stress"]) == 40,
                "seeded inventory changed")
        for index, spec in enumerate(data["stress"]):
            e = _entry(source, index, spec["case"], documents[values_file][spec["case"]],
                       dict(spec), spec, f"/stress/{index}", values_file, "/" + _pointer_key(spec["case"]))
            require(e["n"] == spec["n"], "seeded size mismatch")
            e.update(construction_family="seeded_legal_gap", seed=spec["seed"], bias=spec["bias"])
            if e["n"] == 1500:
                e.update(membership_status="EXCLUDED", canonical_case_id=None, duplicate_of=None,
                         exclusion_reason="addendum_section_1_n1500",
                         exclusion_reference=REGISTRATION_PATH + "#1")
                excluded.append(e)
            else:
                included.append(e)
        expected = {f"stress-{seed}-1500-{bias}" for seed in range(11, 15) for bias in ("0.05", "0.25")}
        require({e["original_case_id"] for e in excluded} == expected and len(excluded) == 8,
                "n=1500 exclusion list changed")
    else:
        raise ValueError("unknown source kind")
    require(len(included) == source.count, "source membership count changed: " + source.name)
    return included, excluded


def assign_canonical(entries):
    """First normalized sequence wins; a hash match must also match every rank."""
    seen, ids = {}, set()
    for entry in entries:
        require(entry["case_id"] not in ids, "duplicate global case id")
        ids.add(entry["case_id"])
        ranks = rank_normalize(entry["values"])
        require(ranks == entry["rank_sequence"] and digest(ranks) == entry["rank_sha256"],
                "invalid normalized input identity")
        previous = seen.get(entry["rank_sha256"])
        if previous is None:
            seen[entry["rank_sha256"]] = entry
            entry.update(membership_status="CANONICAL", canonical_case_id=entry["case_id"], duplicate_of=None)
        else:
            require(previous["rank_sequence"] == ranks, "rank digest collision")
            entry.update(membership_status="DUPLICATE", canonical_case_id=previous["case_id"],
                         duplicate_of=previous["case_id"])
    return entries


def load_suite(root=ROOT):
    documents = load_documents(root)
    entries, exclusions = [], []
    for source in SOURCES:
        added, omitted = load_source(source, documents)
        entries.extend(added)
        exclusions.extend(omitted)
    assign_canonical(entries)
    require(len(entries) == 302 and len(exclusions) == 8, "suite inventory changed")
    payload = dict(schema=SCHEMA, scope="input_inventory_only",
                   registration=dict(path=REGISTRATION_PATH, commit=REGISTRATION_COMMIT,
                                     sha256=FILE_SHA256[REGISTRATION_PATH]),
                   source_order=list(SOURCE_ORDER), source_files=dict(FILE_SHA256),
                   legacy_selections={s.name: s.selection_sha256 for s in SOURCES if s.selection_sha256},
                   deduplication_rule="first source/index, normalized full rank sequence; no mirror equivalence",
                   entries=entries, exclusions=exclusions)
    return {**payload, "suite_sha256": digest(payload)}


def canonical_cases(suite, source=None):
    """Read the canonical representatives without altering their archived values."""
    if source is not None:
        require(source in SOURCE_ORDER, "unknown source")
    return [e for e in suite["entries"] if e["membership_status"] == "CANONICAL"
            and (source is None or e["source"] == source)]


def summarize(suite):
    counts = {}
    by_id = {e["case_id"]: e for e in suite["entries"]}
    for source in SOURCE_ORDER:
        rows = [e for e in suite["entries"] if e["source"] == source]
        duplicates = [e for e in rows if e["duplicate_of"] is not None]
        counts[source] = dict(
            entries=len(rows), duplicate_entries=len(duplicates), canonical_inputs=len(rows)-len(duplicates),
            within_source_duplicates=sum(by_id[e["duplicate_of"]]["source"] == source for e in duplicates),
            cross_source_duplicates=sum(by_id[e["duplicate_of"]]["source"] != source for e in duplicates),
            excluded_entries=sum(e["source"] == source for e in suite["exclusions"]),
            sizes=dict(sorted(Counter(str(e["n"]) for e in rows).items(), key=lambda x: int(x[0]))),
            construction_families=dict(sorted(Counter(e["construction_family"] for e in rows).items())),
        )
    return dict(schema="input_suite_inventory_summary_v1", suite_sha256=suite["suite_sha256"],
                source_order=list(SOURCE_ORDER), per_source=counts,
                entries=len(suite["entries"]), canonical_inputs=len(canonical_cases(suite)),
                duplicate_entries=sum(e["duplicate_of"] is not None for e in suite["entries"]),
                excluded_entries=len(suite["exclusions"]), max_n=max(e["n"] for e in suite["entries"]),
                qualification_performed=False, calibration_performed=False, timing_performed=False)


def artifacts(suite):
    mapping = [{k: e[k] for k in ("case_id", "source", "source_index", "canonical_case_id",
                                  "duplicate_of", "rank_sha256", "membership_status")} for e in suite["entries"]]
    initial = dict(schema="input_suite_initial_execution_state_v1", suite_sha256=suite["suite_sha256"],
                   scope="not_run_template_only",
                   cases={e["case_id"]: dict(canonical_case_id=e["canonical_case_id"],
                                             stages={stage: "NOT_RUN" for stage in STAGES})
                          for e in suite["entries"]})
    return {"suite.json": suite, "summary.json": summarize(suite),
            "deduplication.json": dict(suite_sha256=suite["suite_sha256"], mappings=mapping),
            "exclusions.json": dict(suite_sha256=suite["suite_sha256"], entries=suite["exclusions"]),
            "initial_execution_state.json": initial}


def write_bundle(output, root=ROOT):
    # Build and validate inputs before creating any output; never overwrite an archive.
    suite = load_suite(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in artifacts(suite).items():
        (output / name).write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding='utf-8', newline='\n')
    return suite


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(write_bundle(args.output)), ensure_ascii=False, indent=2))
