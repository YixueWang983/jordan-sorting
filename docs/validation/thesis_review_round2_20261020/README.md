# Second review corrections — 20 October 2026

Baseline: `2da8b662bf3c50c1bd51ee85ed2215a72a34f7c7`.
This revision changes the manuscript and adds read-only review records.
It neither changes the measured implementation nor repeats any campaign.

## Changes and checks

| Review item | Resolution | Evidence |
| --- | --- | --- |
| A: selected diagnostic rows | Table 6.5 now gives all fifteen individual cases, including both heavy directions, with T/L, H/L, U/L and reduction. Results, abstract and conclusion say four hook-free wins and eleven ratios of 1.09–1.68. | `local_supplement_recheck.json`, reconstructed from every saved batch/output |
| B: dummy re-entry premise | A.5 includes bracketing of all other finite region endpoints; A.6 explains the empty outer group and free slot. | Printed page 88 of Fung et al. (1990), locality lemma (b), inspected directly; current `backend_argument.tex` |
| C: generator and provenance | Section 4.4.1 explains gap legality, rank values, seeds, bias and RNG scheduling. B.4 becomes a one-sentence locator. | Forty saved inputs regenerated exactly, without sorting; `supplement_provenance.md` |
| C: AI disclosure | FU's Computer Science-specific guidance checked; Appendix B.5 describes author-directed, AI-assisted work by activity. | `AI_USE_RECORD.md`; complete tool inventory, personal reflection and any supervisor-specific requirements remain for the author |
| Minor wording/layout | Conclusion now invites independent review; Figure A.1 caption identifies omitted finger arrows; historical section starts on the next page. | Final PDF and visual review |

No claim is made that Codex completed most of the work. Contribution percentages
are not inferred from conversations. The review-draft disclosure is not a
completed or signed university declaration.

## Actual executions in this round

- **805 unittest methods passed**, no failures or skips reported (`unittest.log`).
- Both formal archive validators returned `archive_valid=true`, `complete=true`,
  `stage=formal`: 140 common inputs and 12 targeted inputs. This reads saved
  qualifications, calibrations, outputs and measurements; it is not retiming.
- The local supplement checker reconstructs all 900 diagnostic batches,
  11,700 timed outputs, 180 warm-up outputs, and saved records for the forty
  correctness cases. It emits all fifteen individual table rows and the
  four/eleven split, rather than aggregating selected cases.
- Forty generator inputs exactly match their saved values under the recorded
  seeds and sequential RNG schedule. This is input regeneration, not forty
  new sorting or qualification runs.
- Eight subprocess entry checks reject optimized Python for the two new
  read-only checkers, before archive reads or report output.
- Tracked files under `src/`, `experiments/`, `tests/`, `data/`, `results/`,
  and the prior sealed supplementary directory match the baseline Git blobs.
  The prior PDF and ZIP and all 1,346 old manifest entries remain unchanged.

## Reproduce the checks

Run from the repository root with unoptimized Python and the project dependencies.
Reports below were saved using CPython 3.12.14 on the local machine.
The commands print reports; use new output paths if redirecting stdout.

```sh
PYTHONPATH=src:experiments python3 -m unittest discover -s tests -v
python3 docs/validation/thesis_review_round2_20261020/check_local_supplement.py
python3 docs/validation/thesis_review_round2_20261020/check_round2.py

PYTHONPATH=src:experiments python3 experiments/validate_matched_measurement.py \
  docs/validation/final_review_formal_20261015/formal_common \
  --qualification docs/validation/common_qualification_v2_20261015/qualification \
  --calibration docs/validation/id_lifecycle_calibration_20261015/calibration_common

PYTHONPATH=src:experiments python3 experiments/validate_matched_measurement.py \
  docs/validation/final_review_formal_20261015/formal_targeted_split \
  --qualification docs/validation/split_trace_followup_20261015/qualification \
  --calibration docs/validation/id_lifecycle_calibration_20261015/calibration_targeted_split
```

`check_round2.py` checks the new stored validator reports and unittest log as
well as frozen files and text. It does not itself rerun those tests/validators.
The previous `thesis_revision_20261020/check_local_supplement.py` is preserved:
its old table assertion belongs to the thesis at `2da8b662`, not the new table.
Use the new checker for this revision. Do not rewrite the old manifest.

## Build and delivery

The fresh build uses LuaLaTeX, Biber, Libertinus and DejaVu Sans Mono:

```sh
cd thesis
latexmk -lualatex main.tex
```

`build_report.json` binds the PDF to its inputs and records page/warning counts;
`visual_review.json` records actual rendered-page checks. Font, line spacing,
margins and right-page chapter starts are unchanged.

The new PDF is `output/pdf/jordan_thesis_supervisor_review_20261020_r2.pdf`;
the new package is `output/packages/jordan_supervisor_review_20261020_r2.zip`.
Their earlier counterparts remain intact. The package includes the manuscript,
proofs, current review records and the original local supplement. It does not
duplicate all earlier raw formal data: retrieve that data from the fixed
baseline repository. Its root manifest checks every other package member.

The formal producer remains `4a83fa6b7a4213e9e5758fe3454e002ebc266459`.
The local supplementary producer remains
`19a553fb9a089fae726c4ba49c5412a9e4bd12d3`.
This round adds no mathematical certification or newly qualified backend.
