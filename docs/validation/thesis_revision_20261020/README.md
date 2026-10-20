# Thesis restructuring and supplied review material — 20 October 2026

Baseline: `19a553fb9a089fae726c4ba49c5412a9e4bd12d3`.
This is a thesis revision with a separate bounded exploratory supplement,
not a new implementation, qualification or formal campaign.
The current formal execution remains `4a83fa6b7a4213e9e5758fe3454e002ebc266459`.

## Changes

- Appendix A now develops the English representation, recursive join/deletion
  transient, exact grouping/locality and mixed-operation cost argument. It
  includes the previously reviewed R3 correction and nonempty split condition.
  This is the project's manual source-level argument, not independent proof certification.
- `family` is distinguished from the whole upper/lower parity forest; the
  parent/direct-child latest-member grouping invariant is explicit.
- Three new original TikZ diagrams show the physical ribs, split/adopt sequence
  and current qualification → calibration → formal evidence flow.
- The measured tree configuration explicitly retains `_Tracked` field access
  hooks and operation/phase wrappers with detailed collection disabled.
- The common-set nesting table explicitly records zero two-sided splits in
  every stratum. Numeric formal results and existing result figures are unchanged.
- Repeated proof summaries, historical timing method detail and historical
  metadata lists were replaced by the developed argument and a compact source
  index. Historical archives themselves remain unchanged.
- After receiving all four scripts/logs, the proposed local diagnostic was
  completed on the original M4 and CPython 3.12.14; a small fixed-seed correctness
  supplement was also recorded. These have their own pre-execution protocol.

## Four external files supplied during this revision

`external_review/` preserves the supplied files byte-for-byte. The script
`check_external_material.py` parses their syntax and summaries, checks basic
case/seed consistency and recomputes ratios/counts. It does **not** execute
those scripts, generate inputs, run sorting, certify source/environment or
reconstruct missing raw measurements. Run without Python optimization:

```sh
python docs/validation/thesis_revision_20261020/check_external_material.py
```

`external_material_check.json` contains the results and exact incoming hashes.
The stress log reports 1,600 large inputs and 32,404 two-sided splits, plus
300 checked inputs and 272 two-sided splits, with zero reported failures.
The logged seeds are 11–14 and 21–22. The length ranges in the accompanying
review are not bound by command lines in these files. There are no per-input
hashes or traces with which to reconstruct the aggregate counts independently.

The wrapper log contains four successful 15-case summary dictionaries and a
failed earlier `tree_nowr` attempt (`_side` descriptor binding TypeError). The
supplied final script excludes static/class/property descriptors when unwrapping;
the earlier failing script version is not supplied. This log is not a pristine,
manifest-bound one-shot campaign. Removing field access hooks yields reported
tree/list ratios approximately 0.649–0.807 on the four heavy 512/513 cases;
that is useful diagnostic evidence but not a frozen formal-protocol estimate.

Two further script limits matter:

1. The wrapper script's docstring says every output is checked, but the timed
   inner loop keeps only `r`: only the last output in each timed batch is
   compared. All three warmups are compared. No per-batch timing vector is saved.
2. Both scripts use `assert` without an optimization guard. Interpreter flags
   were not included in the supplied logs. We do not modify these external
   originals or retroactively assert that those checks executed.

The thesis acknowledges these external aggregates as reviewer-reported.
They are excluded from verified coverage and formal performance estimates;
generator frequency is not a population estimate. The new local runs below
have separate inputs, execution records and scope.

## Local exploratory runs

`run_supplement.py` adapts the supplied approaches without changing production
files. `local_supplement/protocol.json` and `inputs.json` were written before
any diagnostic sorting/timing, with source, script, input and environment hashes.
The source files match `19a553fb` (and the formal source); the working tree
was dirty only because this thesis revision was being prepared. Runtime removal
of hooks/decorators occurs only inside the named isolated subprocess.

- Diagnostic: the same fifteen named cases as the supplied log, four variants,
  three warmups and fifteen batches per case/variant. Batch sizes are 25 calls
  at 128 and 7 at 512/513, not the formal B table. Every output is retained
  and checked after timing. All 900 batches, 11,700 timed outputs and 180 warmup
  outputs passed. The timer also includes output append; GC remains enabled,
  with collection before each batch. Case order is fixed and variant order
  rotates by case; batches of different variants are not interleaved.
- Source-level hooks removed: `_Tracked.__getattribute__` and `__setattr__`.
  The fourth variant additionally unwraps the operation/phase decorators,
  excluding static/class/property descriptors. Per-process identities record
  every modified method. This is not a qualified production backend.
