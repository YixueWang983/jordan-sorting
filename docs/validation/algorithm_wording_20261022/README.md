# Algorithm/proof wording and branch-coverage distinction

22 October 2026. Committed review baseline:
`46ac95db7d771b503e3eca5afe28b7661fd697d5`.
This continues the uncommitted AI-disclosure scope revision from the same day;
its files and PDF remain unchanged. Only three further thesis sources change.

## Corrections to the manuscript and to the supplied review's scope

1. **Appendix A, Lemma A.3.** Valid `join_down` descent keeps the opposite
   argument at its original blackened root. If descending the left input's
   right path, the current rank cannot fall below that fixed rank: a black
   step decreases it by one, a red step preserves it, and equal-rank black
   roots stop. A red tie descends to a black child of the same rank. The mirror
   has the same property. Thus descent does not switch sides, and recursive
   conflicts are RR or LL. LR/RL remain defensive helper branches.

   The supplied review's broader statement that **no test ever executed LR/RL
   is not correct**. The existing October 16
   `check_join_transients.py::JoinTransientChecks.test_all_four_black_root_repairs`
   constructs all four cases and directly calls the production helper.
   These are helper fixtures, not complete sorting or reachable valid-join
   histories. The revised proof states both the reachability restriction and
   the direct-test distinction. The old branch audit describes the wider helper
   contract; it is retained as a historical text rather than silently rewritten.

2. **Chapter 4 coverage table.** Near-nephew deletion repair is supported by
   operation-level evidence; complete-sort coverage is not established by this
   table. The supplied review's “only exhaustive shapes” qualification is too
   narrow: `test_deletion_shortness_cases_and_mirrored_near_rotation` already
   constructs a seed-39, 100-item insertion history and three successive splits,
   in both directions, asserting a positive near-rotation count. The separate
   exhaustive shape test also covers it. Neither is a complete Jordan input.

3. **Chapter 3 online condition.** A finite pair belongs to exactly one live
   sibling group, whose owner is its parent. This describes the logical relation
   without requiring a parent field on every tree-backed pair.

The historical operation-cost `heterogeneous_split_20261013/summary.json` has
zero at every one of its 180 occurrences of each queried counter
(`join_inner_repairs`, `deletion_near_rotations`). Those include nested/aggregate
reports, not 180 independent runs. That cost archive is not the entire test suite.

## Actual focused checks

Nine existing test methods passed, with no failures, errors or skips:

- Seven October 16 join/transient checks, including the four direct repair
  subcases, red-root transmission and its mirror.
- The existing seed-39 deletion-repair history test and its mirror.
- The existing exhaustive real-finger split test through nine leaves:
  1,088 internal shape/cut cases, with 25 near-nephew rotations. The internal
  cases/branch counts are not additional test methods or complete sort inputs.

`focused_tests.log` and `focused_checks.json` record this execution against
unchanged production code. To repeat without overwriting the historical
script's result JSON, use unittest import (not its direct script entry):

```sh
PYTHONPATH=src:tests:experiments python3 -m unittest -v \
  docs.validation.join_proof_correction_20261016.check_join_transients.JoinTransientChecks \
  test_heterogeneous_finger_split.SplitAdoptTests.test_deletion_shortness_cases_and_mirrored_near_rotation \
  test_finger_refinement.RepresentationRefinementTests.test_actual_finger_split_all_black_root_shapes_and_cuts_through_nine_leaves
```

The supplied review mentions four diagnostic scripts and `scaling.log`, but
their attachments were not available with this message. Its large-input counts
and complete-sort branch frequencies were not independently rerun or verified
here, and are not added to the thesis. Even stable measured work per point would
not by itself exclude uninstrumented work or establish an asymptotic bound.

## Build, preservation and assistance

- Clean isolated LuaLaTeX / latexmk / Biber build: **70 pages**, no final
  warnings, overfull/underfull boxes or bibliography errors.
- All 70 pages rendered against the preceding disclosure-scope PDF; physical
  pages 7, 9, 29, 38 and 59–65 change, with **59 pages pixel-identical**.
  All eleven changed pages were inspected; pages 38 and 59 were also inspected
  separately at full-page resolution. Figure/section movement is reflected in
  the contents and list of figures.
- The approved 418-word reflection and its rendered text are unchanged.
  Numeric bibliography order is unchanged. The build report binds all source inputs.
- `src/`, `experiments/`, `tests/`, `data/` and `results/` remain unchanged.
  No full regression suite, input qualification, calibration, formal timing or
  large-scale stress campaign was repeated. Earlier archives and PDFs remain intact.
- Codex checked the user-supplied review against the source and existing tests,
  proposed the qualified wording, ran the nine checks, and built/reviewed the PDF.
  This is not independent mathematical certification or completed AI disclosure.

Output: `output/pdf/jordan_thesis_supervisor_review_20261022_algorithm_review.pdf`.
