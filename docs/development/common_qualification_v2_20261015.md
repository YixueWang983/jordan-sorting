# Full common qualification v2 — 2026-10-15

The full runner explicitly calls `run_synchronous_qualification`; it never
calls the public diagnostics entry that retains fresh replay at every prefix.
The original 140 selected rows, values, order and mirror origins are reused
unchanged. Their canonical selection SHA-256 remains
`c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b`.
No new candidates, replacements, quotas or performance-based selections occur.

## Execution and evidence contract

For each input, both backends run (first backend alternating by selected index):

1. Two independently initialized CHECKED instances advance through the same
   production iterator. Every completed prefix receives full local/history
   audits and logical/physical/state comparison. An external callback also
   compares the primary prefix output with sorted input values. Expectations
   are never passed into the sorting core.
2. A third fresh CHECKED instance replays once to the final prefix. The main
   instance is freshly audited again before comparison. This is part of the
   synchronous record, not a fourth mode or another input sample.
3. A separate public minimal invocation initializes its own instance and
   compares its output externally. Tree configuration is explicitly
   `detailed_work=False` throughout.

Each input has four committed mode records: two synchronous and two minimal.
Each synchronous record reports `n-2` prefix comparisons, one final fresh replay,
three observed initializations (actual backend/config/policy), and prefix output
hashes plus state integrity hashes. Minimal records each observe one
initialization. State hashes are integrity identifiers, not independent proofs.
The controller already checks disjoint mutable instances/registries/nodes.

This changes the v1 fresh-construction schedule. It does not retain the old
claim of `n-2` fresh replays per backend. The old v1 archive remains immutable.

## Budget and failure policy

The original 180-second worker budget is shared by both backends, audits,
replay, minimal calls, process startup and persistence. The campaign budget is
1800 seconds. Each completed mode is a separately committed complete gzip.
A failure/timeout stops the campaign; every remaining selected input receives
NOT_RUN. No retry, dropped legal case, replacement or budget increase is allowed.
I/O failures propagate and may leave an incomplete archive, never a pass.

The parent checks the four mode records and coverage, not merely exit code 0.
The independent validator rechecks input legality/classification, exact frozen
selection, configuration, coverage fields, output/prefix hashes, trace sizes and
counts, statuses, summary and exact file/directory inventory. It binds all Python
source hashes to the named Git commit, which can precede a results-only commit.
It does not rerun the sorter or independently prove all hashed physical states.

## Before the full campaign

47 targeted regression methods pass, including 13 new full-v2 tests, 11
synchronous-controller tests, 6 earlier refactor evidence tests, and existing
common-qualification and pilot tests. Logs are in
`docs/validation/common_qualification_v2_20261015/tests.log`.
The new tests cover actual two-backend routing, actual process timeout during a
later mode and recovery, full failure-archive reconstruction, missing checks,
incorrect config/counts, malformed outputs and resealed semantic tampering.
Small fixture plans/mock clean-worktree metadata are explicitly test-only.
They do not qualify the 140-input set.

Freeze this source and plan before the actual campaign. Save its exact commit
in the environment, then archive results in a separate commit. No production
sorting code or tree operations change in this increment. The old pilot remains
historical to its earlier producing source.

## Gates that remain separate

Successful common qualification does not authorize formal measurement or certify
the efficient-backend minimum. Independent batch calibration, formal runner and
validator acceptance, and review of cost/representation/locality claims remain.
The existing matched measurement rules are copied unchanged into this archive.
All qualification wall-time values are resource observations, not performance.