- Removing field hooks reduces per-input tree medians by 37.7–52.1%.
  The four heavy 512/513 cases favor the hook-free variant; grouped ratios are
  0.691 and 0.688. This is an exploratory configuration effect, not an exact
  additive fraction of data-structure cost or a replacement formal result.
- Correctness: 32 predetermined cases from seeds 11–14, sizes 128/512/513/1500
  and biases .05/.25, plus eight cases from seeds 21–22, sizes 32/33/64/70,
  bias .1. The supplied generator function is reused with fixed sequential
  RNG streams. All inputs are saved and oracle-checked; each case checks list
  minimal, tree minimal and tree trace output. The eight small cases additionally
  run tree checked with the public fresh-prefix replay checker.
- All forty distinct input hashes passed, with 678 two-sided splits in 38
  inputs and maximum smaller side 13. Complete original tree trace is saved;
  replay work is not added to split counts. This bounded run does not reproduce
  the reviewer's 1,900 cases or prove broad randomized coverage.

All 100 workers completed within the 900-second campaign budget (180 seconds
per worker), in about 113 seconds. Complete gzip records are committed before
continuing; exceptions/timeouts stop the campaign and retain earlier files.
The independent read-only `check_local_supplement.py` reconstructs all outputs,
batch medians, counts, event ordering and the four thesis table rows. It does
not invoke a sorter or independently decode large-case physical trees.

```sh
# Inspect the already saved local records:
python docs/validation/thesis_revision_20261020/check_local_supplement.py
# Reproduce in a NEW output directory; do not overwrite the saved campaign:
python docs/validation/thesis_revision_20261020/run_supplement.py freeze /tmp/jordan-supplement-new
python docs/validation/thesis_revision_20261020/run_supplement.py run /tmp/jordan-supplement-new
python docs/validation/thesis_revision_20261020/run_supplement.py check /tmp/jordan-supplement-new
```

The original formal protocol, 140/12 qualification, calibration and samples were
not rerun. No complete unittest suite was rerun during this thesis revision.

## Proof correspondence and verification scope

English appendix → existing corrected review sections:

- Definition D and insertion/conversion lemma: R1–R2.
- Recursive join contract: R3, including red-root passthrough and black-parent repair.
- Detachment/split/adoption: R4–R6, including role spans and header/leaf lifetimes.
- Re-entry and prefix induction: L1–L4; original Fung locality lemma on printed
  p. 88 is restricted to the child case. The finite-parent extension remains
  explicitly the project's argument. Printed pp. 87–88 were visually reread.
- Cumulative join: C1–C2, normalized-height baseline and strong induction.
- Finger/rib and mixed potential: C3–C5; no reset after split.
- Total theorem: section 7, unit-cost/expected-amortized dictionary model.

The prose transfer and source correspondence were checked locally; this is not
new external mathematical certification. Production Python and all earlier
archives remain frozen. This revision requires no rerun of qualification,
calibration or formal samples. See the build and revision checks in this
directory for the actual local work performed.

## Build and delivery

Build the supplied `thesis/` with `latexmk -lualatex main.tex`, LuaLaTeX, Biber,
Libertinus and DejaVu Sans Mono. Figure PDFs are included; their original TikZ
sources are under `thesis/figures/source/` and can be rebuilt with LuaLaTeX,
`standalone`, `pgf` and `preview`. No margin, body font size, line spacing or
right-page chapter setting was reduced. This remains a supervisor review draft;
personal registration information and the signed declaration are not final.

## Final checks and package

- Fresh isolated build: 70 physical pages, zero final warnings/overfull/underfull
  boxes; eight blank duplex pages. Font, margins and line spacing are unchanged.
- All pages inspected visually; after the local supplement, fifteen changed
  pages were checked again and the remaining pages compared pixel-for-pixel.
- Nineteen formal numeric table rows and four diagnostic rows checked against
  their separate archived summaries/records. Sixteen actual optimization-mode
  rejection subprocesses passed for four new evidence scripts.
- The four supplied originals match their incoming files byte-for-byte.
- `SHA256SUMS.json` covers this new validation folder, excluding itself.
- The new PDF and `output/packages/jordan_supervisor_review_20261020.zip`
  have separate hashes. The ZIP contains paper sources, proofs, this new
  record set and a reading guide. It does not duplicate all older raw formal
  archives; fixed repository revisions supply those. Previous deliverables
  and frozen formal data are retained without modification.

These checks do not constitute external certification of the mathematical
argument, full-suite execution, or completion of university submission details.
