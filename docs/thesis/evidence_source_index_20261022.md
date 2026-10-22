# Evidence and source index accompanying Appendix B

22 October 2026. This expands the compact index in the thesis after the author
approved inclusion of the personal AI-use reflection. It preserves the previous
appendix's source and archive bindings. Execution commits identify the producers,
not the later commits that saved their results.

## Current evidence

| Role | Producer | Directory under `docs/validation/` |
| --- | --- | --- |
| 140-input qualification | `3cafb44` | `common_qualification_v2_20261015/` |
| 12-input qualification | `668371f` | `split_trace_followup_20261015/` |
| ID recheck and calibration | `c5b5ac3` | `id_lifecycle_calibration_20261015/` |
| Formal 140 + 12 | `4a83fa6` | `final_review_formal_20261015/` |

The formal archive contains 5,600 common and 480 targeted sample batches.
Its Python code matches calibration source `c5b5ac3`; result storage at
`ce0148b` does not change execution identity. UTC timestamps identify runs;
dated directories identify work packages. Inputs, B tables and data stay frozen.
Full hashes and manifests remain in those archives.

## Proof-to-source correspondence

Appendix A develops the argument in English.

| Source | Correspondence |
| --- | --- |
| `src/heterogeneous_finger_backend.py`: node/header classes, `_repair_insert`, `_rotate_outward` | Representation map D and insertion lemma |
| Same file: `split_value`, `adopt_split` | Public header transition |
| `src/heterogeneous_finger_split.py`: conversion, `balance_down`, `join_down`, `repair_short`, `split_down` | Join, split, telescoping, finger and mixed-operation lemmas |
| `src/paper_jordan.py`: Step 1/2/3 core | Locality lemma and total-cost theorem |

The branch audit is `docs/development/finger_final_review_20261015.md`.
Red-root and split-potential corrections are recorded under
`docs/validation/join_proof_correction_20261016/`; older review receipts do not
certify the subsequently revised appendix.

## Development and historical evidence

The operation tests and 18-input structural campaign in the correctness-coverage
table are respectively archived under
`docs/validation/heterogeneous_split_20261013/` and
`docs/validation/heterogeneous_work_modes_20261013/`.
Their recorded source hashes match `cc1aa2d` and `84f7e13`, not the parent HEADs
recorded with uncommitted changes. The inventory under
`docs/validation/review_delivery_20261016/` checks saved reports, without
reconstructing unsaved traces or rerunning inputs.

Historical formal/pilot producers are `98868b1`/`01f6480`.
`docs/thesis/claim_to_evidence_table.md` retains their method, results and archive
locators. Old timings are not pooled with current results.

## Supplement and manuscript revisions

The local diagnostic, seeded inputs and external-material provenance are indexed
in `docs/validation/thesis_review_round2_20261020/README.md`. Original records
remain unchanged. That directory also records the October 20 manuscript checks.

Subsequent manuscript-only records are under
`docs/validation/numeric_citations_20261022/`,
`docs/validation/ai_wording_20261022/`,
`docs/validation/ai_alignment_20261022/`, and
`docs/validation/ai_reflection_integration_20261022/`.
Each binds its own PDF to its own source snapshot. An earlier build report is
not a hash certificate for a later manuscript.

AI-use details and the approved reflection are in
`docs/development/AI_USE_RECORD_20261022_integrated.md`.
The full reflection is now part of Appendix B; the Chinese review translation
stays in the accompanying record. The author's request to incorporate the text
does not complete separate personal-information or declaration requirements.
